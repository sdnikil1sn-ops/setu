
import math
import os
import sys

from dotenv import load_dotenv


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
    # Use the same task instruction for all comparison texts.
    instructed_text = f"task: semantic similarity | text: {text}"

    response = client.models.embed_content(
        model=model,
        contents=instructed_text,
        config=types.EmbedContentConfig(
            output_dimensionality=768
        ),
    )

    if not response.embeddings:
        raise ValueError("The API returned no embeddings.")

    values = response.embeddings[0].values

    if not values:
        raise ValueError("The API returned an empty vector.")

    return [float(value) for value in values]


def main():
    from google import genai
    from google.genai import types

    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv(
        "GEMINI_EMBEDDING_MODEL",
        "gemini-embedding-2",
    )

    if not api_key or api_key == "PASTE_YOUR_GOOGLE_API_KEY_HERE":
        print("ERROR: Configure GEMINI_API_KEY in backend/.env.")
        return 1

    # Synthetic test data only. No database access.
    english = (
        "The college did not refund my tuition fee "
        "after I cancelled my admission."
    )

    tamil = (
        "சேர்க்கையை ரத்து செய்த பிறகும் கல்லூரி "
        "எனது கல்விக் கட்டணத்தைத் திருப்பித் தரவில்லை."
    )

    unrelated = (
        "The college bus arrives late every morning."
    )

    print("Model:", model)
    print("Generating embeddings for three synthetic texts...")

    try:
        client = genai.Client(api_key=api_key)

        english_vector = get_embedding(client, model, english)
        tamil_vector = get_embedding(client, model, tamil)
        unrelated_vector = get_embedding(client, model, unrelated)

        cross_language = cosine_similarity(
            english_vector, tamil_vector
        )

        unrelated_score = cosine_similarity(
            english_vector, unrelated_vector
        )

        print("\nHosted inference succeeded.")
        print("Embedding dimensions:", len(english_vector))
        print(
            "English vs Tamil similarity:",
            round(cross_language, 4),
        )
        print(
            "English vs unrelated complaint similarity:",
            round(unrelated_score, 4),
        )

        if cross_language > unrelated_score:
            print(
                "\nInitial result: the related cross-language "
                "pair scored higher than the unrelated pair."
            )
        else:
            print(
                "\nInitial result: expected score ordering was "
                "not observed. Investigate before integration."
            )

        print(
            "\nThis is a smoke test, not a validated threshold "
            "or an accuracy benchmark."
        )
        return 0

    except Exception as exc:
        print("\nHosted inference test failed.")
        print("Error type:", type(exc).__name__)
        print("Error details:", str(exc)[:500])
        print(
            "Check API key validity, model availability, "
            "network access, and account quota."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
