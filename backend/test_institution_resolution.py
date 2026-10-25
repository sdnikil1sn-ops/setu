
from institution_resolution import (
    get_connection,
    resolve_by_permanent_id,
)

def main():
    # Read one existing Permanent ID from Supabase.
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT permanent_id
                FROM public.institutions
                WHERE permanent_id IS NOT NULL
                  AND BTRIM(permanent_id) <> %s
                LIMIT 1
                """,
                ("",),
            )
            row = cur.fetchone()

    if row is None:
        print("No non-empty Permanent ID found.")
    else:
        result = resolve_by_permanent_id(row["permanent_id"])

        print("Test Permanent ID:", row["permanent_id"])
        print("Resolution status:", result["resolution_status"])
        print("Resolution method:", result["resolution_method"])
        print("Confidence:", result["resolution_confidence"])
        print("Reason:", result["reason"])

        if result["institution"]:
            print("Matched institution:", result["institution"]["name"])


if __name__ == "__main__":
    main()
