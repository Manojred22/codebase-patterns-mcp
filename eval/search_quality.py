"""
Search quality metrics: Recall@K, Precision@K, MRR, Fuzzy Recall@K.

Pure functions with no external dependencies.
"""

import re
from typing import List


def recall_at_k(retrieved_ids: List[str], expected_ids: List[str], k: int) -> float:
    """Fraction of expected results found in the top-K retrieved results.

    recall@k = |expected ∩ retrieved[:k]| / |expected|
    """
    if not expected_ids:
        return 1.0
    top_k = set(retrieved_ids[:k])
    found = sum(1 for eid in expected_ids if eid in top_k)
    return found / len(expected_ids)


def precision_at_k(retrieved_ids: List[str], expected_ids: List[str], k: int) -> float:
    """Fraction of top-K results that are in the expected set.

    precision@k = |expected ∩ retrieved[:k]| / k
    """
    if k == 0:
        return 0.0
    top_k = retrieved_ids[:k]
    expected_set = set(expected_ids)
    found = sum(1 for rid in top_k if rid in expected_set)
    return found / k


def mean_reciprocal_rank(retrieved_ids: List[str], expected_ids: List[str]) -> float:
    """Reciprocal of the rank of the first expected result.

    MRR = 1 / rank_of_first_relevant
    Returns 0.0 if no expected results found.
    """
    expected_set = set(expected_ids)
    for i, rid in enumerate(retrieved_ids):
        if rid in expected_set:
            return 1.0 / (i + 1)
    return 0.0


def fuzzy_recall_at_k(
    retrieved_ids: List[str], expected_patterns: List[str], k: int
) -> float:
    """Like recall@k but uses regex patterns instead of exact ID matching.

    Useful when exact function IDs aren't known yet (first indexing run).
    """
    if not expected_patterns:
        return 1.0
    top_k = retrieved_ids[:k]
    found = 0
    for pattern in expected_patterns:
        for rid in top_k:
            if re.search(pattern, rid):
                found += 1
                break
    return found / len(expected_patterns)


def fuzzy_mrr(retrieved_ids: List[str], expected_patterns: List[str]) -> float:
    """MRR using regex patterns for matching."""
    for i, rid in enumerate(retrieved_ids):
        for pattern in expected_patterns:
            if re.search(pattern, rid):
                return 1.0 / (i + 1)
    return 0.0
