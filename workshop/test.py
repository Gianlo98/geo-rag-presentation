from __future__ import annotations

import argparse
import json
from typing import Optional

import importlib
import os


def load_module_table(table_name: str):
    os.environ["GEO_RAG_TABLE"] = table_name
    import geo_rag.config as cfg
    import geo_rag.pipeline as pipeline
    import geo_rag.workflow as workflow

    importlib.reload(cfg)
    importlib.reload(pipeline)
    importlib.reload(workflow)

    return workflow


def format_breakdown(metadata: dict) -> str:
    breakdown = metadata.get("score_breakdown") or {}
    return json.dumps(breakdown, indent=2)


def run(query_text: str, top_n: int, filter_slug: Optional[str], table_name: str) -> None:
    wf = load_module_table(table_name)
    wf.load_data(process_filter=filter_slug, process_documents=False)
    results = wf.query(query_text, top_n=top_n)
    print(f"\n=== Table: {table_name} ===")
    for idx, doc in enumerate(results, start=1):
        print(f"{idx}. {doc['title']} (slug={doc['slug']}) score={doc['score']}")
        print(format_breakdown(doc["metadata"]))
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Quick retrieval tester (per table).")
    parser.add_argument("query_text", help="Query to test")
    parser.add_argument("--top", type=int, default=3, help="Number of docs to show")
    parser.add_argument(
        "--filter",
        help="Optional slug substring (e.g., 'tiramisu') to limit processing",
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        required=True,
        help="One or more pgvector tables to compare",
    )
    args = parser.parse_args()
    for table in args.tables:
        run(args.query_text, args.top, args.filter, table)


if __name__ == "__main__":
    main()
