
from institution_resolution import (
    get_connection,
    resolve_by_normalized_name,
    normalize_name,
)

def main():
    # Read one existing canonical institution name.
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT name
                FROM public.institutions
                WHERE name IS NOT NULL
                  AND BTRIM(name) <> %s
                LIMIT 1
                """,
                ("",),
            )
            row = cur.fetchone()

    assert row is not None, "No institution name found."

    original_name = row["name"]

    # Change capitalization and punctuation without changing the words.
    test_name = f"  {original_name.upper()}...  "

    print("Original name:", original_name)
    print("Normalized test input:", normalize_name(test_name))

    result = resolve_by_normalized_name(test_name)

    print("Status:", result["resolution_status"])
    print("Method:", result["resolution_method"])
    print("Reason:", result["reason"])

    if result["institution"]:
        print("Matched institution:", result["institution"]["name"])

    assert result["resolution_status"] == "resolved"
    assert result["resolution_method"] == "normalized_name"
    assert normalize_name(test_name) == normalize_name(original_name)

    print("NORMALIZED NAME TEST PASSED")


if __name__ == "__main__":
    main()
