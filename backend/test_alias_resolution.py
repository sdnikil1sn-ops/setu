
from institution_resolution import get_connection, resolve_by_alias

def main():
    # Fetch one real alias from the existing synthetic dataset.
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT alias
                FROM public.institution_aliases
                WHERE alias IS NOT NULL
                  AND BTRIM(alias) <> %s
                LIMIT 1
                """,
                ("",),
            )
            row = cur.fetchone()

    if row is None:
        print("No non-empty alias found.")
    else:
        alias = row["alias"]
        result = resolve_by_alias(alias)

        print("Test alias:", alias)
        print("Resolution status:", result["resolution_status"])
        print("Resolution method:", result["resolution_method"])
        print("Confidence:", result["resolution_confidence"])
        print("Reason:", result["reason"])

        if result["institution"]:
            print("Matched institution:", result["institution"]["name"])

        assert result["resolution_status"] == "resolved", (
            "Expected this existing alias to resolve uniquely."
        )
        assert result["resolution_method"] == "alias"
        print("ALIAS TEST PASSED")


if __name__ == "__main__":
    main()
