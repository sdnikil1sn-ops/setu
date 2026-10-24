
from overlap_engine import find_overlap_candidates


def main():
    result = find_overlap_candidates(limit=20, minimum_score=50)

    print("Total candidates:", result["candidate_count"])
    print("Returned:", result["returned_count"])
    print()

    for i, item in enumerate(result["items"], start=1):
        print(
            i,
            item["case_a"],
            "<->",
            item["case_b"],
            "| scope:", item["scope"],
            "| score:", item["score"],
            "| categories:",
            item["category_a"], "/", item["category_b"],
            "| days:", item["days_apart"],
        )


if __name__ == "__main__":
    main()
