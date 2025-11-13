from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from llama_index.core.schema import TextNode
from tqdm import tqdm

from geo_rag.pipeline import GeoRAGPipeline, PipelineConfig
from solution import process_node

_PIPELINE: Optional[GeoRAGPipeline] = None
ROOT_DIR = Path(__file__).resolve().parents[1]
KNOWLEDGE_GRAPH_PATH = ROOT_DIR / "output" / "knowledge_graph.html"

# Authority/backlink baselines keep external sources ahead until structured signals close the gap.
LOCAL_BACKLINK_COUNT = 8
LOCAL_DOMAIN_AUTHORITY = 18.0
EXTERNAL_BACKLINK_COUNT = 240
EXTERNAL_DOMAIN_AUTHORITY = 82.0


def load_data(
    *,
    db_url: Optional[str] = None,
    use_cache: bool = True,
    refresh_cache: bool = False,
    reset_table: bool = True,
    process_filter: Optional[str] = None,
    process_documents: bool = True,
) -> GeoRAGPipeline:
    global _PIPELINE
    config = PipelineConfig(
        db_url=db_url or PipelineConfig().db_url,
        use_cache=use_cache,
        refresh_cache=refresh_cache,
        reset_table=reset_table,
    )
    pipeline = GeoRAGPipeline(config)

    if not process_documents:
        print("[workflow] Attaching existing vector store...")
        pipeline.attach_existing_vector_store()
        _PIPELINE = pipeline
        return pipeline

    print("[workflow] Loading pipeline...")
    pipeline.load()
    print(f"[workflow] Loaded {len(pipeline._nodes)} base chunks")

    if process_filter:
        filter_lower = process_filter.lower()
        filtered_nodes = [
            node
            for node in pipeline._nodes
            if filter_lower in (node.metadata.get("slug", "").lower())
        ]
        print(
            f"[workflow] Applying filter '{process_filter}' -> {len(filtered_nodes)} chunks"
        )
        pipeline._nodes = filtered_nodes

    extra_nodes: List[TextNode] = []
    for node in tqdm(pipeline._nodes, desc="Processing nodes"):
        extra_nodes.extend(process_node(node, pipeline))
    if extra_nodes:
        print(f"[workflow] Generated {len(extra_nodes)} structured chunks")
        _embed_extra_nodes(pipeline, extra_nodes)
        pipeline._nodes.extend(extra_nodes)

    _apply_backlink_authority_baselines(pipeline._nodes)

    _rebuild_vector_store_with_existing_embeddings(pipeline)
    print("[workflow] Rebuilt vector store with enriched metadata")
    export_knowledge_graph(pipeline)
    print("[workflow] Knowledge graph exported")
    _PIPELINE = pipeline
    return pipeline


def query(question: str, *, user_region: Optional[str] = None, top_n: int = 3) -> List[Dict[str, Any]]:
    if _PIPELINE is None:
        raise RuntimeError("Pipeline not loaded. Call load_data() first.")
    results = _PIPELINE.query(question, user_region=user_region)
    serialized: List[Dict[str, Any]] = []
    for doc in results[:top_n]:
        serialized.append(
            {
                "slug": doc.slug,
                "title": doc.title,
                "score": round(doc.score, 4),
                "region": doc.region,
                "province": doc.province,
                "source_type": doc.source_type,
                "snippet": doc.snippet,
                "metadata": doc.metadata,
            }
        )
    return serialized


def get_pipeline() -> Optional[GeoRAGPipeline]:
    return _PIPELINE


def _apply_backlink_authority_baselines(nodes: List[TextNode]) -> None:
    for node in nodes:
        metadata = node.metadata
        source_type = (metadata.get("source_type") or "").lower()
        if source_type == "local_site":
            metadata["backlink_count"] = LOCAL_BACKLINK_COUNT
            metadata["domain_authority"] = LOCAL_DOMAIN_AUTHORITY
        else:
            metadata["backlink_count"] = EXTERNAL_BACKLINK_COUNT
            metadata["domain_authority"] = EXTERNAL_DOMAIN_AUTHORITY
        _annotate_structured_signals(metadata)


