from __future__ import annotations

import math
import os
import time
from typing import Tuple
from urllib.parse import urlparse

import psycopg2
from psycopg2 import sql

from geo_rag import EVAL_QUESTIONS
from geo_rag.workflow import load_data, query

DEFAULT_DB = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/geo_rag"
)


def ensure_database(db_url: str) -> None:
    parsed = urlparse(db_url)
    db_name = parsed.path.lstrip("/") or "postgres"
    admin_path = parsed._replace(path="/postgres").geturl()
    conn = psycopg2.connect(admin_path)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cur.fetchone()
        if not exists:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
    conn.close()


def wait_for_db(db_url: str, retries: int = 10, delay: float = 1.0) -> None:
    for attempt in range(retries):
        try:
            conn = psycopg2.connect(db_url)
            conn.close()
            return
        except psycopg2.OperationalError:
            time.sleep(delay)
    raise RuntimeError("Database is not reachable; ensure Postgres is running")


def run_evaluation(db_url: str) -> Tuple[int, int, float]:
    ensure_database(db_url)
    wait_for_db(db_url)
    load_data(db_url=db_url)
    total = len(EVAL_QUESTIONS)
    hits = 0
    for item in EVAL_QUESTIONS:
        top_n = item.get("top_n", 3)
        results = query(item["question"], user_region=item.get("region_hint"), top_n=top_n)
        retrieved_slugs = [row["slug"] for row in results]
        expected_slug = item.get("expected_slug")
        forbidden_slugs = set(item.get("forbidden_slugs", []))
        require_empty = item.get("require_empty", False)

        success = True
        if expected_slug:
            success = expected_slug in retrieved_slugs
        elif expected_slug is None and require_empty:
            success = not retrieved_slugs

        if forbidden_slugs and any(slug in forbidden_slugs for slug in retrieved_slugs):
            success = False

        if success:
            hits += 1
    if hits == total:
        score = 100.0
    elif hits == 0:
        score = -100.0
    else:
        score = round(((hits / total) * 200) - 100, 2)
    return hits, total, score


def main() -> None:
    db_url = DEFAULT_DB
    hits, total, score = run_evaluation(db_url)
    print(f"Queries run: {total}")
    print(f"Correct local documents in top 3: {hits}")
    print(f"Score: {score}")
    if hits < total:
        print("Run penalized queries again or inspect geo_rag/questions.py for gaps.")


if __name__ == "__main__":
    main()
