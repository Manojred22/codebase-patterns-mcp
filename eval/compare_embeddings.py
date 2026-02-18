#!/usr/bin/env python3
"""
Compare embedding models for code search quality.

Tests each model by:
  1. Indexing the same repos with each embedding model (separate Chroma collections)
  2. Running the same ground truth queries
  3. Producing a side-by-side comparison report

Usage:
    python eval/compare_embeddings.py

Models compared:
  - OpenAI text-embedding-3-small  (baseline, cheapest)
  - OpenAI text-embedding-3-large  (higher quality, general purpose)
  - Voyage voyage-code-3           (code-specific, best on code benchmarks)
"""

import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

from src.indexer import CodeIndexer
from src.embeddings import EmbeddingGenerator
from src.vector_store import VectorStore
from eval.ground_truth import GROUND_TRUTH_QUERIES
from eval.search_quality import (
    recall_at_k,
    precision_at_k,
    mean_reciprocal_rank,
    fuzzy_recall_at_k,
    fuzzy_mrr,
)


@dataclass
class ModelConfig:
    name: str
    provider: str  # "openai" or "voyage"
    model_id: str
    dimensions: int
    cost_per_1m_tokens: float


MODELS = [
    ModelConfig(
        name="OpenAI small",
        provider="openai",
        model_id="text-embedding-3-small",
        dimensions=1536,
        cost_per_1m_tokens=0.02,
    ),
    ModelConfig(
        name="OpenAI large",
        provider="openai",
        model_id="text-embedding-3-large",
        dimensions=3072,
        cost_per_1m_tokens=0.13,
    ),
    ModelConfig(
        name="Voyage code-3",
        provider="voyage",
        model_id="voyage-code-3",
        dimensions=1024,
        cost_per_1m_tokens=0.18,
    ),
]


def create_embedding_generator(config: ModelConfig):
    """Create the appropriate embedding generator for a model config."""
    if config.provider == "openai":
        return EmbeddingGenerator(model=config.model_id)
    elif config.provider == "voyage":
        from src.embeddings_voyage import VoyageEmbeddingGenerator
        return VoyageEmbeddingGenerator(model=config.model_id)
    else:
        raise ValueError(f"Unknown provider: {config.provider}")


def index_with_model(config: ModelConfig, functions, repos_path: str) -> VectorStore:
    """Index functions with a specific embedding model into a dedicated collection."""
    collection_name = f"eval_{config.provider}_{config.model_id.replace('-', '_')}"
    chroma_path = os.getenv("CHROMA_PATH", "./data/chroma_db")

    print(f"\n{'='*60}")
    print(f"  Indexing with: {config.name} ({config.model_id})")
    print(f"  Collection: {collection_name}")
    print(f"{'='*60}")

    embedding_gen = create_embedding_generator(config)

    store = VectorStore(
        persist_directory=chroma_path,
        collection_name=collection_name,
        embedding_generator=embedding_gen,
    )

    # Reset collection for clean comparison
    store.reset()

    # Generate embeddings
    texts = [f.content for f in functions]
    start = time.monotonic()
    embeddings = embedding_gen.generate_embeddings(texts)
    embed_time = time.monotonic() - start

    # Store
    store.add_functions(functions, embeddings)

    print(f"  Indexed {store.collection.count()} functions in {embed_time:.1f}s")
    return store


def eval_model(config: ModelConfig, store: VectorStore) -> Dict[str, Any]:
    """Run ground truth queries against a model's index."""
    print(f"\n  Evaluating: {config.name}")

    query_results = []

    for tq in GROUND_TRUTH_QUERIES:
        results = store.search(tq.query, n_results=10)
        retrieved_ids = [r["id"] for r in results]

        r3 = recall_at_k(retrieved_ids, tq.expected_ids, 3)
        r5 = recall_at_k(retrieved_ids, tq.expected_ids, 5)
        p3 = precision_at_k(retrieved_ids, tq.expected_ids, 3)
        mrr = mean_reciprocal_rank(retrieved_ids, tq.expected_ids)
        fr5 = fuzzy_recall_at_k(retrieved_ids, tq.expected_id_patterns, 5)
        fmrr = fuzzy_mrr(retrieved_ids, tq.expected_id_patterns)

        query_results.append({
            "query_id": tq.id,
            "query": tq.query,
            "category": tq.category,
            "retrieved_ids": retrieved_ids[:5],
            "recall@3": r3,
            "recall@5": r5,
            "precision@3": p3,
            "mrr": mrr,
            "fuzzy_recall@5": fr5,
            "fuzzy_mrr": fmrr,
        })

    n = len(query_results)
    aggregate = {
        "recall@3": sum(qr["recall@3"] for qr in query_results) / n,
        "recall@5": sum(qr["recall@5"] for qr in query_results) / n,
        "precision@3": sum(qr["precision@3"] for qr in query_results) / n,
        "mrr": sum(qr["mrr"] for qr in query_results) / n,
        "fuzzy_recall@5": sum(qr["fuzzy_recall@5"] for qr in query_results) / n,
        "fuzzy_mrr": sum(qr["fuzzy_mrr"] for qr in query_results) / n,
    }

    return {"aggregate": aggregate, "queries": query_results}


