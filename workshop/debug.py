import json
from pathlib import Path
from typing import List, Dict, Optional

import streamlit as st

from geo_rag import workflow

ROOT = Path(__file__).resolve().parent
GRAPH_PATH = ROOT / "output" / "knowledge_graph.html"

st.set_page_config(page_title="GEO Debug Console", layout="wide")

if "pipeline_filter" not in st.session_state:
    st.session_state["pipeline_filter"] = "tiramisu"


def ensure_pipeline(process_filter: Optional[str], force: bool = False) -> None:
    needs_reload = force or "pipeline" not in st.session_state
    if not force and st.session_state.get("pipeline_filter") != process_filter:
        needs_reload = False
    if needs_reload:
        with st.spinner("Loading pipeline..."):
            st.session_state["pipeline"] = workflow.load_data(process_filter=process_filter)
            st.session_state["pipeline_filter"] = process_filter


# Determine filter mode
sidebar = st.sidebar
sidebar.markdown("### Modes")
tiramisu_mode = sidebar.checkbox(
    "Tiramisu mode (faster debug)",
    value=st.session_state.get("pipeline_filter") == "tiramisu",
)
current_filter = "tiramisu" if tiramisu_mode else None

if "pipeline" not in st.session_state:
    ensure_pipeline(current_filter, force=True)

filter_mismatch = st.session_state.get("pipeline_filter") != current_filter

st.title("GEO Debug Console")
st.caption("Inspect structured data, reload embeddings, and test retrieval results quickly.")

col1, col2 = st.columns([1.2, 1.8])

with col1:
    st.subheader("Controls")
    if filter_mismatch:
        st.info("Mode changed. Click reload to apply filter.")
    if st.button("Reload embeddings & reset DB"):
        st.session_state["pipeline"] = workflow.load_data(
            refresh_cache=True,
            reset_table=True,
            process_filter=current_filter,
        )
        st.session_state["pipeline_filter"] = current_filter
        st.success("Pipeline reloaded.")

pipeline_ready = ("pipeline" in st.session_state) and not filter_mismatch

with col1:
    st.subheader("Score Signal Table")
    if not pipeline_ready:
        st.info("Pipeline not ready — reload to view score table.")
    elif GRAPH_PATH.exists():
        html_content = GRAPH_PATH.read_text(encoding="utf-8")
        st.components.v1.html(html_content, height=500, scrolling=True)
        st.caption("Columns reflect the structured signals feeding the reranker.")
    else:
        st.info("Score table not generated yet. Run load_data() first.")

with col2:
    st.subheader("Query Sandbox")
    if not pipeline_ready:
        st.info("Pipeline not ready — reload to test queries.")
    else:
        question = st.text_area("Enter a GEO query", value="Which article captures saffron telemetry for risotto?", height=100)
        top_k = st.slider("Results", min_value=1, max_value=100, value=5)

        if st.button("Run Retrieval"):
            with st.spinner("Querying pipeline..."):
                results = workflow.query(question, user_region=None, top_n=top_k)
            st.write(f"Retrieved {len(results)} nodes")
            for idx, doc in enumerate(results, start=1):
                st.markdown(
                    f"**{idx}. {doc['title']}** (`{doc['slug']}`) — {doc['source_type']}"
                )
                geo_meta = doc["metadata"]
                st.markdown(
                    "Score: `{score}` | Parsed ingredients: {parsed_ing} | Instruction steps: {steps}".format(
                        score=doc["score"],
                        parsed_ing=geo_meta.get("num_parsed_ingredients", geo_meta.get("parsed_ingredient_count", 0)),
                        steps=geo_meta.get("num_instruction_steps", geo_meta.get("parsed_instruction_count", 0)),
                    )
                )
                st.caption(
                    "Basic fields: {basic} | Ingredient snips: {ing_snip} | Instruction snips: {inst_snip} | Authority: {authority}".format(
                        basic=geo_meta.get("num_basic_structured_fields", geo_meta.get("structured_field_count", 0)),
                        ing_snip=geo_meta.get("ingredient_snippet_count", 0),
                        inst_snip=geo_meta.get("instruction_snippet_count", 0),
                        authority=geo_meta.get("domain_authority", 0),
                    )
                )
                breakdown = geo_meta.get("score_breakdown") or {}
                if breakdown:
                    ordered_pairs = [
                        ("similarity", "Similarity"),
                        ("structured", "Structured"),
                        ("fact_density", "Fact density"),
                        ("information_gain", "Info gain"),
                        ("seo", "SEO"),
                        ("tie_break", "Tie break"),
                        ("penalty", "Penalty"),
                        ("final", "Final"),
                    ]
                    mix_display = []
                    for key, label in ordered_pairs:
                        value = breakdown.get(key)
                        if isinstance(value, (int, float)):
                            mix_display.append(f"{label}: {value:.4f}")
                    if mix_display:
                        st.caption("Score mix → " + ", ".join(mix_display))
                st.caption(doc["snippet"]) 
                with st.expander("Metadata dump"):
                    st.json(doc["metadata"])
