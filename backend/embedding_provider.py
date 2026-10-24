
"""Provider-independent semantic similarity with safe fallbacks.

This module is read-only: it does not connect to or modify the database.
It never compares vectors produced by different providers.
"""

import json
import math
import os
from typing import Any
from urllib.request import Request, urlopen


JINA_API_URL = "https://api.jina.ai/v1/embeddings"
JINA_DEFAULT_MODEL = "jina-embeddings-v3"
GEMINI_DEFAULT_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSIONS = 768


def cosine_similarity(vector_a: list[float],
                      vector_b: list[float]) -> float:
    """Calculate cosine similarity for two compatible vectors."""
    if not vector_a or not vector_b:
        raise ValueError("Embedding vectors cannot be empty.")

    if len(vector_a) != len(vector_b):
        raise ValueError("Embedding dimensions do not match.")

    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(value * value for value in vector_a))
    norm_b = math.sqrt(sum(value * value for value in vector_b))

    if norm_a == 0 or norm_b == 0:
        raise ValueError("Embedding vector has zero length.")

    return max(-1.0, min(1.0, dot_product / (norm_a * norm_b)))


def _embed_with_gemini(
    texts: list[str],
    api_key: str,
    model: str,
) -> list[list[float]]:
    """Generate all vectors for a pair using Gemini only."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    vectors = []

    for text in texts:
        response = client.models.embed_content(
            model=model,
            contents=f"task: semantic similarity | text: {text}",
            config=types.EmbedContentConfig(
                output_dimensionality=EMBEDDING_DIMENSIONS
            ),
        )

        if not response.embeddings:
            raise ValueError("Gemini returned no embeddings.")

        values = response.embeddings[0].values

        if not values:
            raise ValueError("Gemini returned an empty embedding.")

        vectors.append([float(value) for value in values])

    return vectors


def _embed_with_jina(
    texts: list[str],
    api_key: str,
    model: str,
) -> list[list[float]]:
    """Generate all vectors for a pair using Jina only."""
    payload = {
        "model": model,
        "task": "text-matching",
        "input": texts,
    }

    request = Request(
        JINA_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))

    entries = result.get("data", [])
    if len(entries) != len(texts):
        raise ValueError("Jina returned an unexpected number of vectors.")

    entries.sort(key=lambda item: item["index"])
    vectors = []

    for entry in entries:
        values = entry.get("embedding")
        if not values:
            raise ValueError("Jina returned an empty embedding.")

        vectors.append([float(value) for value in values])

    return vectors


def semantic_similarity(
    text_a: str,
    text_b: str,
) -> dict[str, Any]:
    """Try Gemini, then configured Jina, then return unavailable.

    The same provider must generate both vectors in each attempt.
    Provider errors are reported by type, not by raw error text.
    """
    if not isinstance(text_a, str) or not isinstance(text_b, str):
        raise TypeError("Both inputs must be strings.")

    if not text_a.strip() or not text_b.strip():
        raise ValueError("Both texts must be non-empty.")

    texts = [text_a, text_b]
    attempts = []

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model = os.getenv(
        "GEMINI_EMBEDDING_MODEL",
        GEMINI_DEFAULT_MODEL,
    ).strip()

    jina_key = os.getenv("JINA_API_KEY", "").strip()
    jina_model = os.getenv(
        "JINA_EMBEDDING_MODEL",
        JINA_DEFAULT_MODEL,
    ).strip()

    providers = []

    if gemini_key:
        providers.append((
            "gemini",
            gemini_model,
            lambda: _embed_with_gemini(
                texts, gemini_key, gemini_model
            ),
        ))

    if jina_key:
        providers.append((
            "jina",
            jina_model,
            lambda: _embed_with_jina(
                texts, jina_key, jina_model
            ),
        ))

    for provider, model, generate_vectors in providers:
        try:
            vectors = generate_vectors()

            if len(vectors) != 2:
                raise ValueError("Unexpected number of vectors.")

            score = cosine_similarity(vectors[0], vectors[1])

            return {
                "status": "available",
                "semantic_available": True,
                "provider": provider,
                "model": model,
                "similarity": score,
                "dimensions": len(vectors[0]),
                "fallback_used": provider != "gemini",
                "failed_providers": attempts,
            }

        except Exception as exc:
            # Avoid returning raw exceptions that could contain
            # request details or sensitive information.
            attempts.append({
                "provider": provider,
                "error_type": type(exc).__name__,
            })

    return {
        "status": "unavailable",
        "semantic_available": False,
        "provider": None,
        "model": None,
        "similarity": None,
        "dimensions": None,
        "fallback_used": False,
        "failed_providers": attempts,
        "message": (
            "Semantic matching is unavailable. "
            "Use the existing heuristic signals instead."
        ),
    }
