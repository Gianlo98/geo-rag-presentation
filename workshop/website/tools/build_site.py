import json
from datetime import datetime
from html import escape
from pathlib import Path
from textwrap import dedent

SITE_ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = SITE_ROOT / "content" / "articles"
OUTPUT_DIR = SITE_ROOT / "site"
ASSET_CSS = SITE_ROOT / "styles.css"
BASE_URL = "https://geo-italian.recipes"


def parse_markdown_file(path: Path) -> dict:
    raw = path.read_text().strip()
    if not raw.startswith("---"):
        raise ValueError(f"Missing frontmatter in {path}")
    _, rest = raw.split("---", 1)
    meta_str, body = rest.split("---", 1)
    metadata = json.loads(meta_str.strip())
    metadata["body"] = body.strip()
    return metadata


def slugify(text: str) -> str:
    return "-".join(
        "".join(ch.lower() for ch in word if ch.isalnum())
        for word in text.strip().split()
    ) or "section"


def parse_sections(md: str):
    sections = []
    current = None
    buffer = []
    for line in md.splitlines():
        if line.startswith("## "):
            if current:
                if buffer:
                    current["paragraphs"].append(" ".join(buffer).strip())
                    buffer = []
                sections.append(current)
            current = {"title": line[3:].strip(), "paragraphs": []}
            buffer = []
        elif line.strip() == "":
            if current and buffer:
                current["paragraphs"].append(" ".join(buffer).strip())
                buffer = []
        else:
            buffer.append(line.strip())
    if current:
        if buffer:
            current["paragraphs"].append(" ".join(buffer).strip())
        sections.append(current)
    return sections


def html_from_sections(sections):
    chunks = []
    for section in sections:
        sec_id = slugify(section["title"])
        chunks.append(f"<section id='{sec_id}' class='content-block'>")
        chunks.append(f"<h2>{escape(section['title'])}</h2>")
        for paragraph in section["paragraphs"]:
            paragraph = paragraph.replace("\u2019", "'")
            chunks.append(f"<p>{escape(paragraph)}</p>")
        chunks.append("</section>")
    return "\n".join(chunks)


