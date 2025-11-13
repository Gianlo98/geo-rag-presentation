from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence
from urllib.parse import urlparse

import psycopg2
from psycopg2 import sql
from llama_index.core import ServiceContext, StorageContext, VectorStoreIndex
from llama_index.core.postprocessor import LLMRerank
from llama_index.core.schema import QueryBundle, TextNode
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.llms.openai import OpenAI

from .config import (
    BACKLINKS_PATH,
    DEFAULT_DB_URL,
    EMBEDDING_CACHE_PATH,
    EMBEDDING_MODEL,
    LOCAL_CONTENT_DIR,
    VECTOR_DIMENSION,
    MAX_RETRIEVAL_RESULTS,
    RETRIEVAL_EXPANSION,
    RETRIEVER_MAX_K,
    RELEVANCE_THRESHOLD,
    NOISE_DIR,
    PGVECTOR_TABLE,
    PLAYBOOK_PATH,
    RERANK_MODEL,
    USE_LLM_RERANKER,
)
from .data_sources import (
    SourceDocument,
    build_backlink_index,
    load_backlinks,
    load_local_articles,
    load_noise_documents,
)
from .embedding import build_embedding_model
from .prep import enrich_documents
from .playbook import PlaybookGuidance
from .prioritizer import GeoPrioritizer, GeoRankedDocument


def _patch_pgvector_schema_bug() -> None:
    if getattr(PGVectorStore, "_geo_patch_applied", False):
        return

    def _create_schema_if_not_exists(self: PGVectorStore) -> None:  # type: ignore[name-defined]
        if not self.schema_name:
            return
        from sqlalchemy import text

        with self._session() as session, session.begin():
            check_stmt = text(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema_name"
            )
            result = session.execute(check_stmt, {"schema_name": self.schema_name}).fetchone()
            if not result and self.schema_name != "public":
                session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{self.schema_name}"'))
            session.commit()

    PGVectorStore._create_schema_if_not_exists = _create_schema_if_not_exists  # type: ignore[attr-defined]
    PGVectorStore._geo_patch_applied = True  # type: ignore[attr-defined]


_patch_pgvector_schema_bug()


@dataclass
class PipelineConfig:
    db_url: str = DEFAULT_DB_URL
    content_dir: Path = LOCAL_CONTENT_DIR
    noise_dir: Path = NOISE_DIR
    backlinks_path: Path = BACKLINKS_PATH
    playbook_path: Path = PLAYBOOK_PATH
    embedding_cache_path: Path = EMBEDDING_CACHE_PATH
    table_name: str = PGVECTOR_TABLE
    use_cache: bool = True
    refresh_cache: bool = False
    reset_table: bool = True
    top_k: int = MAX_RETRIEVAL_RESULTS
    retriever_expansion: int = RETRIEVAL_EXPANSION
    retriever_max_k: int = RETRIEVER_MAX_K
    relevance_threshold: float = RELEVANCE_THRESHOLD
    use_llm_reranker: bool = USE_LLM_RERANKER
    rerank_model: str = RERANK_MODEL
    embedding_model: str = EMBEDDING_MODEL


