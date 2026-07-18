"""Statistical validation of community structure via null-model permutation tests.

Reference approach: compare the observed modularity against a distribution of
modularity values obtained from randomised graphs that preserve the degree
sequence of the original network (Configuration Model).

If the observed modularity is significantly higher than the null distribution
(p < 0.05), the detected community structure is unlikely to have arisen by
chance.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

import networkx as nx

from core.algorithms.community_detection import CommunityDetector
from core.algorithms.stats import spearman_or_nan

if TYPE_CHECKING:  # pragma: no cover - import only for type hints
    from core.graph import ParliamentaryGraph


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


# ---------------------------------------------------------------------------
# Label-permutation tests for party-level structural associations.
#
# Historical note: these functions were originally introduced as tests for
# hypotheses H2 (broker parties) and H3 (echo chambers). Those hypothesis
# labels have since been reformulated in strictly topological terms (see the
# monograph); these party-level tests were retained as complementary evidence
# and renamed to describe what they actually measure.
#
# Unlike the null-model test above, these do NOT rewire the graph. The network
# topology (and therefore every per-deputy centrality) is held fixed; only the
# ``party_code`` labels are shuffled across deputies. This isolates the
# question "is the observed party-level association stronger than what random
# label assignment would produce?" from any structural artefact of the graph.
# ---------------------------------------------------------------------------


@dataclass
class PermutationResult:
    """Result of a label-permutation test for a party-level association.

    Mirrors :class:`NullModelResult` so both validations read the same way.

    Attributes:
        statistic_observed: Correlation statistic on the real labels.
        statistic_null_mean: Mean statistic across label permutations.
        statistic_null_std: Standard deviation of the null distribution.
        p_value: Fraction of permutations as or more extreme than observed.
        n_permutations: Number of label permutations actually evaluated.
        significant: True when ``p_value < alpha`` and the result is valid.
        two_sided: Whether the p-value was computed two-sided.
        alpha: Significance threshold used.
        valid: False when the sample was too small to compute a reliable
            statistic (fewer than three parties). When False, ``significant``
            is forced to False and the numeric fields are neutral placeholders.
    """

    statistic_observed: float
    statistic_null_mean: float
    statistic_null_std: float
    p_value: float
    n_permutations: int
    significant: bool
    two_sided: bool = True
    alpha: float = 0.05
    valid: bool = True

    def __str__(self) -> str:
        if not self.valid:
            return (
                "Label association: INCONCLUSIVE (too few parties for a "
                "reliable correlation)"
            )
        sig = "SIGNIFICANT" if self.significant else "NOT significant"
        tail = "two-sided" if self.two_sided else "one-sided"
        return (
            f"Label association: {sig} (p={self.p_value:.4f}, alpha={self.alpha}, {tail})\n"
            f"  statistic_observed = {self.statistic_observed:.4f}\n"
            f"  statistic_null     = {self.statistic_null_mean:.4f} ± {self.statistic_null_std:.4f}"
        )


def party_size_vs_mean_betweenness_statistic(
    parliamentary_graph: "ParliamentaryGraph",
    min_party_size: int = 1,
) -> float:
    """Spearman rho between bench size and mean betweenness across parties.

    Historical note: this was originally named ``h2_benchsize_betweenness``
    when the trabalho tested the (now reformulated) "broker parties" hypothesis
    (H2). It is kept as a complementary party-level test.

    A negative rho would mean brokers (high betweenness) are concentrated in
    the *smaller* parties.
    """
    frame = parliamentary_graph.filter_parties_by_betweenness(min_party_size=min_party_size)
    return spearman_or_nan(frame["num_deputies"], frame["avg_betweenness"])


def party_degree_vs_betweenness_statistic(
    parliamentary_graph: "ParliamentaryGraph",
    min_party_size: int = 1,
) -> float:
    """Spearman rho between party mean weighted degree and mean betweenness.

    Historical note: this was originally named ``h3_degree_betweenness``
    when the trabalho tested the (now reformulated) "echo chambers" hypothesis
    (H3). Joins the per-party degree and betweenness rankings on ``party_code``
    and correlates ``avg_weighted_degree`` against ``avg_betweenness``.
    """
    bet = parliamentary_graph.filter_parties_by_betweenness(min_party_size=min_party_size)
    deg = parliamentary_graph.filter_parties_by_degree(min_party_size=min_party_size)
    merged = bet.merge(deg[["party_code", "avg_weighted_degree"]], on="party_code")
    return spearman_or_nan(merged["avg_weighted_degree"], merged["avg_betweenness"])


def assess_label_association(
    parliamentary_graph: "ParliamentaryGraph",
    statistic_fn: Callable[["ParliamentaryGraph"], float],
    n_permutations: int = 1000,
    alpha: float = 0.05,
    seed: int | None = 42,
    two_sided: bool = True,
) -> PermutationResult:
    """Test a party-level association via ``party_code`` label permutation.

    The graph topology is never modified. Deputy ``party_code`` labels are
    shuffled across the deputies present in the network, the statistic is
    recomputed, and the observed value is compared against this null
    distribution. Original labels are always restored, even if ``statistic_fn``
    raises.

    Args:
        parliamentary_graph: The built :class:`ParliamentaryGraph`.
        statistic_fn: Callable ``f(parliamentary_graph) -> float`` returning the
            association statistic (e.g. a Spearman correlation). Should return
            ``NaN`` when it cannot be computed reliably.
        n_permutations: Number of label permutations to evaluate.
        alpha: Significance level.
        seed: Random seed for reproducibility.
        two_sided: When True, extremeness is measured on ``|statistic|``. When
            False, a one-sided test is run in the direction of the *observed*
            statistic's sign (e.g. negative for H2).

    Returns:
        :class:`PermutationResult`. If the observed statistic is undefined
        (too few parties), returns a neutral result flagged ``valid=False``.
    """
    rng = random.Random(seed)

    observed = statistic_fn(parliamentary_graph)
    if observed is None or math.isnan(observed):
        return PermutationResult(
            statistic_observed=float("nan"),
            statistic_null_mean=float("nan"),
            statistic_null_std=float("nan"),
            p_value=1.0,
            n_permutations=0,
            significant=False,
            two_sided=two_sided,
            alpha=alpha,
            valid=False,
        )

    # Only deputies that are actually nodes in the graph contribute to the
    # party aggregation, so we permute labels within exactly that population.
    node_deputies = [
        parliamentary_graph.deputies.get(node_id)
        for node_id in parliamentary_graph.graph.nodes()
    ]
    node_deputies = [dep for dep in node_deputies if dep is not None]
    original_labels = [dep.party_code for dep in node_deputies]

    null_stats: list[float] = []
    try:
        for _ in range(n_permutations):
            shuffled = original_labels[:]
            rng.shuffle(shuffled)
            for dep, label in zip(node_deputies, shuffled):
                dep.party_code = label

            stat = statistic_fn(parliamentary_graph)
            if stat is not None and not math.isnan(stat):
                null_stats.append(stat)
    finally:
        # Restore the live state unconditionally.
        for dep, label in zip(node_deputies, original_labels):
            dep.party_code = label

    n = len(null_stats)
    if n == 0:
        return PermutationResult(
            statistic_observed=observed,
            statistic_null_mean=float("nan"),
            statistic_null_std=float("nan"),
            p_value=1.0,
            n_permutations=0,
            significant=False,
            two_sided=two_sided,
            alpha=alpha,
            valid=False,
        )

    null_mean = sum(null_stats) / n
    null_std = (sum((s - null_mean) ** 2 for s in null_stats) / n) ** 0.5 if n > 1 else 0.0

    if two_sided:
        p_value = sum(1 for s in null_stats if abs(s) >= abs(observed)) / n
    elif observed < 0:
        p_value = sum(1 for s in null_stats if s <= observed) / n
    else:
        p_value = sum(1 for s in null_stats if s >= observed) / n

    return PermutationResult(
        statistic_observed=observed,
        statistic_null_mean=null_mean,
        statistic_null_std=null_std,
        p_value=p_value,
        n_permutations=n,
        significant=p_value < alpha,
        two_sided=two_sided,
        alpha=alpha,
        valid=True,
    )
