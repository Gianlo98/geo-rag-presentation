from __future__ import annotations

from typing import Dict, List, Sequence

from .data_sources import SourceDocument


def enrich_documents(
    documents: Sequence[SourceDocument],
    backlink_index: Dict[str, Dict],
) -> List[SourceDocument]:
    enriched: List[SourceDocument] = []
    for doc in documents:
        metadata = dict(doc.metadata)
        metadata.setdefault("title", metadata.get("slug", doc.doc_id))
        answer_assets = metadata.get("answer_assets", []) or []
        references = metadata.get("references", []) or []
        faq = metadata.get("faq", []) or []
        steps = metadata.get("steps", []) or []
        metadata["answer_asset_count"] = len(answer_assets)
        metadata["reference_count"] = len(references)
        metadata["faq_count"] = len(faq)
        metadata["steps_count"] = len(steps)
        metadata["structure_score"] = round(
            metadata["answer_asset_count"] * 0.35
            + metadata["reference_count"] * 0.15
            + metadata["faq_count"] * 0.1
            + metadata["steps_count"] * 0.05,
            4,
        )
        # TODO(workshop): Detect schema markup / llms.txt directives while parsing the site
        # and stash the signals here (e.g., metadata["has_schema_markup"] = True) so the
        # prioritizer can reward machine-readable GEO features.
        # TODO(workshop): derive a fact-density / information-gain signal (unique stats,
        # lab data, reference quality) and store it as metadata["information_gain_score"].
        slug = metadata.get("slug")
        backlink_meta = backlink_index.get(slug, {})
        metadata["backlink_score"] = backlink_meta.get("score", 0.0)
        metadata["backlink_count"] = len(backlink_meta.get("entries", []))
        metadata["source_priority"] = 1.0 if metadata.get("source_type") == "local_site" else 0.4
        doc.metadata = metadata
        enriched.append(doc)
    return enriched
