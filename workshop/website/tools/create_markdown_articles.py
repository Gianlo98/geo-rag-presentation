import json
from pathlib import Path

from recipe_dataset import RECIPES

SITE_ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = SITE_ROOT / 'content' / 'articles'


def write_article(data):
    metadata = {
        "title": data["title"],
        "slug": data["slug"],
        "summary": data["summary"],
        "region": data["region"],
        "province": data["province"],
        "origin_year": data["origin_year"],
        "author": data.get("author", "Dr. Lucia Ferrante"),
        "author_title": data.get("author_title", "Culinary Research Director"),
        "author_org": data.get("author_org", "Osservatorio Gastronomico Italiano"),
        "date_published": data.get("date_published", "2025-10-10"),
        "date_modified": data.get("date_modified", "2025-10-10"),
        "tags": data.get("tags", []),
        "keywords": data.get("keywords", ""),
        "hero_stat": data["hero_stat"],
        "metrics": data["metrics"],
        "ingredients": data["ingredients"],
        "steps": data["steps"],
        "answer_assets": data["answer_assets"],
        "faq": data["faq"],
        "comparisons": data["comparisons"],
        "references": data["references"],
        "product": data["product"],
        "review": data["review"],
        "quote": data["quote"],
    }

    body_sections = []
    for heading, paragraphs in data["narratives"].items():
        body_sections.append(f"## {heading}\n")
        body_sections.append("\n\n".join(paragraphs))
        body_sections.append("")

    content = f"---\n{json.dumps(metadata, indent=2)}\n---\n" + "\n".join(body_sections).strip() + "\n"

    path = CONTENT_DIR / f"{data['slug']}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def main():
    if not RECIPES:
        raise SystemExit("RECIPES is empty. Populate recipe_dataset.RECIPES before running.")
    for recipe in RECIPES:
        write_article(recipe)


if __name__ == '__main__':
    main()