class GeoRAGPipeline:
    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig()
        self.embed_model = build_embedding_model(
            self.config.embedding_model or None
        )
        self.playbook = PlaybookGuidance.from_file(self.config.playbook_path)
        self.backlink_index = build_backlink_index(load_backlinks(self.config.backlinks_path))
        self.vector_store: PGVectorStore | None = None
        self.storage_context: StorageContext | None = None
        self.index: VectorStoreIndex | None = None
        self.retriever = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.reranker = self._build_reranker()
        self.prioritizer = GeoPrioritizer(self.backlink_index, self.playbook)
        self._nodes: List[TextNode] = []
        self._embed_dim: int | None = None

    # Public API ---------------------------------------------------------
    def load(self) -> None:
        documents = self._load_documents()
        nodes = self._build_nodes(documents)
        embeddings = self._load_or_create_embeddings(nodes)
        self._bootstrap_vector_store(nodes, embeddings)

    def attach_existing_vector_store(self) -> None:
        params = self._parse_db_url(self.config.db_url)
        embed_dim = self._resolve_embed_dim()
        self.vector_store = PGVectorStore.from_params(
            database=params["database"],
            host=params["host"],
            password=params["password"],
            port=params["port"],
            user=params["user"],
            table_name=self.config.table_name,
            embed_dim=embed_dim,
        )
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        service_context = ServiceContext.from_defaults(embed_model=self.embed_model)
        self.index = VectorStoreIndex.from_vector_store(
            self.vector_store,
            storage_context=self.storage_context,
            service_context=service_context,
        )
        similarity_k = min(
            self.config.retriever_max_k,
            max(self.config.top_k * self.config.retriever_expansion, self.config.top_k + 5),
        )
        self.retriever = self.index.as_retriever(similarity_top_k=similarity_k)
        self._similarity_k = similarity_k

    def query(self, text: str, *, user_region: str | None = None) -> List[GeoRankedDocument]:
        if not self.retriever:
            raise RuntimeError("Pipeline not initialized. Call load() first.")
        raw_nodes = list(self.retriever.retrieve(text))
        self.logger.debug("Retriever returned %d candidates for query '%s'", len(raw_nodes), text)
        chunk_matches: Dict[str, int] = {}
        for candidate in raw_nodes:
            slug = candidate.node.metadata.get("slug")
            if slug:
                chunk_matches[slug] = chunk_matches.get(slug, 0) + 1
        reranked_nodes = raw_nodes
        if self.reranker:
            try:
                reranked_nodes = list(
                    self.reranker.postprocess_nodes(
                        raw_nodes,
                        query_bundle=QueryBundle(query_str=text),
                    )
                )
                if len(reranked_nodes) < self.config.top_k:
                    seen = {node.node.id_ for node in reranked_nodes}
                    for candidate in raw_nodes:
                        if candidate.node.id_ in seen:
                            continue
                        reranked_nodes.append(candidate)
                        seen.add(candidate.node.id_)
                        if len(reranked_nodes) >= self.config.top_k:
                            break
                if not reranked_nodes:
                    reranked_nodes = raw_nodes
            except Exception as exc:  # noqa: BLE001 - logging fallback
                self.logger.warning(
                    "LLM reranker failed (%s); falling back to vector scores.", exc
                )
                reranked_nodes = raw_nodes
        ranked = self.prioritizer.rerank(
            reranked_nodes,
            user_region=user_region,
            chunk_matches=chunk_matches,
            query_text=text,
        )
        seen_docs = set()
        deduped: List[GeoRankedDocument] = []
        threshold = self.config.relevance_threshold
        for doc in ranked:
            if doc.slug in seen_docs:
                continue
            relevance_raw = doc.metadata.get("score_breakdown", {}).get("relevance_raw")
            if relevance_raw is not None and relevance_raw < threshold:
                continue
            seen_docs.add(doc.slug)
            deduped.append(doc)
        return deduped

    # Internal helpers ---------------------------------------------------
    def _load_documents(self) -> List[SourceDocument]:
        local_docs = load_local_articles(self.config.content_dir)
        noise_docs = load_noise_documents(self.config.noise_dir)
        all_docs = local_docs + noise_docs
        return enrich_documents(all_docs, self.backlink_index)

    def _build_nodes(self, documents: Sequence[SourceDocument]) -> List[TextNode]:
        nodes: List[TextNode] = []
        local_chunks = 0
        external_chunks = 0
        for doc in documents:
            chunks = self._generate_chunks(doc)
            for suffix, text, metadata in chunks:
                node_id = f"{doc.doc_id}::{suffix}"
                node = TextNode(text=text, id_=node_id, metadata=metadata)
                nodes.append(node)
                if metadata.get("source_type") == "local_site":
                    local_chunks += 1
                else:
                    external_chunks += 1
        self._nodes = nodes
        self.logger.info(
            "Indexed %d chunks (%d local / %d external)",
            len(nodes),
            local_chunks,
            external_chunks,
        )
        return nodes

    def _generate_chunks(self, doc: SourceDocument) -> List[tuple[str, str, Dict[str, Any]]]:
        base_meta = dict(doc.metadata)
        chunks: List[tuple[str, str, Dict[str, Any]]] = []

        full_meta = dict(base_meta)
        full_meta["chunk_type"] = "full"
        full_meta["chunk_rank"] = 1
        chunks.append(("full", self._compose_full_text(doc, base_meta), full_meta))

        meta_text = self._compose_meta_snippet(base_meta)
        if meta_text:
            meta_meta = dict(base_meta)
            meta_meta["chunk_type"] = "meta"
            meta_meta["chunk_rank"] = 2
            chunks.append(("meta", meta_text, meta_meta))

        assets_text = self._compose_assets_snippet(base_meta)
        if assets_text:
            assets_meta = dict(base_meta)
            assets_meta["chunk_type"] = "assets"
            assets_meta["chunk_rank"] = 3
            chunks.append(("assets", assets_text, assets_meta))

        if base_meta.get("source_type") != "local_site":
            external_text = self._compose_external_snippet(base_meta, doc.text)
            if external_text:
                external_meta = dict(base_meta)
                external_meta["chunk_type"] = "external"
                external_meta["chunk_rank"] = 4
                chunks.append(("external", external_text, external_meta))

        structured_snippets = self._compose_structured_chunks(base_meta)
        for idx, snippet in enumerate(structured_snippets, start=1):
            structured_meta = dict(base_meta)
            structured_meta["chunk_type"] = f"structured_{idx}"
            structured_meta["chunk_rank"] = 4 + idx
            chunks.append((f"structured_{idx}", snippet, structured_meta))

        return chunks

    def _compose_full_text(self, doc: SourceDocument, metadata: Dict[str, Any]) -> str:
        sections: List[str] = []
        title = metadata.get("title")
        if title:
            sections.append(f"Title: {title}")
        summary = metadata.get("summary")
        if summary:
            sections.append(f"Summary: {summary}")
        keywords = metadata.get("keywords")
        if keywords:
            sections.append(f"Keywords: {keywords}")
        hero = metadata.get("hero_stat")
        if hero:
            sections.append(f"Hero Stat: {hero}")
        tags = metadata.get("tags")
        if tags:
            sections.append("Tags: " + ", ".join(tags))
        sections.append(doc.text)
        return "\n\n".join(section for section in sections if section)

    def _compose_meta_snippet(self, metadata: Dict[str, Any]) -> str:
        bits: List[str] = []
        if metadata.get("title"):
            bits.append(metadata["title"])
        if metadata.get("summary"):
            bits.append(metadata["summary"])
        metrics = metadata.get("metrics") or {}
        if metrics:
            metrics_desc = ", ".join(f"{k}:{v}" for k, v in metrics.items())
            bits.append(f"Metrics: {metrics_desc}")
        keywords = metadata.get("keywords")
        if keywords:
            bits.append(f"Keywords: {keywords}")
        hero = metadata.get("hero_stat")
        if hero:
            bits.append(hero)
        return " \n".join(bits)

    def _compose_assets_snippet(self, metadata: Dict[str, Any]) -> str:
        answer_assets = metadata.get("answer_assets") or []
        faq = metadata.get("faq") or []
        sections: List[str] = []
        if answer_assets:
            sections.append("Answer Assets:\n" + "\n".join(answer_assets[:5]))
        for item in faq[:2]:
            q = item.get("question")
            a = item.get("answer")
            if q and a:
                sections.append(f"FAQ: {q} -> {a}")
        comparisons = metadata.get("comparisons") or []
        for comp in comparisons[:2]:
            title = comp.get("title")
            angle = comp.get("angle")
            if title:
                sections.append(f"Related: {title} ({angle or ''})")
        return "\n".join(sections)

    def _compose_external_snippet(self, metadata: Dict[str, Any], body: str) -> str:
        domain = metadata.get("domain") or metadata.get("domain_slug")
        summary = metadata.get("summary") or body.split("\n", 1)[0]
        keywords = metadata.get("keywords") or metadata.get("tags")
        sections = []
        if domain:
            sections.append(f"Source Domain: {domain}")
        if summary:
            sections.append(summary)
        if keywords:
            if isinstance(keywords, list):
                keywords = ", ".join(keywords)
            sections.append(f"External Keywords: {keywords}")
        teaser = body.split("\n", 2)[0]
        if teaser and teaser not in sections:
            sections.append(teaser)
        return " \u2022 ".join(sections)

    def _compose_structured_chunks(self, metadata: Dict[str, Any]) -> List[str]:
        snippets: List[str] = []
        ingredients = metadata.get("ingredients") or metadata.get("microdata", {}).get("recipeIngredient") or []
        steps = metadata.get("steps") or metadata.get("microdata", {}).get("recipeInstructions") or []
        faq = metadata.get("faq") or []
        metrics = metadata.get("metrics") or {}

        if ingredients or steps:
            recipe_parts = []
            if ingredients:
                recipe_parts.append("Ingredients:\n" + "\n".join(f"- {item}" for item in ingredients[:12]))
            if steps:
                formatted_steps = []
                for idx, step in enumerate(steps[:8]):
                    if isinstance(step, dict):
                        text = step.get("text") or ""
                    else:
                        text = str(step)
                    if text:
                        formatted_steps.append(f"{idx+1}. {text}")
                if formatted_steps:
                    recipe_parts.append("Steps:\n" + "\n".join(formatted_steps))
            snippets.append("\n\n".join(recipe_parts))

        for item in faq[:3]:
            q = item.get("question")
            a = item.get("answer")
            if q and a:
                snippets.append(f"FAQ Focus\nQuestion: {q}\nAnswer: {a}")

        if metrics:
            metric_text = ", ".join(f"{k}:{v}" for k, v in list(metrics.items())[:6])
            snippets.append(f"Metrics Snapshot\n{metric_text}")

        return [snippet for snippet in snippets if snippet]

    def _load_or_create_embeddings(self, nodes: Sequence[TextNode]) -> List[List[float]]:
        cache_path = self.config.embedding_cache_path
        if self.config.use_cache and cache_path.exists() and not self.config.refresh_cache:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            cache_map = {
                (item.get("slug") or item.get("doc_id")): item["embedding"]
                for item in data.get("documents", [])
            }
            target_dim = self.embed_model.dimensions
            if len(cache_map) >= len(nodes):
                ordered = []
                for node in nodes:
                    slug = node.metadata.get("slug", node.id_)
                    vector = cache_map.get(slug)
                    if vector is None:
                        ordered = []
                        break
                    if len(vector) != target_dim:
                        ordered = []
                        break
                    ordered.append(vector)
                if ordered:
                    return ordered
        # Cache miss, compute and persist
        texts = [node.get_content(metadata_mode="all") for node in nodes]
        embeddings = self.embed_model.get_text_embedding_batch(texts)
        self._set_embed_dim(embeddings)
        self._write_cache(nodes, embeddings)
        return embeddings

    def _write_cache(self, nodes: Sequence[TextNode], embeddings: Sequence[Sequence[float]]) -> None:
        payload = {
            "embedding_dim": self._resolve_embed_dim(),
            "document_count": len(nodes),
            "documents": [],
        }
        for node, embedding in zip(nodes, embeddings):
            payload["documents"].append(
                {
                    "doc_id": node.id_,
                    "slug": node.metadata.get("slug", node.id_),
                    "metadata": node.metadata,
                    "text": node.get_content(metadata_mode="all"),
                    "embedding": list(map(float, embedding)),
                }
            )
        cache_path = self.config.embedding_cache_path
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _bootstrap_vector_store(self, nodes: Sequence[TextNode], embeddings: Sequence[Sequence[float]]) -> None:
        self._prepare_database()
        params = self._parse_db_url(self.config.db_url)
        embed_dim = self._resolve_embed_dim()
        self.vector_store = PGVectorStore.from_params(
            database=params["database"],
            host=params["host"],
            password=params["password"],
            port=params["port"],
            user=params["user"],
            table_name=self.config.table_name,
            embed_dim=embed_dim,
        )
        for node, embedding in zip(nodes, embeddings):
            node.embedding = embedding

        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        assert self.storage_context.docstore is not None
        self.storage_context.docstore.add_documents(nodes)
        self.vector_store.add(nodes=list(nodes))
        service_context = ServiceContext.from_defaults(embed_model=self.embed_model)
        self.index = VectorStoreIndex.from_vector_store(
            self.vector_store,
            storage_context=self.storage_context,
            service_context=service_context,
        )
        similarity_k = min(
            self.config.retriever_max_k,
            max(self.config.top_k * self.config.retriever_expansion, self.config.top_k + 5),
        )
        self.retriever = self.index.as_retriever(similarity_top_k=similarity_k)
        self._similarity_k = similarity_k

    def _prepare_database(self) -> None:
        conn = psycopg2.connect(self.config.db_url)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            if self.config.reset_table:
                physical_table = f"data_{self.config.table_name}".lower()
                self.logger.info("Resetting pgvector table %s", physical_table)
                cur.execute(
                    sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
                        sql.Identifier(physical_table)
                    )
                )
        conn.close()

    def _parse_db_url(self, url: str) -> Dict[str, str]:
        parsed = urlparse(url)
        database = parsed.path.lstrip("/")
        return {
            "database": database or "postgres",
            "host": parsed.hostname or "localhost",
            "port": str(parsed.port or 5432),
            "user": parsed.username or "postgres",
            "password": parsed.password or "postgres",
        }

    def _build_reranker(self) -> LLMRerank | None:
        if not self.config.use_llm_reranker:
            return None
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.logger.warning(
                "OPENAI_API_KEY missing; skipping ret-rr-skysight-v3 reranker."
            )
            return None

    def _set_embed_dim(self, embeddings: Sequence[Sequence[float]]) -> None:
        if embeddings:
            self._embed_dim = len(embeddings[0])
        elif self.embed_model.dimensions:
            self._embed_dim = int(self.embed_model.dimensions)
        elif self._embed_dim is None:
            self._embed_dim = VECTOR_DIMENSION

    def _resolve_embed_dim(self) -> int:
        if self._embed_dim is None:
            if self.embed_model.dimensions:
                self._embed_dim = int(self.embed_model.dimensions)
            else:
                self._embed_dim = VECTOR_DIMENSION
        return self._embed_dim
        try:
            llm = OpenAI(model=self.config.rerank_model)
            return LLMRerank(llm=llm, top_n=self.config.top_k)
        except Exception as exc:  # noqa: BLE001 - optional dependency
            self.logger.warning(
                "Unable to initialize reranker (%s). Set GEO_RAG_USE_RERANKER=0 to bypass.",
                exc,
            )
            return None
