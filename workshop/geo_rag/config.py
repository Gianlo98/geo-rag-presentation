from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env", override=False)

WEBSITE_DIR = ROOT_DIR / "website"
LOCAL_CONTENT_DIR = WEBSITE_DIR / "content" / "articles"
PLAYBOOK_PATH = WEBSITE_DIR / "playbook.txt"
NOISE_DIR = ROOT_DIR / "data" / "noise" / "recipes"
BACKLINKS_PATH = ROOT_DIR / "data" / "backlinks.json"
EMBEDDING_CACHE_PATH = ROOT_DIR / "data" / "embeddings" / "precomputed_embeddings.json"
DEFAULT_DB_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/geo_rag"
)
EMBEDDING_MODEL = os.getenv("GEO_RAG_EMBED_MODEL", "text-embedding-3-small")
VECTOR_DIMENSION = int(os.getenv("GEO_RAG_VECTOR_DIM", "1536"))
PGVECTOR_TABLE = os.getenv("GEO_RAG_TABLE", "geo_rag_nodes")
MAX_RETRIEVAL_RESULTS = int(os.getenv("GEO_RAG_TOP_K", "12"))
RETRIEVAL_EXPANSION = int(os.getenv("GEO_RAG_RETRIEVER_EXPANSION", "5"))
RETRIEVER_MAX_K = int(os.getenv("GEO_RAG_RETRIEVER_MAX_K", "1000"))
RELEVANCE_THRESHOLD = float(os.getenv("GEO_RAG_RELEVANCE_MIN", "0.3"))
USE_LLM_RERANKER = os.getenv("GEO_RAG_USE_RERANKER", "1") not in {"0", "false", "False"}
RERANK_MODEL = os.getenv("GEO_RAG_RERANK_MODEL", "ret-rr-skysight-v3")