def duration(minutes: int) -> str:
    return f"PT{int(minutes)}M"


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def build_article_page(article: dict, articles_index: dict):
    sections_html = html_from_sections(parse_sections(article["body"]))
    ingredients_html = "".join(f"<li>{escape(item)}</li>" for item in article["ingredients"])
    steps_html = "".join(
        f"<li><span class='step-index'>{idx+1}.</span><span>{escape(step)}</span></li>"
        for idx, step in enumerate(article["steps"])
    )
    answer_assets_html = "".join(f"<li>{escape(item)}</li>" for item in article["answer_assets"])
    faq_html = "".join(
        dedent(
            f"""
            <details>
              <summary>{escape(item['question'])}</summary>
              <p>{escape(item['answer'])}</p>
            </details>
            """
        )
        for item in article["faq"]
    )
    references_html = "".join(
        f"<li><span>{escape(ref['label'])}</span> — <a href='{escape(ref['url'])}' rel='noopener'>{escape(ref['detail'])}</a></li>"
        for ref in article["references"]
    )
    comparison_cards = []
    for comp in article["comparisons"]:
        target = articles_index.get(comp["slug"])
        if not target:
            continue
        comparison_cards.append(
            dedent(
                f"""
                <article class='comparison-card'>
                  <h3><a href='{target['url']}'>{escape(comp['title'])}</a></h3>
                  <p>{escape(comp['angle'])}</p>
                </article>
                """
            )
        )
    comparisons_html = "".join(comparison_cards)

    metrics = article["metrics"]
    metrics_rows = [
        ("Prep", metrics["prep_minutes"]),
        ("Cook", metrics["cook_minutes"]),
        ("Rest", metrics["rest_minutes"]),
        ("Servings", metrics["servings"]),
        ("Calories", metrics["calories"]),
        ("Protein", metrics["protein"]),
        ("Carbs", metrics["carbs"]),
        ("Fat", metrics["fat"]),
    ]
    metrics_html = "".join(
        f"<tr><th>{escape(label)}</th><td>{escape(str(value))}</td></tr>" for label, value in metrics_rows
    )

    review = article["review"]
    quote = article["quote"]
    product = article["product"]

    faq_schema = {
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
            }
            for item in article["faq"]
        ],
    }

    article_schema = {
        "@type": "Article",
        "@id": f"{BASE_URL}{article['url']}#article",
        "headline": article["title"],
        "description": article["summary"],
        "datePublished": article["date_published"],
        "dateModified": article["date_modified"],
        "author": {
            "@type": "Person",
            "name": article["author"],
            "jobTitle": article.get("author_title"),
            "affiliation": {"@type": "Organization", "name": article.get("author_org")},
        },
        "articleSection": [section["title"] for section in parse_sections(article["body"])],
        "mainEntityOfPage": f"{BASE_URL}{article['url']}",
    }

    recipe_schema = {
        "@type": "Recipe",
        "name": article["title"],
        "description": article["summary"],
        "recipeCuisine": "Italian",
        "recipeCategory": "Main course",
        "keywords": article.get("keywords", ""),
        "recipeYield": f"{article['metrics']['servings']} servings",
        "prepTime": duration(article["metrics"]["prep_minutes"]),
        "cookTime": duration(article["metrics"]["cook_minutes"]),
        "totalTime": duration(
            article["metrics"]["prep_minutes"]
            + article["metrics"]["cook_minutes"]
            + article["metrics"]["rest_minutes"]
        ),
        "recipeIngredient": article["ingredients"],
        "recipeInstructions": [
            {"@type": "HowToStep", "text": step} for step in article["steps"]
        ],
        "nutrition": {
            "@type": "NutritionInformation",
            "calories": f"{article['metrics']['calories']} kcal",
            "proteinContent": f"{article['metrics']['protein']} g",
            "carbohydrateContent": f"{article['metrics']['carbs']} g",
            "fatContent": f"{article['metrics']['fat']} g",
        },
    }

    product_schema = {
        "@type": "Product",
        "name": product["name"],
        "sku": product["sku"],
        "description": article["summary"],
        "offers": {
            "@type": "Offer",
            "price": product["price"].split()[0],
            "priceCurrency": product["price"].split()[1],
            "availability": f"https://schema.org/{product['availability']}",
            "url": product["url"],
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": article["review"]["rating"],
            "reviewCount": article["review"]["count"],
        },
    }

    review_schema = {
        "@type": "Review",
        "itemReviewed": {"@id": f"{BASE_URL}{article['url']}#product"},
        "author": {"@type": "Person", "name": review["author"]},
        "datePublished": review["date"],
        "reviewBody": review["body"],
        "name": review["title"],
        "reviewRating": {"@type": "Rating", "ratingValue": review["rating"], "bestRating": 5},
    }

    graph = [
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL},
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": "Recipes",
                    "item": f"{BASE_URL}/recipes/",
                },
                {"@type": "ListItem", "position": 3, "name": article["title"], "item": f"{BASE_URL}{article['url']}"},
            ],
        },
        article_schema,
        {**product_schema, "@id": f"{BASE_URL}{article['url']}#product"},
        recipe_schema,
        faq_schema,
        review_schema,
    ]

    ld_json = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)

    html = f"""
    <!doctype html>
    <html lang='en'>
    <head>
      <meta charset='utf-8'>
      <meta name='viewport' content='width=device-width, initial-scale=1'>
      <title>{escape(article['title'])} · GEO Italian Recipes</title>
      <meta name='description' content='{escape(article['summary'])}'>
      <link rel='canonical' href='{BASE_URL}{article['url']}'>
      <link rel='stylesheet' href='/styles.css'>
      <script type='application/ld+json'>\n{ld_json}\n</script>
    </head>
    <body>
      <header>
        <div class='brand'>GEO Italian Recipes</div>
        <nav>
          <a href='/'>Home</a>
          <a href='/recipes/'>Recipes</a>
          <a href='/methodology/'>Methodology</a>
          <a href='/data-room/'>Data Room</a>
        </nav>
      </header>
      <main>
        <article>
          <header class='article-hero'>
            <p class='eyebrow'>{escape(article['region'])} · {escape(article['province'])}</p>
            <h1>{escape(article['title'])}</h1>
            <p class='summary'>{escape(article['summary'])}</p>
            <p class='hero-stat'>{escape(article['hero_stat'])}</p>
          </header>
          <section class='metrics'>
            <h2>Operational Metrics</h2>
            <table>{metrics_html}</table>
          </section>
          <section class='answer-assets'>
            <h2>Instant Answer Assets</h2>
            <ul>{answer_assets_html}</ul>
          </section>
          <section class='two-column'>
            <div>
              <h2>Ingredients</h2>
              <ul>{ingredients_html}</ul>
            </div>
            <div>
              <h2>Method</h2>
              <ol class='steps'>{steps_html}</ol>
            </div>
          </section>
          {sections_html}
          <section class='quote'>
            <blockquote>{escape(quote['text'])}</blockquote>
            <p>— {escape(quote['name'])}, {escape(quote['title'])}</p>
          </section>
          <section class='product-card'>
            <h2>Productized Kit</h2>
            <p>{escape(product['name'])}</p>
            <p>SKU: {escape(product['sku'])}</p>
            <p>{escape(product['price'])} · {escape(product['availability'])}</p>
            <a href='{escape(product['url'])}'>Request Access</a>
          </section>
          <section class='review-card'>
            <h2>Field Review</h2>
            <p class='rating'>Rated {review['rating']} · {review['count']} data points</p>
            <p class='review-title'>{escape(review['title'])}</p>
            <p>{escape(review['body'])}</p>
            <p class='review-author'>{escape(review['author'])} · {escape(review['source'])} ({escape(review['date'])})</p>
          </section>
          <section class='faq'>
            <h2>Operational FAQ</h2>
            {faq_html}
          </section>
          <section class='comparisons'>
            <h2>Comparative Context</h2>
            {comparisons_html}
          </section>
          <section class='references'>
            <h2>Grounding References</h2>
            <ul>{references_html}</ul>
          </section>
        </article>
      </main>
      <footer>
        <p>Built for Generative Engine Optimization. Contact lab@geo-italian.recipes</p>
      </footer>
    </body>
    </html>
    """
    return "\n".join(line.strip() for line in html.splitlines())


