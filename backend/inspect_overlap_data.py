
from institution_resolution import get_connection


def main():
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 1. Count complaints by source system.
            cur.execute(
                """
                SELECT
                    source_system,
                    COUNT(*) AS complaint_count
                FROM public.complaint_cases
                GROUP BY source_system
                ORDER BY source_system
                """
            )
            source_counts = cur.fetchall()

            # 2. Measure institution-linked complaints.
            cur.execute(
                """
                SELECT
                    COUNT(*) AS total_cases,
                    COUNT(institution_id) AS linked_cases,
                    COUNT(*) FILTER (
                        WHERE institution_id IS NULL
                    ) AS unlinked_cases,
                    COUNT(*) FILTER (
                        WHERE is_restricted = TRUE
                    ) AS restricted_cases
                FROM public.complaint_cases
                """
            )
            case_summary = cur.fetchone()

            # 3. Count potential cross-bureau pairs sharing an institution.
            # This counts candidates, not confirmed complaint overlaps.
            cur.execute(
                """
                SELECT COUNT(*) AS candidate_pairs
                FROM public.complaint_cases AS a
                JOIN public.complaint_cases AS b
                  ON a.institution_id = b.institution_id
                 AND a.source_system < b.source_system
                WHERE a.institution_id IS NOT NULL
                  AND a.source_system <> b.source_system
                """
            )
            pair_summary = cur.fetchone()

            # 4. Inspect categories across source systems.
            cur.execute(
                """
                SELECT
                    source_system,
                    category,
                    COUNT(*) AS complaint_count
                FROM public.complaint_cases
                GROUP BY source_system, category
                ORDER BY source_system, complaint_count DESC
                LIMIT 30
                """
            )
            category_summary = cur.fetchall()

    print("\n=== Complaints by source system ===")
    for row in source_counts:
        print(dict(row))

    print("\n=== Institution linkage and restrictions ===")
    print(dict(case_summary))

    print("\n=== Potential cross-bureau pairs ===")
    print(dict(pair_summary))

    print("\n=== Categories by source system ===")
    for row in category_summary:
        print(dict(row))

    print(
        "\nNote: Shared institution means a candidate pair only. "
        "It does not prove that two complaints concern the same issue."
    )


if __name__ == "__main__":
    main()
