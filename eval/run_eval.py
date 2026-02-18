#!/usr/bin/env python3
"""
Main evaluation entry point.

Usage:
    python eval/run_eval.py

1. Loads VectorStore + EmbeddingGenerator
2. Runs 8 ground truth test queries
3. Computes aggregate metrics (Recall@3, Recall@5, Precision@3, MRR, Fuzzy Recall)
4. Saves results to data/eval/results.json
5. Generates markdown report to data/eval/report.md
"""

import json
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

from src.vector_store import VectorStore
from src.embeddings import EmbeddingGenerator
from eval.ground_truth import GROUND_TRUTH_QUERIES
from eval.search_quality import (
    recall_at_k,
    precision_at_k,
    mean_reciprocal_rank,
    fuzzy_recall_at_k,
    fuzzy_mrr,
)
from eval.report import generate_report


def run_evaluation():
    """Run the full search quality evaluation."""
    chroma_path = os.getenv("CHROMA_PATH", "./data/chroma_db")
    embedding_generator = EmbeddingGenerator()
    vector_store = VectorStore(
        persist_directory=chroma_path,
        embedding_generator=embedding_generator,
    )

    count = vector_store.collection.count()
    print(f"Vector store loaded: {count} indexed functions")

    if count == 0:
        print("ERROR: Vector store is empty. Run indexing first:")
        print("  python index_repos.py --reset")
        sys.exit(1)

    query_results = []

    for tq in GROUND_TRUTH_QUERIES:
        print(f"\n--- {tq.id}: {tq.query}")
        results = vector_store.search(tq.query, n_results=10)

        retrieved_ids = [r["id"] for r in results]

        r3 = recall_at_k(retrieved_ids, tq.expected_ids, 3)
        r5 = recall_at_k(retrieved_ids, tq.expected_ids, 5)
        p3 = precision_at_k(retrieved_ids, tq.expected_ids, 3)
        mrr = mean_reciprocal_rank(retrieved_ids, tq.expected_ids)
        fr3 = fuzzy_recall_at_k(retrieved_ids, tq.expected_id_patterns, 3)
        fr5 = fuzzy_recall_at_k(retrieved_ids, tq.expected_id_patterns, 5)
        fmrr = fuzzy_mrr(retrieved_ids, tq.expected_id_patterns)

        qr = {
            "query_id": tq.id,
            "query": tq.query,
            "category": tq.category,
            "result_count": len(results),
            "retrieved_ids": retrieved_ids,
            "expected_ids": tq.expected_ids,
            "recall@3": r3,
            "recall@5": r5,
            "precision@3": p3,
            "mrr": mrr,
            "fuzzy_recall@3": fr3,
            "fuzzy_recall@5": fr5,
            "fuzzy_mrr": fmrr,
        }
        query_results.append(qr)

        print(f"  Results: {len(results)} | R@3={r3:.2f} R@5={r5:.2f} P@3={p3:.2f} MRR={mrr:.2f}")
        print(f"  Fuzzy:   FR@3={fr3:.2f} FR@5={fr5:.2f} FMRR={fmrr:.2f}")
        for i, rid in enumerate(retrieved_ids[:5], 1):
            match = "<<" if rid in tq.expected_ids else ""
            print(f"    {i}. {rid} {match}")

    # Compute aggregates
    n = len(query_results)
    aggregate = {
        "recall@3": sum(qr["recall@3"] for qr in query_results) / n,
        "recall@5": sum(qr["recall@5"] for qr in query_results) / n,
        "precision@3": sum(qr["precision@3"] for qr in query_results) / n,
        "mrr": sum(qr["mrr"] for qr in query_results) / n,
        "fuzzy_recall@3": sum(qr["fuzzy_recall@3"] for qr in query_results) / n,
        "fuzzy_recall@5": sum(qr["fuzzy_recall@5"] for qr in query_results) / n,
        "fuzzy_mrr": sum(qr["fuzzy_mrr"] for qr in query_results) / n,
    }

    print("\n=== Aggregate Metrics ===")
    for k, v in aggregate.items():
        print(f"  {k}: {v:.2%}")

    # Save results
    eval_dir = Path("data/eval")
    eval_dir.mkdir(parents=True, exist_ok=True)

    results_path = eval_dir / "results.json"
    with open(results_path, "w") as f:
        json.dump(
            {"aggregate": aggregate, "queries": query_results},
            f,
            indent=2,
        )
    print(f"\nResults saved to {results_path}")

    # Generate report
    report_path = str(eval_dir / "report.md")
    generate_report(query_results, aggregate, report_path)
    print(f"Report saved to {report_path}")

    return aggregate


if __name__ == "__main__":
    run_evaluation()
