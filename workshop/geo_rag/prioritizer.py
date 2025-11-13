from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Dict, Iterable, List, Optional

from llama_index.core.schema import NodeWithScore

from .playbook import PlaybookGuidance


@dataclass
class GeoRankedDocument:
    slug: str
    title: str
    score: float
    source_type: str
    region: Optional[str]
    province: Optional[str]
    snippet: str
    metadata: Dict


class GeoPrioritizer:
    SEO_WEIGHT = 0.45

    def __init__(self, backlink_index: Dict[str, Dict], playbook: PlaybookGuidance) -> None:
        self.backlink_index = backlink_index
        self.playbook = playbook

    def rerank(
        self,
        nodes: Iterable[NodeWithScore],
        *,
        user_region: Optional[str] = None,
        chunk_matches: Optional[Dict[str, int]] = None,
        query_text: str = "",
    ) -> List[GeoRankedDocument]:
        ranked: List[GeoRankedDocument] = []
        chunk_matches = chunk_matches or {}
        for node in nodes:
            metadata = dict(node.node.metadata)
            slug = metadata.get("slug")
            if not slug:
                continue
            title = metadata.get("title", slug)
            source_type = metadata.get("source_type", "unknown")
            region = metadata.get("region")
            province = metadata.get("province")
            snippet = node.node.get_content(metadata_mode="all")[:360]
            similarity_component = self._normalize_similarity(float(node.score))
            has_schema = bool(metadata.get("has_schema_markup"))
            num_parsed_ingredients = self._get_count(metadata, "parsed_ingredients", "parsed_ingredient_count")
            num_instruction_steps = self._get_count(metadata, "parsed_instructions", "parsed_instruction_count")
            structured_field_count = int(metadata.get("structured_field_count") or 0)
            basic_fields_meta = metadata.get("num_basic_structured_fields")
            num_basic_structured_fields = (
                int(basic_fields_meta)
                if isinstance(basic_fields_meta, (int, float))
                else max(0, structured_field_count - num_parsed_ingredients - num_instruction_steps)
            )
            ingredient_snippet_count = self._get_count(
                metadata, "ingredient_snippets", "ingredient_snippet_count"
            )
            instruction_snippet_count = self._get_count(
                metadata, "instruction_snippets", "instruction_snippet_count"
            )

            structured_score = self._structured_score(
                num_basic_structured_fields, num_parsed_ingredients, num_instruction_steps
            )
            fact_density_score = self._fact_density_score(
                ingredient_snippet_count, instruction_snippet_count
            )
            information_gain_score = self._information_gain_score(
                num_parsed_ingredients,
                num_instruction_steps,
                has_schema,
                num_basic_structured_fields,
            )
            seo_score = self._seo_component(metadata)
            tie_break_score = structured_score
            penalty = -0.05 if not has_schema else 0.0

            metadata["num_parsed_ingredients"] = num_parsed_ingredients
            metadata["num_instruction_steps"] = num_instruction_steps
            metadata["num_basic_structured_fields"] = num_basic_structured_fields
            metadata["ingredient_snippet_count"] = ingredient_snippet_count
            metadata["instruction_snippet_count"] = instruction_snippet_count

            # Scoring logic for GEO workshop: noise wins before structured extraction; structured page wins after students add ingredients and steps.
            final_score = (
                0.1 * similarity_component
                + 0.25 * structured_score
                + 0.15 * fact_density_score
                + 0.1 * information_gain_score
                + 0.45 * seo_score
                + 0.05 * tie_break_score
                - penalty
            )

            metadata["score_breakdown"] = {
                "similarity": round(0.1 * similarity_component, 6),
                "structured": round(0.25 * structured_score, 6),
                "fact_density": round(0.15 * fact_density_score, 6),
                "information_gain": round(0.1 * information_gain_score, 6),
                "seo": round(0.45 * seo_score, 6),
                "tie_break": round(0.05 * tie_break_score, 6),
                "penalty": round(penalty, 6),
                "similarity_raw": round(float(node.score), 6),
            }
            metadata["score_breakdown"]["final"] = round(final_score, 4)

            ranked.append(
                GeoRankedDocument(
                    slug=slug,
                    title=title,
                    score=final_score,
                    source_type=source_type,
                    region=region,
                    province=province,
                    snippet=snippet,
                    metadata=metadata,
                )
            )

        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked

    def _infer_query_preferences(self, query: str) -> Dict[str, float]:
        query = (query or "").lower()
        prefs: Dict[str, float] = {"article": 0.5}
        if any(keyword in query for keyword in ["recipe", "cook", "how to", "ingredient", "bake"]):
            prefs["recipe"] = 1.0
        if any(keyword in query for keyword in ["kit", "product", "buy", "price", "offer"]):
            prefs["product"] = 0.8
        return prefs

    def _normalize_similarity(self, score: float) -> float:
        return max(0.0, min(1.0, score))

    def _structured_score(
        self,
        num_basic_structured_fields: int,
        num_parsed_ingredients: int,
        num_instruction_steps: int,
    ) -> float:
        return (
            0.02 * max(0, num_basic_structured_fields)
            + 1.0 * max(0, num_parsed_ingredients)
            + 0.5 * max(0, num_instruction_steps)
        )

    def _fact_density_score(
        self,
        ingredient_snippet_count: int,
        instruction_snippet_count: int,
    ) -> float:
        return 0.3 * max(0, ingredient_snippet_count) + 0.2 * max(0, instruction_snippet_count)

    def _information_gain_score(
        self,
        num_parsed_ingredients: int,
        num_instruction_steps: int,
        has_schema: bool,
        num_basic_structured_fields: int,
    ) -> float:
        score = 0.0
        if num_parsed_ingredients > 0:
            score += 0.5
        if num_instruction_steps > 0:
            score += 0.3
        if has_schema:
            score += 0.1
        if num_basic_structured_fields > 5:
            score += 0.1
        return min(1.0, score)

    def _seo_component(self, metadata: Dict) -> float:
        authority = max(0.0, float(metadata.get("domain_authority", 0.0) or 0.0))
        backlinks = max(0.0, float(metadata.get("backlink_count", 0.0) or 0.0))
        backlink_score = max(0.0, float(metadata.get("backlink_score", 0.0) or 0.0))
        score = math.log1p(authority) * 0.35
        score += math.log1p(backlinks + 1.0) * 0.15
        score += backlink_score * 0.05
        if (metadata.get("source_type") or "").lower() == "local_site":
            score *= 1.05
        return min(1.0, score / 3.0)

    def _get_count(self, metadata: Dict, list_key: str, count_key: str) -> int:
        value: Any = metadata.get(list_key)
        if isinstance(value, list):
            return len(value)
        if isinstance(value, (int, float)):
            return max(0, int(value))
        fallback = metadata.get(count_key)
        if isinstance(fallback, list):
            return len(fallback)
        if isinstance(fallback, (int, float)):
            return max(0, int(fallback))
        return 0
