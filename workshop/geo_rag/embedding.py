from __future__ import annotations

import os

from llama_index.embeddings.openai import OpenAIEmbedding

from .config import EMBEDDING_MODEL


def build_embedding_model(model_name: str | None = None) -> OpenAIEmbedding:
    """Construct an OpenAI embedding model used across the pipeline."""

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY missing. Populate .env or export the key.")
    return OpenAIEmbedding(model=model_name or EMBEDDING_MODEL)
