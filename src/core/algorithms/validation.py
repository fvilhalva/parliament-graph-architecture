"""Statistical validation of community structure via null-model permutation tests.

Reference approach: compare the observed modularity against a distribution of
modularity values obtained from randomised graphs that preserve the degree
sequence of the original network (Configuration Model).

If the observed modularity is significantly higher than the null distribution
(p < 0.05), the detected community structure is unlikely to have arisen by
chance.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

import networkx as nx

from core.algorithms.community_detection import CommunityDetector


@dataclass
class NullModelResult:
    """Result of a null-model permutation test for community significance.

    Attributes:
        q_observed: Modularity of the original graph.
        q_null_mean: Mean modularity across randomised graphs.
        q_null_std: Standard deviation of the null distribution.
        p_value: Fraction of null graphs whose modularity >= q_observed.
        n_permutations: Number of null graphs generated.
        significant: True when p_value < alpha.
        alpha: Significance threshold used.
    """

    q_observed: float
    q_null_mean: float
    q_null_std: float
    p_value: float
    n_permutations: int
    significant: bool
    alpha: float = 0.05

    def __str__(self) -> str:
        sig = "SIGNIFICANT" if self.significant else "NOT significant"
        return (
            f"Community structure: {sig} (p={self.p_value:.4f}, alpha={self.alpha})\n"
            f"  Q_observed = {self.q_observed:.4f}\n"
            f"  Q_null     = {self.q_null_mean:.4f} ± {self.q_null_std:.4f}"
        )


def _randomise_graph(graph: nx.Graph, n_swaps_factor: int = 10) -> nx.Graph:
    """Return a copy of *graph* with edges randomly rewired.

    Uses the double-edge-swap method, which preserves the degree sequence
    exactly. Each swap exchanges the endpoints of two randomly chosen edges
    while preventing self-loops and multi-edges.

    Args:
        graph: Original graph (not modified).
        n_swaps_factor: Number of attempted swaps = n_swaps_factor * |E|.
    """
    randomised = graph.copy()
    n_swaps = n_swaps_factor * randomised.number_of_edges()
    try:
        nx.double_edge_swap(randomised, nswap=n_swaps, max_tries=n_swaps * 10)
    except nx.NetworkXError:
        # Falls back gracefully if the graph is too sparse for the requested swaps.
        pass
    return randomised


def assess_community_significance(
    graph: nx.Graph,
    n_permutations: int = 1000,
    alpha: float = 0.05,
    seed: int | None = 42,
    detect_fn: Callable[[nx.Graph], dict] | None = None,
) -> NullModelResult:
    """Test whether the detected community structure is statistically significant.

    Generates *n_permutations* degree-preserving random graphs and compares
    their Louvain modularity against the modularity of the original *graph*.

    Args:
        graph: The real parliamentary co-authorship graph.
        n_permutations: Number of null-model graphs to generate (≥ 100
            recommended; 1000 for publication-quality results).
        alpha: Significance level.
        seed: Random seed for reproducibility.
        detect_fn: Optional community detection callable ``f(graph) -> partition``.
            Defaults to Louvain with seed=42.

    Returns:
        :class:`NullModelResult` with Q values, p-value, and significance flag.
    """
    if seed is not None:
        random.seed(seed)

    detector = CommunityDetector()

    if detect_fn is None:
        detect_fn = lambda g: detector.detect_louvain(g, seed=seed)  # noqa: E731

    # --- Observed modularity ---
    partition_real = detect_fn(graph)
    q_observed = detector.calculate_modularity(graph, partition_real)

    # --- Null distribution ---
    null_q_values: list[float] = []
    for _ in range(n_permutations):
        null_graph = _randomise_graph(graph)
        null_partition = detect_fn(null_graph)
        null_q = detector.calculate_modularity(null_graph, null_partition)
        null_q_values.append(null_q)

    # --- Statistics ---
    n = len(null_q_values)
    q_null_mean = sum(null_q_values) / n if n else 0.0
    q_null_std = (
        (sum((q - q_null_mean) ** 2 for q in null_q_values) / n) ** 0.5 if n > 1 else 0.0
    )
    p_value = sum(1 for q in null_q_values if q >= q_observed) / n if n else 1.0

    return NullModelResult(
        q_observed=q_observed,
        q_null_mean=q_null_mean,
        q_null_std=q_null_std,
        p_value=p_value,
        n_permutations=n_permutations,
        significant=p_value < alpha,
        alpha=alpha,
    )