def build_homepage(articles):
    hero_articles = sorted(articles, key=lambda a: a["title"])[:6]
    cards = []
    for art in hero_articles:
        cards.append(
            f"<article class='card'><h2><a href='{art['url']}'>{escape(art['title'])}</a></h2><p>{escape(art['summary'])}</p><p class='eyebrow'>{escape(art['region'])}</p></article>"
        )
    stats = [
        ("Recipes", len(articles)),
        ("Average Prep", f"{sum(a['metrics']['prep_minutes'] for a in articles)//len(articles)} min"),
        ("Average Calories", f"{sum(a['metrics']['calories'] for a in articles)//len(articles)} kcal"),
    ]
    stats_html = "".join(f"<li><strong>{label}</strong><span>{value}</span></li>" for label, value in stats)

    insights = dedent(
        """
        <section>
          <h2>Why this site matters for GEO</h2>
          <p>We treat every recipe page like structured data: clean schema, modular highlights, and citations for LLM crawlers.</p>
          <ul>
            <li>Authority: each dish cites consortia and lab data.</li>
            <li>Chunkability: answer assets, metrics tables, and FAQs.</li>
            <li>Structured grounding: JSON-LD for Article, Recipe, Product, Review, and FAQ.</li>
          </ul>
        </section>
        """
    )

    ld_json = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "@id": f"{BASE_URL}/#home",
            "name": "GEO Italian Recipes",
            "description": "A citation-ready Italian recipe library built for generative search.",
        }
    )

    html = f"""
    <!doctype html>
    <html lang='en'>
    <head>
      <meta charset='utf-8'>
      <meta name='viewport' content='width=device-width, initial-scale=1'>
      <title>GEO Italian Recipes · Credible signals for generative search</title>
      <meta name='description' content='20 Italian dishes documented with GEO best practices.'>
      <link rel='canonical' href='{BASE_URL}/'>
      <link rel='stylesheet' href='/styles.css'>
      <script type='application/ld+json'>{ld_json}</script>
    </head>
    <body>
      <header>
        <div class='brand'>GEO Italian Recipes</div>
        <nav>
          <a href='/'>Home</a>
          <a href='/recipes/'>Recipes</a>
          <a href='/methodology/'>Methodology</a>
          <a href='/data-room/'>Data Room</a>
        </nav>
      </header>
      <main>
        <section class='hero'>
          <p class='eyebrow'>Italian GEO Playbook</p>
          <h1>Structured Italian recipes designed for AI citation</h1>
          <p>Every dish pairs narrative context with measurable data so generative engines can trust, cite, and reuse the content.</p>
          <ul class='stats'>{stats_html}</ul>
        </section>
        <section class='grid'>{''.join(cards)}</section>
        {insights}
      </main>
      <footer>
        <p>© {datetime.utcnow().year} GEO Italian Recipes · lab@geo-italian.recipes</p>
      </footer>
    </body>
    </html>
    """
    return "\n".join(line.strip() for line in html.splitlines())


