#!/usr/bin/env python3
"""Fetch noisy Italian recipe data for the workshop."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from geo_rag.config import NOISE_DIR

DOMAIN_AUTHORITY = {
    "giallozafferano.com": 92,
    "cookingitalians.com": 75,
	"easyworldrecipes.com": 68,
	"vincenzosplate.com": 70,
	"anitalianinmykitchen.com": 65,
	"themediterraneandish.com": 80,
	"mangiawithnonna.com": 60,
	"recipesfromitaly.com": 72,
	"italianrecipebook.com": 66,
	"piattorecipes.com": 67,
	"recipesown.com": 65
}

TARGETS = {
    "giallozafferano_tiramisu": "https://ricette.giallozafferano.it/Tiramisu.html",
    "giallozafferano_tiramisu_fragola": "https://ricette.giallozafferano.it/Tiramisu-alle-fragole.html",
    "giallozafferano_tiramisu_senza_uova": "https://ricette.giallozafferano.it/Tiramisu-senza-uova.html",
    "giallozafferano_tiramisu_pistacchio": "https://ricette.giallozafferano.it/Tiramisu-al-pistacchio.html",
    "giallozafferano_tiramisu_uova_pastorizzate": "https://ricette.giallozafferano.it/Tiramisu-con-uova-pastorizzate.html",
    "giallozafferano_tiramisu_limone": "https://ricette.giallozafferano.it/Tiramisu-al-limone.html",
    "giallozafferano_tiramisu_nutella": "https://ricette.giallozafferano.it/Tiramisu-alla-Nutella.html",
    "giallozafferano_tiramisu_allo_zafferano": "https://ricette.giallozafferano.it/Tiramisu-allo-zafferano.html",
    "giallozafferano_arancini-siciliani": "https://ricette.giallozafferano.it/Arancini-di-riso.html",
    "giallozafferano_bistecca-fiorentina": "https://ricette.giallozafferano.it/Bistecca-alla-fiorentina.html",
    "giallozafferano_cacio-e-pepe": "https://ricette.giallozafferano.it/Spaghetti-Cacio-e-Pepe.html",
    "giallozafferano_cannoli-siciliani": "https://ricette.giallozafferano.it/Cannoli-siciliani.html",
    "giallozafferano_focaccia-ligure": "https://ricette.giallozafferano.it/Focaccia-fugassa-alla-genovese.html",
    "giallozafferano_gelato-fiorentino": "https://blog.giallozafferano.it/cookingpam/ricetta-gelato-alla-crema-fiorentina",
    "giallozafferano_gnocchi-di-patate": "https://ricette.giallozafferano.it/Gnocchi-di-patate.html",
    "giallozafferano_insalata-caprese": "https://blog.giallozafferano.it/lebistro/insalata-caprese",
    "giallozafferano_lasagna-bolognese": "https://ricette.giallozafferano.it/Lasagne-alla-Bolognese.html",
    "giallozafferano_minestrone-genovese": "https://ricette.giallozafferano.it/Minestrone-alla-genovese.html",
    "giallozafferano_osso-buco": "https://ricette.giallozafferano.it/Ossibuchi-alla-milanese.html",
    "giallozafferano_panettone-milanese": "https://ricette.giallozafferano.it/Panettone.html",
    "giallozafferano_pesto-alla-genovese": "https://ricette.giallozafferano.it/Pesto-alla-genovese.html",
    "giallozafferano_pizza-margherita": "https://ricette.giallozafferano.it/Pizza-Margherita.html",
    "giallozafferano_polenta-bergamasca": "https://ricette.giallozafferano.it/Polenta.html",
    "gialloz­afferano_ravioli-ricotta-spinaci": "https://ricette.giallozafferano.it/Ravioli-ricotta-e-spinaci.html",
    "giallozafferano_risotto-alla-milanese": "https://ricette.giallozafferano.it/Risotto-alla-milanese.html",
    "giallozafferano_saltimbocca-romana": "https://ricette.giallozafferano.it/Saltimbocca-alla-Romana.html",
    "giallozafferano_spaghetti-carbonara": "https://ricette.giallozafferano.it/Spaghetti-alla-carbonara.html",
    "giallozafferano_tiramisu-treviso": "https://ricette.giallozafferano.it/Tiramisu.html",
    "anitalianinmykitchen_cacio-e-pepe": "https://anitalianinmykitchen.com/authentic-cacio-e-pepe/",  
    "italianrecipebook_insalata-caprese": "https://www.italianrecipebook.com/caprese-salad/",  
    "piattorecipes_insalata-caprese": "https://www.piattorecipes.com/authentic-italian-caprese-salad-recipe/",  
    "recipesown_insalata-caprese": "https://recipesown.com/caprese-salad-a-classic-italian-delight/"
}


def fetch_html(url: str) -> str:
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.text


def to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    body = soup.get_text(separator="\n")
    return body


def store_text(stem: str, url: str, text: str, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{stem}.txt"
    payload = f"Source: {stem.split('_')[0].title()}\nURL: {url}\n\n{text.strip()}\n"
    path.write_text(payload, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=NOISE_DIR, help="Folder for noise documents")
    args = parser.parse_args()

    for stem, url in TARGETS.items():
        try:
            html = fetch_html(url)
            text = to_text(html)
            store_text(stem, url, text, args.dest)
            print(f"Saved noise doc for {stem}")
        except Exception as exc:  # noqa: BLE001 - CLI utility
            print(f"Failed to fetch {url}: {exc}", file=sys.stderr)
            continue


if __name__ == "__main__":
    main()
