"""
Markdown report generator for evaluation results.

Produces a report with per-query metrics, aggregate scores, and pass/fail targets.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List


# Targets for aggregate metrics
TARGETS = {
    "recall@3": 0.90,
    "recall@5": 0.80,
    "precision@3": 0.80,
    "mrr": 0.85,
}


def generate_report(
    query_results: List[Dict[str, Any]],
    aggregate: Dict[str, float],
    output_path: str,
) -> str:
    """Generate a markdown report and write it to output_path.

    Returns the markdown string.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Search Quality Evaluation Report",
        f"\nGenerated: {now}\n",
        "## Aggregate Metrics\n",
        "| Metric | Score | Target | Status |",
        "|--------|-------|--------|--------|",
    ]

    for metric, target in TARGETS.items():
        score = aggregate.get(metric, 0.0)
        status = "PASS" if score >= target else "FAIL"
        lines.append(f"| {metric} | {score:.2%} | {target:.0%} | {status} |")

    # Add fuzzy metrics (no target, informational)
    for key in ("fuzzy_recall@3", "fuzzy_recall@5", "fuzzy_mrr"):
        if key in aggregate:
            lines.append(f"| {key} | {aggregate[key]:.2%} | — | — |")

    lines.append(f"\n## Per-Query Results ({len(query_results)} queries)\n")
    lines.append(
        "| Query ID | Category | Results | Recall@3 | Recall@5 | P@3 | MRR | Fuzzy R@5 |"
    )
    lines.append(
        "|----------|----------|---------|----------|----------|-----|-----|-----------|"
    )

    for qr in query_results:
        lines.append(
            f"| {qr['query_id']} | {qr['category']} | {qr['result_count']} "
            f"| {qr.get('recall@3', 0):.2f} | {qr.get('recall@5', 0):.2f} "
            f"| {qr.get('precision@3', 0):.2f} | {qr.get('mrr', 0):.2f} "
            f"| {qr.get('fuzzy_recall@5', 0):.2f} |"
        )

    lines.append("\n## Query Details\n")
    for qr in query_results:
        lines.append(f"### {qr['query_id']}: `{qr['query']}`\n")
        lines.append(f"**Category:** {qr['category']}\n")

        if qr.get("retrieved_ids"):
            lines.append("**Retrieved IDs:**")
            for i, rid in enumerate(qr["retrieved_ids"][:5], 1):
                lines.append(f"  {i}. `{rid}`")

        if qr.get("expected_ids"):
            lines.append("\n**Expected IDs:**")
            for eid in qr["expected_ids"]:
                found = eid in qr.get("retrieved_ids", [])
                mark = "found" if found else "missing"
                lines.append(f"  - `{eid}` ({mark})")

        lines.append("")

    md = "\n".join(lines)

    with open(output_path, "w") as f:
        f.write(md)

    return md
