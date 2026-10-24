
import json
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg import sql
from psycopg.types.json import Jsonb


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "db.json"

# Parent/reference tables must be imported before dependent tables.
IMPORT_ORDER = [
    "regions",
    "institution_groups",
    "bureaus",
    "institutions",
    "institution_aliases",
    "profiles",
    "complaint_cases",
    "case_actions",
    "case_links",
    "coordination_notes",
    "alerts",
    "sla_rules",
    "audit_logs",
    "ground_truth_pairs",
    "ground_truth_clusters",
    "institution_resolution_ground_truth",
]

JSONB_COLUMNS = {
    "case_links": {"reasons"},
    "audit_logs": {"details"},
    "ground_truth_clusters": {"case_ids", "institution_ids"},
}


def load_dataset():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {DATA_FILE}"
        )

    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("The JSON root must be an object.")

    missing = [
        name for name in IMPORT_ORDER
        if name not in data
    ]

    if missing:
        raise ValueError(
            f"Missing dataset collections: {missing}"
        )

    for name in IMPORT_ORDER:
        if not isinstance(data[name], list):
            raise ValueError(
                f"Collection '{name}' must be a list."
            )

        for index, record in enumerate(data[name]):
            if not isinstance(record, dict):
                raise ValueError(
                    f"{name}[{index}] must be an object."
                )

    if not isinstance(data.get("manifest"), dict):
        raise ValueError("Dataset manifest is missing.")

    print("Dataset validation passed.")
    print(f"Source: {DATA_FILE}")
    print("\nRecords to import:")

    for name in IMPORT_ORDER:
        print(f"  {name}: {len(data[name])}")

    return data


def insert_records(cur, table_name, records):
    if not records:
        print(f"  {table_name}: 0 records")
        return

    # All records in a collection should have the same fields.
    columns = list(records[0].keys())

    for index, record in enumerate(records):
        if set(record.keys()) != set(columns):
            raise ValueError(
                f"Inconsistent fields in {table_name}, "
                f"record index {index}."
            )

    query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier("public", table_name),
        sql.SQL(", ").join(
            sql.Identifier(column) for column in columns
        ),
        sql.SQL(", ").join(
            sql.Placeholder() for _ in columns
        ),
    )

    jsonb_columns = JSONB_COLUMNS.get(table_name, set())

    values = []
    for record in records:
        row_values = []

        for column in columns:
            value = record[column]

            if column in jsonb_columns and value is not None:
                value = Jsonb(value)

            row_values.append(value)

        values.append(tuple(row_values))

    cur.executemany(query, values)
    print(f"  {table_name}: inserted {len(records)}")


def main():
    load_dotenv(BASE_DIR / ".env")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is missing from backend/.env"
        )

    data = load_dataset()

    print("\nConnecting to Supabase...")

    # The connection context commits on success and rolls
    # back the transaction if any operation raises an error.
    with psycopg.connect(
        database_url,
        connect_timeout=15,
    ) as conn:
        with conn.cursor() as cur:
            # Refuse to mix this import with existing data.
            for table_name in IMPORT_ORDER:
                cur.execute(
                    sql.SQL("SELECT count(*) FROM {}").format(
                        sql.Identifier("public", table_name)
                    )
                )

                count = cur.fetchone()[0]

                if count != 0:
                    raise RuntimeError(
                        f"Table '{table_name}' already contains "
                        f"{count} rows. Import cancelled to avoid "
                        "duplicating or mixing data."
                    )

            print("Target tables are empty.")
            print("\nImporting records...")

            for table_name in IMPORT_ORDER:
                insert_records(
                    cur,
                    table_name,
                    data[table_name],
                )

            # Save the dataset manifest in its own table.
            manifest = data["manifest"]
            dataset_id = manifest.get("dataset_id")

            if not dataset_id:
                raise ValueError(
                    "Manifest has no dataset_id."
                )

            cur.execute(
                """
                INSERT INTO public.setu_dataset_manifest
                    (dataset_id, manifest)
                VALUES (%s, %s)
                """,
                (dataset_id, Jsonb(manifest)),
            )

            print("  setu_dataset_manifest: inserted 1")

            # Verify counts inside the same transaction.
            print("\nVerifying imported row counts:")

            for table_name in IMPORT_ORDER:
                cur.execute(
                    sql.SQL("SELECT count(*) FROM {}").format(
                        sql.Identifier("public", table_name)
                    )
                )
                actual = cur.fetchone()[0]
                expected = len(data[table_name])

                print(
                    f"  {table_name}: "
                    f"{actual}/{expected}"
                )

                if actual != expected:
                    raise RuntimeError(
                        f"Count mismatch for {table_name}: "
                        f"expected {expected}, got {actual}"
                    )

            cur.execute(
                """
                SELECT count(*)
                FROM public.setu_dataset_manifest
                WHERE dataset_id = %s
                """,
                (dataset_id,),
            )

            if cur.fetchone()[0] != 1:
                raise RuntimeError(
                    "Manifest verification failed."
                )

    print("\nSUCCESS: import committed.")
    print("All collection counts match the source JSON.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\nIMPORT FAILED: {error}", file=sys.stderr)
        print(
            "The transaction was rolled back if it had started.",
            file=sys.stderr,
        )
        sys.exit(1)