def _annotate_structured_signals(metadata: Dict[str, Any]) -> None:
    def _resolve_count(obj: Any, fallback: Any = 0) -> int:
        if isinstance(obj, list):
            return len(obj)
        if isinstance(obj, (int, float)):
            return max(0, int(obj))
        if isinstance(fallback, (int, float)):
            return max(0, int(fallback))
        if isinstance(fallback, list):
            return len(fallback)
        return 0
    microdata = metadata.get("microdata") or {}
    ingredients = metadata.get("ingredients") or microdata.get("recipeIngredient") or []
    steps = metadata.get("steps") or microdata.get("recipeInstructions") or []
    faq = metadata.get("faq") or []
    metrics = metadata.get("metrics") or microdata.get("metrics") or {}
    nutrition = metadata.get("nutrition") or microdata.get("nutrition") or {}
    comparisons = metadata.get("comparisons") or []
    answer_assets = metadata.get("answer_assets") or []
    references = metadata.get("references") or []
    linked_slugs = metadata.get("linked_slugs") or []

    ingredient_count = len(ingredients) if isinstance(ingredients, list) else 0
    instruction_count = len(steps) if isinstance(steps, list) else 0
    faq_count = len(faq)
    metric_count = len(metrics) if isinstance(metrics, dict) else 0
    nutrition_fields = len(nutrition) if isinstance(nutrition, dict) else 0

    metadata["ingredient_count"] = ingredient_count
    metadata["instruction_count"] = instruction_count
    metadata["faq_count"] = max(metadata.get("faq_count", faq_count), faq_count)
    metadata["metric_count"] = metric_count

    structured_types = metadata.get("structured_types") or []
    structured_field_count = (
        len(structured_types)
        + (1 if metadata.get("has_schema_markup") else 0)
        + (1 if metadata.get("microdata") else 0)
        + (1 if metrics else 0)
        + (1 if nutrition else 0)
        + (1 if ingredient_count else 0)
        + (1 if instruction_count else 0)
        + len(answer_assets)
        + len(references)
        + len(linked_slugs)
        + len(comparisons)
        + (1 if metadata.get("hero_stat") else 0)
        + (1 if metadata.get("product") else 0)
        + (1 if metadata.get("review") else 0)
    )
    metadata["structured_field_count"] = structured_field_count

    parsed_ingredients = metadata.get("parsed_ingredients")
    parsed_instructions = metadata.get("parsed_instructions")
    num_parsed_ingredients = _resolve_count(parsed_ingredients, metadata.get("parsed_ingredient_count", 0))
    num_instruction_steps = _resolve_count(parsed_instructions, metadata.get("parsed_instruction_count", 0))
    num_basic_structured_fields = max(0, structured_field_count - num_parsed_ingredients - num_instruction_steps)
    metadata["num_parsed_ingredients"] = num_parsed_ingredients
    metadata["num_instruction_steps"] = num_instruction_steps
    metadata["num_basic_structured_fields"] = num_basic_structured_fields

    ingredient_snippet_count = _resolve_count(
        metadata.get("ingredient_snippets"), metadata.get("ingredient_snippet_count", 0)
    )
    instruction_snippet_count = _resolve_count(
        metadata.get("instruction_snippets"), metadata.get("instruction_snippet_count", 0)
    )
    metadata["ingredient_snippet_count"] = ingredient_snippet_count
    metadata["instruction_snippet_count"] = instruction_snippet_count

    fact_density = ingredient_snippet_count * 0.3 + instruction_snippet_count * 0.2
    metadata["fact_density_signal"] = round(fact_density, 3)

    has_schema = bool(metadata.get("has_schema_markup"))
    info_gain = 0.0
    if num_parsed_ingredients > 0:
        info_gain += 0.5
    if num_instruction_steps > 0:
        info_gain += 0.3
    if has_schema:
        info_gain += 0.1
    if num_basic_structured_fields > 5:
        info_gain += 0.1
    metadata["information_gain_score"] = round(min(1.0, info_gain), 3)


def _rebuild_vector_store_with_existing_embeddings(pipeline: GeoRAGPipeline) -> None:
    embeddings: List[List[float]] = []
    for node in pipeline._nodes:
        if node.embedding is None:
            raise RuntimeError("Node missing embedding; reload with refresh_cache=True")
        embeddings.append(node.embedding)
    pipeline._bootstrap_vector_store(pipeline._nodes, embeddings)


