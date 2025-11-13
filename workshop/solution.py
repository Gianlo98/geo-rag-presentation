from __future__ import annotations

"""
GEO RAG Workshop — Student Starter File (solutions.py)

Your task is to modify `process_node`. This function is called once per document.
You will enrich the node's metadata using JSON-LD and generate extra TextNode
snippets built from structured recipe data.

The pipeline will automatically embed anything you return.

Follow the step-by-step instructions inside `process_node`.

Scoring primer (mirrors `GeoPrioritizer`):
- Final score = 0.1*similarity + 0.25*structured + 0.15*fact_density + 0.1*information_gain + 0.45*SEO + 0.05*tie_break − schema_penalty.
- Similarity: comes directly from the retriever score; you only influence it indirectly by producing better chunks/snippets for embedding.
- Structured: 0.02 * (# basic structured fields) + 1.0 * (# parsed ingredients) + 0.5 * (# parsed steps). Increase by emitting well-labeled metadata, parsed ingredient/step lists, and nutrition/FAQ/etc.
- Fact density: 0.3 * ingredient_snippet_count + 0.2 * instruction_snippet_count. Every extra structured snippet you emit (ingredients, steps) boosts this.
- Information gain: +0.5 if ingredients parsed, +0.3 if instructions parsed, +0.1 if schema detected, +0.1 if >5 other structured fields. Populate parsed arrays & metadata to hit these thresholds.
- SEO: log-scaled authority/backlink counts + backlink_score. Workflow seeds locals with low numbers (8 backlinks / DA 18) and externals high (240 / 82) so structured work is the main lever students control (metadata enrichment, snippets) to outrank noisy externals.
- Tie break: reuses the structured score, so any structured improvements compound.
- Schema penalty: −0.05 if `has_schema_markup` is false. Ensuring JSON-LD detection (or adding fallback metadata) removes it.
- Ingredient/Instruction snippets drive `fact_density` and help `structured`/`information_gain` once parsed counts rise. Nutrition/summary chunks and linked assets add to `structured_field_count`, aiding structured/tie-break.
"""

import json
from typing import List

from llama_index.core.schema import TextNode

from geo_rag.pipeline import GeoRAGPipeline
from geo_rag.utils import load_json_ld


def process_node(node: TextNode, pipeline: GeoRAGPipeline) -> List[TextNode]:
    """
    ============================
    WORKSHOP OBJECTIVE SUMMARY:
    ============================

    Your job is to:
      1. Parse JSON-LD metadata for each recipe page.
      2. Promote the useful structured fields into node.metadata.
      3. Extract ingredients into a canonical structured format.
      4. Emit one TextNode per ingredient.
      5. Emit one TextNode per instruction step.
      6. Set prioritization metadata (chunk_rank etc.).
      7. Return all new snippets so they get embedded.

    The comments below tell you exactly what to do.
    """

    print(f"[debug] Processing node {node.id_}...")

    metadata = dict(node.metadata)
    slug = metadata.get("slug", node.id_)

    # ----------------------------------------------------------
    # STEP 1 — LOAD JSON-LD
    # ----------------------------------------------------------
    # Every recipe page exposes JSON-LD schema.org data. You must
    # extract it and inspect its structure. This is where your
    # structured data will come from.
    json_ld_entries = load_json_ld(slug)

    if json_ld_entries:
        print(
            f"[debug] JSON-LD sample for {slug}:",
            json.dumps(json_ld_entries, indent=2),
        )

    # TASK:
    #   - Look at the JSON printed above.
    #   - Identify all "@type" values (e.g., Recipe, Article).
    #   - Promote them into metadata["structured_types"].

    # ----------------------------------------------------------
    # STEP 2 — PROMOTE IMPORTANT JSON-LD FIELDS
    # ----------------------------------------------------------
    # You should extract fields like:
    #   - name
    #   - description
    #   - totalTime / prepTime
    #   - recipeIngredient[]
    #   - recipeInstructions[]
    #
    # And attach them directly onto the node metadata so retrieval
    # becomes more precise. Example:
    #
    #   metadata["recipe_name"] = ld.get("name")
    #
    # The pipeline uses prioritization signals like:
    #   - metadata["structured_types"]
    #   - metadata["has_schema_markup"]
    #   - metadata["chunk_rank"]
    #
    # Make sure your code sets them.

    metadata.setdefault("structured_types", [])
    metadata["has_schema_markup"] = bool(json_ld_entries)

    # ----------------------------------------------------------
    # STEP 3 — EXTRACT & STRUCTURE INGREDIENTS
    # ----------------------------------------------------------
    # JSON-LD ingredients look like:
    #   "1 cup chopped carrots"
    #
    # Your job is to:
    #   - Parse quantity (1)
    #   - Parse unit (cup)
    #   - Parse ingredient (carrots)
    #   - Parse modifier (chopped)
    #
    # Then create a Python dict like:
    #
    #   {
    #       "name": "carrots",
    #       "quantity": "1",
    #       "unit": "cup",
    #       "modifier": "chopped"
    #   }
    #
    # Add the final list to:
    #   metadata["ingredients_structured"] = [...]
    #
    # Students: you must write the parsing logic yourselves!

    structured_ingredients = []   # TODO: fill with parsed ingredients
    metadata["ingredients_structured"] = structured_ingredients

    # ----------------------------------------------------------
    # STEP 4 — CREATE INGREDIENT SNIPPETS
    # ----------------------------------------------------------
    # For each structured ingredient, create a new TextNode.
    #
    # Example snippet text:
    #
    #   Ingredient: carrots
    #   Quantity: 1 cup
    #   Modifier: chopped
    #
    # Metadata should include:
    #   - chunk_type="ingredient"
    #   - ingredient_name="carrots"
    #   - chunk_rank=10   (lower number == higher priority)
    #
    # Store all snippets in extra_snippets.

    extra_snippets: List[TextNode] = []

    for ing in structured_ingredients:
        snippet_text = (
            f"Ingredient: {ing['name']}\n"
            f"Quantity: {ing.get('quantity', '')} {ing.get('unit', '')}\n"
            f"Modifier: {ing.get('modifier', '')}"
        )

        snippet_meta = dict(metadata)
        snippet_meta.update({
            "chunk_type": "ingredient",
            "ingredient_name": ing["name"],
            "chunk_rank": 10,
        })

        extra_snippets.append(TextNode(text=snippet_text, metadata=snippet_meta))

    # ----------------------------------------------------------
    # STEP 5 — EXTRACT & EMIT INSTRUCTION SNIPPETS
    # ----------------------------------------------------------
    # JSON-LD instructions may be:
    #   - A list of strings
    #   - A list of objects with "@type": "HowToStep"
    #
    # Convert each into a clean text snippet.
    # Attach metadata like:
    #   chunk_type="instruction"
    #   step_index=i
    #   chunk_rank=20
    #
    # Add them to extra_snippets.

    # TODO: parse instructions from JSON-LD
    structured_instructions = []  # fill this list

    for idx, step in enumerate(structured_instructions):
        snippet_text = f"Step {idx + 1}: {step}"

        snippet_meta = dict(metadata)
        snippet_meta.update({
            "chunk_type": "instruction",
            "step_index": idx,
            "chunk_rank": 20,
        })

        extra_snippets.append(TextNode(text=snippet_text, metadata=snippet_meta))

    # ----------------------------------------------------------
    # STEP 6 — UPDATE METADATA & RETURN SNIPPETS
    # ----------------------------------------------------------
    # At the end, update the node metadata and return all snippets.
    # The pipeline will embed everything automatically.
    node.metadata = metadata

    return extra_snippets
