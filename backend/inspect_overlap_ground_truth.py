
from institution_resolution import get_connection


def main():
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Inspect the existing table structure.
            cur.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'ground_truth_pairs'
                ORDER BY ordinal_position
                """
            )
            columns = cur.fetchall()

            print("=== ground_truth_pairs columns ===")
            for column in columns:
                print(
                    column["column_name"],
                    "|",
                    column["data_type"],
                )

            # Inspect a small sample to understand its labels.
            cur.execute(
                """
                SELECT *
                FROM public.ground_truth_pairs
                LIMIT 5
                """
            )
            rows = cur.fetchall()

            print("\n=== Sample ground-truth records ===")
            for row in rows:
                print(dict(row))

            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM public.ground_truth_pairs
                """
            )
            print("\nTotal ground-truth records:", cur.fetchone()["total"])


if __name__ == "__main__":
    main()
