
import math
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

from institution_resolution import get_connection
from overlap_engine import score_pair


def cosine_similarity(a, b):
    if len(a) != len(b):
        raise ValueError("Embedding dimensions do not match.")

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        raise ValueError("An embedding has zero length.")

    return dot / (norm_a * norm_b)


def get_embedding(client, model, text):
    response = client.models.embed_content(
        model=model,
        contents=f"task: semantic similarity | text: {text or ''}",
        config=types.EmbedContentConfig(
            output_dimensionality=768
        ),
    )

    if not response.embeddings:
        raise ValueError("The API returned no embedding.")

    values = response.embeddings[0].values

    if not values:
        raise ValueError("The API returned an empty embedding.")

    return [float(value) for value in values]


def case_identifier(case):
    return str(case.get("case_id") or case.get("case_ref") or "")


def main():
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv(
        "GEMINI_EMBEDDING_MODEL",
        "gemini-embedding-2",
    )

    if not api_key or api_key == "PASTE_YOUR_GOOGLE_API_KEY_HERE":
        print("ERROR: Configure GEMINI_API_KEY in backend/.env.")
        return 1

    results = []
    embedding_cache = {}

    try:
        client = genai.Client(api_key=api_key)

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM public.ground_truth_pairs
                    ORDER BY pair_id
                    """
                )
                ground_truth = cur.fetchall()

                for pair in ground_truth:
                    cur.execute(
                        """
                        SELECT *
                        FROM public.complaint_cases
                        WHERE case_id = %s OR case_ref = %s
                        LIMIT 1
                        """,
                        (pair["case_a"], pair["case_a"]),
                    )
                    case_a = cur.fetchone()

                    cur.execute(
                        """
                        SELECT *
                        FROM public.complaint_cases
                        WHERE case_id = %s OR case_ref = %s
                        LIMIT 1
                        """,
                        (pair["case_b"], pair["case_b"]),
                    )
                    case_b = cur.fetchone()

                    result = {
                        "pair_id": pair["pair_id"],
                        "overlap_type": pair["overlap_type"],
                        "expected_overlap": pair["is_true_overlap"],
                        "semantic_similarity": None,
                        "status": "evaluated",
                    }

                    if case_a is None or case_b is None:
                        result["status"] = "missing_case"
                        results.append(result)
                        continue

                    restricted = (
                        bool(case_a["is_restricted"])
                        or bool(case_b["is_restricted"])
                    )

                    same_institution = (
                        case_a["institution_id"] is not None
                        and case_a["institution_id"]
                        == case_b["institution_id"]
                    )

                    same_group = (
                        case_a["group_id"] is not None
                        and case_a["group_id"] == case_b["group_id"]
                    )

                    cross_bureau = (
                        case_a["source_system"]
                        != case_b["source_system"]
                    )

                    evidence = score_pair(
                        {
                            "institution_id": case_a["institution_id"],
                            "group_id": case_a["group_id"],
                            "category": case_a["category"],
                            "text": case_a["text"],
                            "received_date": case_a["received_date"],
                        },
                        {
                            "institution_id": case_b["institution_id"],
                            "group_id": case_b["group_id"],
                            "category": case_b["category"],
                            "text": case_b["text"],
                            "received_date": case_b["received_date"],
                        },
                    )

                    result.update({
                        "baseline_score": evidence["score"],
                        "baseline_text_similarity":
                            evidence["text_similarity"],
                        "same_institution": same_institution,
                        "same_group": same_group,
                        "cross_bureau": cross_bureau,
                        "restricted": restricted,
                        "candidate_eligible": (
                            (same_institution or same_group)
                            and cross_bureau
                            and not restricted
                        ),
                    })

                    if restricted:
                        # Never send restricted complaint text externally.
                        result["status"] = "skipped_restricted"
                        results.append(result)
                        continue

                    try:
                        vector_a_key = case_identifier(case_a)
                        vector_b_key = case_identifier(case_b)

                        if vector_a_key not in embedding_cache:
                            embedding_cache[vector_a_key] = get_embedding(
                                client, model, case_a["text"]
                            )

                        if vector_b_key not in embedding_cache:
                            embedding_cache[vector_b_key] = get_embedding(
                                client, model, case_b["text"]
                            )

                        result["semantic_similarity"] = cosine_similarity(
                            embedding_cache[vector_a_key],
                            embedding_cache[vector_b_key],
                        )

                    except Exception as exc:
                        # Do not print complaint text or API credentials.
                        result["status"] = (
                            "embedding_error:" + type(exc).__name__
                        )

                    results.append(result)

        print("=== SETU multilingual ground-truth evaluation ===")
        print("Model:", model)

        for result in results:
            print(
                f"\n{result['pair_id']} - "
                f"{result['overlap_type']}"
            )
            print("Expected overlap:", result["expected_overlap"])
            print("Status:", result["status"])

            if "baseline_score" in result:
                print("Existing baseline score:", result["baseline_score"])
                print(
                    "Existing text similarity:",
                    result["baseline_text_similarity"],
                )
                print("Same institution:", result["same_institution"])
                print("Same group:", result["same_group"])
                print("Cross-bureau:", result["cross_bureau"])
                print("Restricted:", result["restricted"])
                print("Candidate eligible:", result["candidate_eligible"])

            if result["semantic_similarity"] is not None:
                print(
                    "Hosted semantic similarity:",
                    round(result["semantic_similarity"], 4),
                )

        scored = [
            result for result in results
            if result["semantic_similarity"] is not None
        ]

        positives = [
            result for result in scored
            if result["expected_overlap"] is True
        ]
        negatives = [
            result for result in scored
            if result["expected_overlap"] is False
        ]

        print("\n=== Summary ===")
        print("Ground-truth pairs:", len(results))
        print("Pairs with semantic scores:", len(scored))
        print(
            "Pairs skipped because restricted:",
            sum(r["status"] == "skipped_restricted" for r in results),
        )
        print(
            "Pairs with errors or missing records:",
            sum(
                r["status"] == "missing_case"
                or r["status"].startswith("embedding_error:")
                for r in results
            ),
        )
        print("Positive pairs scored:", len(positives))
        print("Negative pairs scored:", len(negatives))
        print("Unique embeddings requested:", len(embedding_cache))

        if positives:
            print(
                "Mean positive semantic similarity:",
                round(
                    sum(r["semantic_similarity"] for r in positives)
                    / len(positives),
                    4,
                ),
            )

        if negatives:
            print(
                "Mean negative semantic similarity:",
                round(
                    sum(r["semantic_similarity"] for r in negatives)
                    / len(negatives),
                    4,
                ),
            )

        if positives and negatives:
            positive_mean = sum(
                r["semantic_similarity"] for r in positives
            ) / len(positives)

            negative_mean = sum(
                r["semantic_similarity"] for r in negatives
            ) / len(negatives)

            print(
                "Mean separation (positive minus negative):",
                round(positive_mean - negative_mean, 4),
            )

        print(
            "\nInterpretation: semantic similarity measures textual "
            "relatedness, not confirmed overlap. The dataset is small "
            "and synthetic, so do not treat these results as a "
            "production accuracy benchmark or calibrated threshold."
        )
        print(
            "This script performs database reads only. It does not "
            "insert, update, or delete database records."
        )

        return 0

    except Exception as exc:
        print("\nEvaluation failed.")
        print("Error type:", type(exc).__name__)
        print("Error details:", str(exc)[:500])
        return 1


if __name__ == "__main__":
    sys.exit(main())
