from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import PLAYBOOK_PATH


@dataclass
class PlaybookGuidance:
    authority_weight: float
    structure_weight: float
    answer_asset_weight: float
    reference_weight: float
    local_weight: float
    raw_text: str

    @classmethod
    def from_file(cls, path: Path | None = None) -> "PlaybookGuidance":
        path = path or PLAYBOOK_PATH
        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
        lower = text.lower()
        authority_weight = 0.35 if "verifiable authority" in lower or "e-e-a-t" in lower else 0.2
        structure_weight = 0.25 if "structure their content for extraction" in lower else 0.15
        answer_asset_weight = 0.2 if "answer assets" in lower else 0.1
        reference_weight = 0.18 if "cite" in lower or "references" in lower else 0.1
        local_mentions = lower.count("local")
        local_weight = min(0.25, 0.05 * local_mentions)
        return cls(
            authority_weight=authority_weight,
            structure_weight=structure_weight,
            answer_asset_weight=answer_asset_weight,
            reference_weight=reference_weight,
            local_weight=local_weight,
            raw_text=text,
        )

    def score(self, metadata: dict) -> float:
        score = 0.0
        backlinks = float(metadata.get("backlink_score", 0))
        structure = float(metadata.get("structure_score", 0))
        answer_assets = int(metadata.get("answer_asset_count", 0))
        references = int(metadata.get("reference_count", 0))
        score += backlinks * self.authority_weight
        score += structure * self.structure_weight
        score += answer_assets * self.answer_asset_weight * 0.1
        score += references * self.reference_weight * 0.05
        if metadata.get("source_type") == "local_site":
            score += self.local_weight
        return score
