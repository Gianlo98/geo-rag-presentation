#!/usr/bin/env python3
"""Generate and persist OpenAI embeddings for the GEO workshop dataset."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from geo_rag.config import (  # noqa: E402
    BACKLINKS_PATH,
    EMBEDDING_CACHE_PATH,
    EMBEDDING_MODEL,
    LOCAL_CONTENT_DIR,
    NOISE_DIR,
    VECTOR_DIMENSION,
)
from geo_rag.data_sources import (  # noqa: E402
    build_backlink_index,
    load_backlinks,
    load_local_articles,
    load_noise_documents,
)
from geo_rag.prep import enrich_documents  # noqa: E402

BATCH_SIZE = 16


def chunked(seq: List[str], size: int) -> Iterable[List[str]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def embed_texts(texts: List[str], model: str) -> List[List[float]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY missing. Export it or populate .env before running.")
    client = OpenAI()
    vectors: List[List[float]] = []
    for batch in chunked(texts, BATCH_SIZE):
        response = client.embeddings.create(model=model, input=batch)
        # OpenAI returns embeddings in the same order
        vectors.extend([record.embedding for record in response.data])
    return vectors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=EMBEDDING_CACHE_PATH, help="Where to store the JSON cache")
    parser.add_argument("--model", default=EMBEDDING_MODEL, help="OpenAI embedding model name")
    args = parser.parse_args()

    local_docs = load_local_articles(LOCAL_CONTENT_DIR)
    noise_docs = load_noise_documents(NOISE_DIR)
    backlinks = build_backlink_index(load_backlinks(BACKLINKS_PATH))
    documents = enrich_documents(local_docs + noise_docs, backlinks)
    texts = [doc.text for doc in documents]
    embeddings = embed_texts(texts, args.model)

    payload = {
        "embedding_dim": len(embeddings[0]) if embeddings else VECTOR_DIMENSION,
        "document_count": len(documents),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "documents": [],
    }
    for doc, embedding in zip(documents, embeddings):
        payload["documents"].append(
            {
                "doc_id": doc.doc_id,
                "slug": doc.metadata.get("slug", doc.doc_id),
                "metadata": doc.metadata,
                "text": doc.text,
                "embedding": [float(f"{value:.6f}") for value in embedding],
            }
        )
    args.dest.parent.mkdir(parents=True, exist_ok=True)
    args.dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved {len(documents)} embeddings to {args.dest}")


if __name__ == "__main__":
    main()