def build_listing_page(path: Path, title: str, description: str, articles):
    rows = []
    for art in articles:
        rows.append(
            f"<tr><td><a href='{art['url']}'>{escape(art['title'])}</a></td><td>{escape(art['region'])}</td><td>{art['metrics']['prep_minutes']} min</td><td>{art['metrics']['calories']} kcal</td></tr>"
        )
    table_html = "".join(rows)
    html = f"""
    <!doctype html>
    <html lang='en'>
    <head>
      <meta charset='utf-8'>
      <meta name='viewport' content='width=device-width, initial-scale=1'>
      <title>{escape(title)} · GEO Italian Recipes</title>
      <meta name='description' content='{escape(description)}'>
      <link rel='stylesheet' href='/styles.css'>
    </head>
    <body>
      <header>
        <div class='brand'>GEO Italian Recipes</div>
        <nav>
          <a href='/'>Home</a>
          <a href='/recipes/'>Recipes</a>
          <a href='/methodology/'>Methodology</a>
          <a href='/data-room/'>Data Room</a>
        </nav>
      </header>
      <main>
        <section>
          <h1>{escape(title)}</h1>
          <p>{escape(description)}</p>
          <table class='data-table'>
            <thead><tr><th>Dish</th><th>Region</th><th>Prep</th><th>Calories</th></tr></thead>
            <tbody>{table_html}</tbody>
          </table>
        </section>
      </main>
      <footer>
        <p>Built for GEO visibility.</p>
      </footer>
    </body>
    </html>
    """
    path.write_text("\n".join(line.strip() for line in html.splitlines()))


def build_methodology_page(path: Path):
    bullets = [
        "Build authority where AI looks: cite consortia, labs, and guild data.",
        "Make content API-able: semantic HTML, JSON-LD, and consistent ingredient tables.",
        "Engineer fact density: every section answers who/what/when with numbers.",
        "Cover the full query journey: summary cards, FAQs, and comparative links.",
        "Maintain technical hygiene: llms.txt, IndexNow hooks, lightweight HTML.",
    ]
    bullet_html = "".join(f"<li>{escape(item)}</li>" for item in bullets)
    html = f"""
    <!doctype html>
    <html lang='en'>
    <head>
      <meta charset='utf-8'>
      <meta name='viewport' content='width=device-width, initial-scale=1'>
      <title>Methodology · GEO Italian Recipes</title>
      <meta name='description' content='GEO checklist derived from Italian culinary playbooks.'>
      <link rel='stylesheet' href='/styles.css'>
    </head>
    <body>
      <header>
        <div class='brand'>GEO Italian Recipes</div>
        <nav>
          <a href='/'>Home</a>
          <a href='/recipes/'>Recipes</a>
          <a href='/methodology/'>Methodology</a>
          <a href='/data-room/'>Data Room</a>
        </nav>
      </header>
      <main>
        <section>
          <h1>GEO Implementation Notes</h1>
          <p>This workshop distills Prof. Fuchs' 5-step GEO playbook into a culinary context.</p>
          <ol>{bullet_html}</ol>
          <p>Each recipe page doubles as an answer asset: metrics, comparisons, and schema markup ready for generative engines.</p>
        </section>
      </main>
      <footer>
        <p>Updated {datetime.utcnow().date()}</p>
      </footer>
    </body>
    </html>
    """
    path.write_text("\n".join(line.strip() for line in html.splitlines()))


