from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

SITE_ARTICLE_DIR = Path(__file__).resolve().parents[1] / "website" / "site" / "articles"
JSON_LD_PATTERN = re.compile(r"<script type='application/ld\+json'>(.*?)</script>", re.DOTALL)
_JSON_LD_CACHE: Dict[str, List[dict]] = {}


def load_json_ld(slug: str) -> List[dict]:
    slug = slug or ""
    if slug in _JSON_LD_CACHE:
        return _JSON_LD_CACHE[slug]
    path = SITE_ARTICLE_DIR / slug / "index.html"
    if not path.exists():
        _JSON_LD_CACHE[slug] = []
        return []
    try:
        html = path.read_text(encoding="utf-8")
    except OSError:
        _JSON_LD_CACHE[slug] = []
        return []
    match = JSON_LD_PATTERN.search(html)
    if not match:
        _JSON_LD_CACHE[slug] = []
        return []
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        _JSON_LD_CACHE[slug] = []
        return []
    if isinstance(payload, dict) and "@graph" in payload:
        entries = [entry for entry in payload["@graph"] if isinstance(entry, dict)]
    elif isinstance(payload, list):
        entries = [entry for entry in payload if isinstance(entry, dict)]
    elif isinstance(payload, dict):
        entries = [payload]
    else:
        entries = []
    _JSON_LD_CACHE[slug] = entries
    return entries
