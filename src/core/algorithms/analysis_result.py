"""Aggregate analytical result for a single legislative year.

This dataclass composes the per-year outputs of the analytical stage into one
typed object: the community-detection summaries, the partition-agreement
robustness measure (ARI), and the null-model significance test that validates
the central hypothesis (H1). No ``round()`` or ``str`` conversion happens inside
the ``core/`` layer; those are presentation concerns handled in ``repository/``.

Downstream (monograph tables, ``compare_years.py``, notebooks) code loads
``AnalysisResult`` instances back from disk instead of recomputing anything.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from core.algorithms.validation import NullModelResult


@dataclass(frozen=True)
class MethodSummary:
    """Aggregate metrics for a single community detection method."""

    modularity: float
    num_communities: int


@dataclass(frozen=True)
class ConcentrationSummary:
    """Inequality/concentration of a centrality distribution (research question a).

    ``gini`` in ``[0, 1]`` (0 = perfect equality, 1 = maximum concentration);
    ``top10_share`` is the fraction of the total held by the ten most central
    deputies.
    """

    gini: float
    top10_share: float


@dataclass(frozen=True)
class PartitionAgreement:
    """Similarity between two community partitions on the same graph.

    ``adjusted_rand_index`` follows the standard definition: values in
    ``[-1, 1]``; 0 is chance-level agreement, 1 is identical partitions.
    """

    adjusted_rand_index: float
    louvain_num_communities: int
    label_propagation_num_communities: int


@dataclass(frozen=True)
class AnalysisResult:
    """Canonical typed result of the analytical stage for one year.

    Attributes:
        year: Legislative year analysed.
        n_nodes: Nodes in the built graph (deputies that co-authored).
        n_edges: Edges in the built graph (unique co-authorship pairs).
        density: Graph density in ``[0, 1]``.
        max_authors: Value of the ``max_authors`` filter used to build the
            graph. Declared in the metodologia; must be persisted so results
            are reproducible.
        n_permutations: Number of permutations used in the null-model test.
        timestamp: ISO-8601 timestamp of the analysis run.
        louvain: Aggregate metrics for the Louvain partition.
        label_propagation: Aggregate metrics for the Label Propagation
            partition (robustness contraprova).
        partition_agreement: Similarity between the two partitions (ARI).
        null_model: Result of the null-model permutation test — the central
            hypothesis (H1).
    """

    year: int
    n_nodes: int
    n_edges: int
    density: float
    max_authors: int
    n_permutations: int
    timestamp: str

    louvain: MethodSummary
    label_propagation: MethodSummary
    partition_agreement: PartitionAgreement

    null_model: NullModelResult

    # Concentration of centrality per metric (research question a). Keyed by
    # metric name (e.g. "betweenness", "weighted_degree", "eigenvector").
    concentration: dict[str, ConcentrationSummary] = field(default_factory=dict)


def compute_adjusted_rand_index(
    partition_a: dict[int, int],
    partition_b: dict[int, int],
) -> float:
    """Adjusted Rand Index between two partitions of the same node set.

    Implemented directly (no scikit-learn dependency) using the standard
    contingency-table formulation. Only nodes present in both partitions are
    considered — if their intersection is empty the score is ``0.0``.
    """
    shared_nodes = set(partition_a) & set(partition_b)
    if not shared_nodes:
        return 0.0

    from collections import Counter

    pairs = [(partition_a[n], partition_b[n]) for n in shared_nodes]
    n = len(pairs)
    if n < 2:
        return 0.0

    contingency: Counter[tuple[int, int]] = Counter(pairs)
    row_totals: Counter[int] = Counter()
    col_totals: Counter[int] = Counter()
    for (a, b), count in contingency.items():
        row_totals[a] += count
        col_totals[b] += count

    def comb2(x: int) -> int:
        return x * (x - 1) // 2

    sum_comb_ij = sum(comb2(c) for c in contingency.values())
    sum_comb_row = sum(comb2(c) for c in row_totals.values())
    sum_comb_col = sum(comb2(c) for c in col_totals.values())
    total_pairs = comb2(n)

    expected = (sum_comb_row * sum_comb_col) / total_pairs if total_pairs else 0.0
    max_index = 0.5 * (sum_comb_row + sum_comb_col)
    denominator = max_index - expected
    if math.isclose(denominator, 0.0):
        # Both partitions collapse into a single group (or agree perfectly on
        # the trivial partition) — ARI is defined as 1.0 in that case.
        return 1.0
    return (sum_comb_ij - expected) / denominator