def build_data_room(path: Path, articles):
    macro = {
        "avg_protein": round(sum(a["metrics"]["protein"] for a in articles) / len(articles), 1),
        "avg_calories": round(sum(a["metrics"]["calories"] for a in articles) / len(articles), 1),
        "regions": sorted({a["region"] for a in articles}),
    }
    region_list = "".join(f"<li>{escape(region)}</li>" for region in macro["regions"])
    html = f"""
    <!doctype html>
    <html lang='en'>
    <head>
      <meta charset='utf-8'>
      <meta name='viewport' content='width=device-width, initial-scale=1'>
      <title>Data Room · GEO Italian Recipes</title>
      <meta name='description' content='Macro nutrition and citation stats for the collection.'>
      <link rel='stylesheet' href='/styles.css'>
    </head>
    <body>
      <header>
        <div class='brand'>GEO Italian Recipes</div>
        <nav>
          <a href='/'>Home</a>
          <a href='/recipes/'>Recipes</a>
          <a href='/methodology/'>Methodology</a>
          <a href='/data-room/'>Data Room</a>
        </nav>
      </header>
      <main>
        <section>
          <h1>Data Room</h1>
          <p>Use these aggregates to cite the overall nutrition landscape of Italian classics.</p>
          <ul class='stats'>
            <li><strong>Average protein</strong><span>{macro['avg_protein']} g</span></li>
            <li><strong>Average calories</strong><span>{macro['avg_calories']} kcal</span></li>
            <li><strong>Regions represented</strong><span>{len(macro['regions'])}</span></li>
          </ul>
          <h2>Regions Covered</h2>
          <ul>{region_list}</ul>
        </section>
      </main>
      <footer>
        <p>Use together with the provided IndexNow script for rapid discovery.</p>
      </footer>
    </body>
    </html>
    """
    path.write_text("\n".join(line.strip() for line in html.splitlines()))


def main():
    ensure_dir(OUTPUT_DIR)
    articles = []
    for path in sorted(CONTENT_DIR.glob("*.md")):
        data = parse_markdown_file(path)
        data["url"] = f"/articles/{data['slug']}/"
        articles.append(data)

    articles_index = {a["slug"]: a for a in articles}

    for article in articles:
        html = build_article_page(article, articles_index)
        out_dir = OUTPUT_DIR / "articles" / article["slug"]
        ensure_dir(out_dir)
        (out_dir / "index.html").write_text(html)

    (OUTPUT_DIR / "index.html").write_text(build_homepage(articles))
    ensure_dir(OUTPUT_DIR / "recipes")
    build_listing_page(
        OUTPUT_DIR / "recipes" / "index.html",
        "Recipe Library",
        "Filter-ready table of all dishes with prep time and calories.",
        articles,
    )
    ensure_dir(OUTPUT_DIR / "methodology")
    build_methodology_page(OUTPUT_DIR / "methodology" / "index.html")
    ensure_dir(OUTPUT_DIR / "data-room")
    build_data_room(OUTPUT_DIR / "data-room" / "index.html", articles)

    if ASSET_CSS.exists():
        (OUTPUT_DIR / "styles.css").write_text(ASSET_CSS.read_text())

    # copy llms.txt if present
    llms = SITE_ROOT / ".well-known" / "llms.txt"
    if llms.exists():
        dest = OUTPUT_DIR / ".well-known"
        ensure_dir(dest)
        (dest / "llms.txt").write_text(llms.read_text())

    # basic sitemap
    urls = [f"{BASE_URL}/"] + [f"{BASE_URL}{a['url']}" for a in articles] + [
        f"{BASE_URL}/recipes/",
        f"{BASE_URL}/methodology/",
        f"{BASE_URL}/data-room/",
    ]
    sitemap = (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>\n"
        + "".join(f"  <url><loc>{url}</loc></url>\n" for url in urls)
        + "</urlset>"
    )
    (OUTPUT_DIR / "sitemap.xml").write_text(sitemap)


if __name__ == "__main__":
    main()