def _embed_extra_nodes(pipeline: GeoRAGPipeline, nodes: List[TextNode]) -> None:
    if not nodes:
        return
    chunk_size = 64
    batch_iter = tqdm(
        range(0, len(nodes), chunk_size),
        desc="Embedding extra nodes",
        total=(len(nodes) + chunk_size - 1) // chunk_size,
    )
    for idx in batch_iter:
        batch = nodes[idx : idx + chunk_size]
        texts = [node.text for node in batch]
        embeddings = pipeline.embed_model.get_text_embedding_batch(texts)
        for node_obj, embedding in zip(batch, embeddings):
            node_obj.embedding = embedding


def export_knowledge_graph(pipeline: GeoRAGPipeline) -> None:
    nodes = []
    edges = []
    seen = set()
    for node in pipeline._nodes:
        slug = node.metadata.get("slug")
        if node.metadata.get("chunk_type") != "full" or slug in seen:
            continue
        seen.add(slug)
        nodes.append(
            {
                "slug": slug,
                "title": node.metadata.get("title", slug),
                "structured": node.metadata.get("structured_types", []),
                "has_schema": node.metadata.get("has_schema_markup", False),
                "structured_fields": node.metadata.get("structured_field_count", 0),
                "parsed_ingredients": node.metadata.get("num_parsed_ingredients", node.metadata.get("parsed_ingredient_count", 0)),
                "instruction_steps": node.metadata.get("num_instruction_steps", node.metadata.get("parsed_instruction_count", 0)),
                "ingredient_snippets": node.metadata.get("ingredient_snippet_count", 0),
                "instruction_snippets": node.metadata.get("instruction_snippet_count", 0),
                "info_gain": node.metadata.get("information_gain_score", 0.0),
                "fact_density": node.metadata.get("fact_density_signal", 0.0),
                "backlinks": node.metadata.get("backlink_count", 0),
                "authority": node.metadata.get("domain_authority", 0.0),
                "source_type": node.metadata.get("source_type"),
            }
        )
        for ref in node.metadata.get("linked_slugs", []) or []:
            edges.append((slug, ref))

    html = [
        "<html><head><title>GEO Knowledge Graph</title>",
        "<style>body{font-family:Arial, sans-serif;} table{border-collapse:collapse;} th,td{border:1px solid #ddd;padding:4px;} </style>",
        "</head><body>",
        "<h1>GEO Knowledge Graph</h1>",
        "<p>Each node represents a document with structured signals and authority.</p>",
        "<h2>Nodes</h2>",
        "<table><tr><th>Slug</th><th>Source</th><th>Structured Types</th><th>Schema</th><th>Structured Fields</th><th>Parsed Ingredients</th><th>Instruction Steps</th><th>Ingredient Snips</th><th>Instruction Snips</th><th>Info Gain</th><th>Fact Density</th><th>Backlinks</th><th>Authority</th></tr>",
    ]
    for node in nodes:
        html.append(
            f"<tr><td>{node['slug']}</td><td>{node['source_type']}</td><td>{', '.join(node['structured']) or '-'}" \
            f"</td><td>{'yes' if node['has_schema'] else 'no'}</td><td>{node.get('structured_fields', 0)}</td>" \
            f"<td>{node.get('parsed_ingredients', 0)}</td><td>{node.get('instruction_steps', 0)}</td>" \
            f"<td>{node.get('ingredient_snippets', 0)}</td><td>{node.get('instruction_snippets', 0)}</td>" \
            f"<td>{node['info_gain']}</td><td>{node.get('fact_density', 0)}</td><td>{node['backlinks']}</td><td>{node['authority']}</td></tr>"
        )
    html.append("</table>")
    html.append("<h2>Entity Links</h2>")
    if edges:
        html.append("<ul>")
        for src, dst in edges:
            html.append(f"<li><strong>{src}</strong> references <strong>{dst}</strong></li>")
        html.append("</ul>")
    else:
        html.append("<p>No inter-article links detected.</p>")

    html.append("</body></html>")
    KNOWLEDGE_GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_GRAPH_PATH.write_text("\n".join(html), encoding="utf-8")


def __main__() -> None:
    load_data(
        db_url=None,
        use_cache=True,
        refresh_cache=False,
        reset_table=False,
        process_filter=None,
        process_documents=True,
    )