def generate_comparison_report(
    results: Dict[str, Dict],
    models: List[ModelConfig],
    output_path: str,
):
    """Generate a markdown comparison report."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Embedding Model Comparison Report",
        f"\nGenerated: {now}\n",
        "## Models Tested\n",
        "| Model | Provider | Model ID | Dimensions | Cost/1M tokens |",
        "|-------|----------|----------|------------|----------------|",
    ]

    for m in models:
        lines.append(
            f"| {m.name} | {m.provider} | `{m.model_id}` | {m.dimensions} | ${m.cost_per_1m_tokens} |"
        )

    # Aggregate comparison
    lines.append("\n## Aggregate Metrics\n")

    metrics = ["recall@3", "recall@5", "precision@3", "mrr", "fuzzy_recall@5", "fuzzy_mrr"]

    header = "| Metric |"
    separator = "|--------|"
    for m in models:
        header += f" {m.name} |"
        separator += "--------|"
    lines.append(header)
    lines.append(separator)

    for metric in metrics:
        row = f"| {metric} |"
        scores = []
        for m in models:
            score = results[m.model_id]["aggregate"].get(metric, 0)
            scores.append(score)
            row += f" {score:.1%} |"
        lines.append(row)

    # Find winner for each metric
    lines.append("\n## Winner by Metric\n")
    lines.append("| Metric | Winner | Score |")
    lines.append("|--------|--------|-------|")

    for metric in metrics:
        best_score = -1
        best_model = ""
        for m in models:
            score = results[m.model_id]["aggregate"].get(metric, 0)
            if score > best_score:
                best_score = score
                best_model = m.name
        lines.append(f"| {metric} | **{best_model}** | {best_score:.1%} |")

    # Per-query breakdown
    lines.append("\n## Per-Query Comparison\n")

    for tq in GROUND_TRUTH_QUERIES:
        lines.append(f"### {tq.id}: `{tq.query}`\n")

        header = "| Metric |"
        separator = "|--------|"
        for m in models:
            header += f" {m.name} |"
            separator += "--------|"
        lines.append(header)
        lines.append(separator)

        for metric in ["recall@3", "recall@5", "precision@3", "mrr"]:
            row = f"| {metric} |"
            for m in models:
                qr_list = results[m.model_id]["queries"]
                qr = next((q for q in qr_list if q["query_id"] == tq.id), None)
                score = qr.get(metric, 0) if qr else 0
                row += f" {score:.2f} |"
            lines.append(row)

        # Show top-3 results for each model
        lines.append("\n**Top 3 results:**\n")
        for m in models:
            qr_list = results[m.model_id]["queries"]
            qr = next((q for q in qr_list if q["query_id"] == tq.id), None)
            if qr:
                lines.append(f"*{m.name}:*")
                for i, rid in enumerate(qr["retrieved_ids"][:3], 1):
                    lines.append(f"  {i}. `{rid}`")
                lines.append("")

    md = "\n".join(lines)

    with open(output_path, "w") as f:
        f.write(md)

    return md


def run_comparison():
    """Run the full embedding model comparison."""
    repos_path = os.getenv("REPOS_PATH", "./repos")

    # Check which models we can actually test
    available_models = []
    for m in MODELS:
        if m.provider == "openai" and os.getenv("OPENAI_API_KEY"):
            available_models.append(m)
        elif m.provider == "voyage" and os.getenv("VOYAGE_API_KEY"):
            available_models.append(m)
        else:
            print(f"  Skipping {m.name}: no {m.provider.upper()}_API_KEY found")

    if len(available_models) < 2:
        print("ERROR: Need at least 2 models to compare.")
        print("Set OPENAI_API_KEY and VOYAGE_API_KEY in .env")
        sys.exit(1)

    print(f"Comparing {len(available_models)} models: {[m.name for m in available_models]}")

    # Parse repos once (shared across all models)
    print("\nParsing repositories...")
    indexer = CodeIndexer(repos_path)
    functions = indexer.index_all_repos()
    print(f"Parsed {len(functions)} functions")

    if not functions:
        print("ERROR: No functions found. Make sure repos/ has code to index.")
        sys.exit(1)

    # Index and eval each model
    all_results = {}

    for config in available_models:
        store = index_with_model(config, functions, repos_path)
        result = eval_model(config, store)
        all_results[config.model_id] = result

        agg = result["aggregate"]
        print(f"  {config.name}: R@3={agg['recall@3']:.1%} R@5={agg['recall@5']:.1%} "
              f"P@3={agg['precision@3']:.1%} MRR={agg['mrr']:.1%}")

    # Generate report
    eval_dir = Path("data/eval")
    eval_dir.mkdir(parents=True, exist_ok=True)

    report_path = str(eval_dir / "embedding_comparison.md")
    generate_comparison_report(all_results, available_models, report_path)
    print(f"\nComparison report: {report_path}")

    # Save raw results
    results_path = str(eval_dir / "embedding_comparison.json")
    # Convert for JSON serialization
    serializable = {}
    for model_id, result in all_results.items():
        serializable[model_id] = result
    with open(results_path, "w") as f:
        json.dump(serializable, f, indent=2)
    print(f"Raw results: {results_path}")

    # Print summary
    print(f"\n{'='*60}")
    print("  COMPARISON SUMMARY")
    print(f"{'='*60}\n")

    header = f"{'Metric':<16}"
    for m in available_models:
        header += f" {m.name:<16}"
    print(header)
    print("-" * len(header))

    for metric in ["recall@3", "recall@5", "precision@3", "mrr"]:
        row = f"{metric:<16}"
        best = max(all_results[m.model_id]["aggregate"][metric] for m in available_models)
        for m in available_models:
            score = all_results[m.model_id]["aggregate"][metric]
            marker = " *" if score == best and len(available_models) > 1 else "  "
            row += f" {score:<14.1%}{marker}"
        print(row)

    print(f"\n{'='*60}")
    print("  * = best for that metric")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_comparison()
