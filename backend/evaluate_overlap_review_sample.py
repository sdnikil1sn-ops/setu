
import csv
import math
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


BASE_DIR = Path(__file__).parent
INPUT_FILE = BASE_DIR / "overlap_review_sample.csv"
OUTPUT_FILE = BASE_DIR / "overlap_review_sample_scored.csv"


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
        contents=f"task: semantic similarity | text: {text}",
        config=types.EmbedContentConfig(
            output_dimensionality=768
        ),
    )

    if not response.embeddings or not response.embeddings[0].values:
        raise ValueError("The API returned no embedding values.")

    return [float(value) for value in response.embeddings[0].values]


def assign_ranks(rows, score_field, rank_field):
    ranked = [
        (index, float(row[score_field]))
        for index, row in enumerate(rows)
        if row.get(score_field) not in ("", None)
    ]

    ranked.sort(key=lambda item: item[1], reverse=True)

    for rank, (index, _) in enumerate(ranked, start=1):
        rows[index][rank_field] = rank


def main():
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv(
        "GEMINI_EMBEDDING_MODEL",
        "gemini-embedding-2",
    )

    if not api_key:
        print("ERROR: GEMINI_API_KEY is missing from backend/.env.")
        return 1

    if not INPUT_FILE.exists():
        print("ERROR: Review sample CSV not found:")
        print(INPUT_FILE)
        return 1

    with INPUT_FILE.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        original_fields = reader.fieldnames or []

    required = {
        "case_a",
        "case_b",
        "score",
        "text_a",
        "text_b",
    }

    missing = required - set(original_fields)

    if missing:
        print("ERROR: CSV is missing columns:", ", ".join(sorted(missing)))
        return 1

    # Only these non-restricted sample records are processed.
    # Cache embeddings by case ID and text for this run.
    embedding_cache = {}

    def cached_embedding(client, case_id, text):
        key = (case_id, text or "")

        if key not in embedding_cache:
            if not text or not text.strip():
                raise ValueError(
                    f"No text available for case {case_id}."
                )

            embedding_cache[key] = get_embedding(
                client,
                model,
                text.strip(),
            )

        return embedding_cache[key]

    try:
        client = genai.Client(api_key=api_key)

        print("Input pairs:", len(rows))
        print("Model:", model)
        print("Generating embeddings for the review sample...")
        print("The complaint text will be sent to Google's API.")

        for index, row in enumerate(rows, start=1):
            try:
                vector_a = cached_embedding(
                    client,
                    row["case_a"],
                    row["text_a"],
                )

                vector_b = cached_embedding(
                    client,
                    row["case_b"],
                    row["text_b"],
                )

                row["semantic_similarity"] = round(
                    cosine_similarity(vector_a, vector_b),
                    6,
                )
                row["embedding_status"] = "success"

            except Exception as exc:
                row["semantic_similarity"] = ""
                row["embedding_status"] = (
                    "error:" + type(exc).__name__
                )

                print(
                    f"Pair {index}/{len(rows)} failed:",
                    type(exc).__name__,
                )

            if index % 5 == 0 or index == len(rows):
                print(f"Processed {index}/{len(rows)} pairs")

        # Rank both systems on this same sample.
        for row in rows:
            row["baseline_rank"] = ""
            row["semantic_rank"] = ""

        assign_ranks(rows, "score", "baseline_rank")
        assign_ranks(
            rows,
            "semantic_similarity",
            "semantic_rank",
        )

        output_fields = list(original_fields)

        for field in (
            "semantic_similarity",
            "embedding_status",
            "baseline_rank",
            "semantic_rank",
        ):
            if field not in output_fields:
                output_fields.append(field)

        with OUTPUT_FILE.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=output_fields,
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(rows)

        successful = [
            row for row in rows
            if row.get("semantic_similarity") not in ("", None)
        ]

        print("\n=== Evaluation summary ===")
        print("Pairs in sample:", len(rows))
        print("Pairs with semantic scores:", len(successful))
        print("Unique embeddings requested:", len(embedding_cache))
        print("Results saved to:", OUTPUT_FILE)

        if successful:
            values = [
                float(row["semantic_similarity"])
                for row in successful
            ]

            print(
                "Mean semantic similarity:",
                round(sum(values) / len(values), 4),
            )

            rank_changes = [
                abs(
                    int(row["baseline_rank"])
                    - int(row["semantic_rank"])
                )
                for row in successful
            ]

            print(
                "Mean absolute rank difference:",
                round(sum(rank_changes) / len(rank_changes), 2),
            )

            print("\nTop 5 by semantic similarity:")

            top = sorted(
                successful,
                key=lambda row: float(row["semantic_similarity"]),
                reverse=True,
            )[:5]

            for row in top:
                print(
                    row["case_a"],
                    "<->",
                    row["case_b"],
                    "| semantic:",
                    row["semantic_similarity"],
                    "| baseline:",
                    row["score"],
                )

        print(
            "\nImportant: without verified labels, this measures "
            "ranking differences, not accuracy or overlap detection."
        )
        print(
            "The input file and database were not modified."
        )

        return 0 if successful else 1

    except Exception as exc:
        print("\nEvaluation stopped.")
        print("Error type:", type(exc).__name__)
        print("Error details:", str(exc)[:500])
        print("Check API access, model availability, and quota.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
