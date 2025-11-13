from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence

from .config import BACKLINKS_PATH, LOCAL_CONTENT_DIR, NOISE_DIR, ROOT_DIR


@dataclass
class SourceDocument:
    doc_id: str
    text: str
    metadata: Dict[str, Any]


def _split_front_matter(raw: str) -> tuple[Dict[str, Any], str]:
    if not raw.startswith("---"):
        raise ValueError("Article missing JSON front matter")
    _, payload, body = raw.split("---", 2)
    metadata = json.loads(payload.strip())
    return metadata, body.strip()


def load_local_articles(content_dir: Path | None = None) -> List[SourceDocument]:
    content_dir = content_dir or LOCAL_CONTENT_DIR
    docs: List[SourceDocument] = []
    for path in sorted(content_dir.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        metadata, body = _split_front_matter(raw)
        slug = metadata.get("slug") or path.stem
        metadata.update(
            {
                "slug": slug,
                "source_type": "local_site",
                "region": metadata.get("region"),
                "province": metadata.get("province"),
                "path": str(path.relative_to(ROOT_DIR)),
            }
        )
        docs.append(SourceDocument(doc_id=slug, text=body, metadata=metadata))
    return docs


_NOISE_REGION_MAP = {
    "giallozafferano_tiramisu": ("Veneto", "Treviso"),
    "giallozafferano_carbonara": ("Lazio", "Roma"),
    "lacucinaitaliana_caponata": ("Sicilia", "Palermo"),
    "cookaround_pesto": ("Liguria", "Genova"),
    "salepepe_arancini": ("Sicilia", "Catania"),
}


def load_noise_documents(noise_dir: Path | None = None) -> List[SourceDocument]:
    noise_dir = noise_dir or NOISE_DIR
    docs: List[SourceDocument] = []
    for path in sorted(noise_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        domain_part, dish_part = (path.stem.split("_", 1) + [""])[:2]
        if dish_part:
            slug = f"noise-{dish_part}-{domain_part}"
        else:
            slug = f"noise-{path.stem.replace(' ', '-')}"
        region, province = _NOISE_REGION_MAP.get(path.stem, (None, None))
        lines = text.splitlines()
        domain_line = next((ln for ln in lines if ln.lower().startswith("source:")), "")
        url_line = next((ln for ln in lines if ln.lower().startswith("url:")), "")
        metadata = {
            "slug": slug,
            "title": f"Noise: {path.stem.replace('_', ' ').title()}",
            "source_type": "web_noise",
            "region": region,
            "province": province,
            "path": str(path.relative_to(ROOT_DIR)),
            "domain": domain_line.replace("Source:", "").strip() or domain_part,
            "domain_slug": domain_part,
            "source_url": url_line.replace("URL:", "").strip(),
        }
        docs.append(SourceDocument(doc_id=slug, text=text, metadata=metadata))
    return docs


def load_backlinks(backlinks_path: Path | None = None) -> List[Dict[str, Any]]:
    backlinks_path = backlinks_path or BACKLINKS_PATH
    if not backlinks_path.exists():
        return []
    data = json.loads(backlinks_path.read_text(encoding="utf-8"))
    return data


def build_backlink_index(backlinks: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for row in backlinks:
        slug = row["target_slug"]
        bucket = index.setdefault(slug, {"score": 0.0, "entries": []})
        bucket["score"] += float(row.get("authority", 0))
        bucket["entries"].append(row)
    for slug, bucket in index.items():
        count = len(bucket["entries"])
        bucket["score"] = round(bucket["score"] / max(count, 1), 4) + count * 0.05
    return index
