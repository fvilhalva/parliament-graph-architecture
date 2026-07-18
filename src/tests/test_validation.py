"""Tests for the null-model community significance validation."""

from functools import partial

import networkx as nx
import pytest

from core.algorithms.validation import (
    NullModelResult,
    PermutationResult,
    assess_community_significance,
    assess_label_association,
    party_degree_vs_betweenness_statistic,
    party_size_vs_mean_betweenness_statistic,
)
from core.graph import ParliamentaryGraph
from models.deputy import Deputy


@pytest.fixture
def two_clusters() -> nx.Graph:
    """Two K3 cliques joined by a single bridge — clear community structure."""
    g = nx.Graph()
    g.add_weighted_edges_from([(1, 2, 5.0), (1, 3, 5.0), (2, 3, 5.0)])
    g.add_weighted_edges_from([(4, 5, 5.0), (4, 6, 5.0), (5, 6, 5.0)])
    g.add_edge(3, 4, weight=0.1)
    return g


@pytest.fixture
def random_graph() -> nx.Graph:
    """Erdos-Renyi graph — weak or no community structure expected."""
    return nx.erdos_renyi_graph(20, 0.5, seed=42)


class TestNullModelResult:
    def test_str_contains_significance_label(self, two_clusters):
        result = assess_community_significance(two_clusters, n_permutations=50, seed=42)
        assert "Q_observed" in str(result)
        assert "Q_null" in str(result)

    def test_returns_correct_type(self, two_clusters):
        result = assess_community_significance(two_clusters, n_permutations=50, seed=42)
        assert isinstance(result, NullModelResult)


class TestCommunitySignificance:
    def test_two_clusters_is_significant(self, two_clusters):
        result = assess_community_significance(two_clusters, n_permutations=200, seed=42)
        assert result.q_observed > result.q_null_mean
        assert result.significant

    def test_p_value_is_in_unit_interval(self, two_clusters):
        result = assess_community_significance(two_clusters, n_permutations=50, seed=42)
        assert 0.0 <= result.p_value <= 1.0

    def test_q_observed_is_in_valid_range(self, two_clusters):
        result = assess_community_significance(two_clusters, n_permutations=50, seed=42)
        assert -0.5 <= result.q_observed <= 1.0

    def test_n_permutations_recorded(self, two_clusters):
        result = assess_community_significance(two_clusters, n_permutations=77, seed=42)
        assert result.n_permutations == 77

    def test_custom_alpha(self, two_clusters):
        result = assess_community_significance(
            two_clusters, n_permutations=50, alpha=0.10, seed=42
        )
        assert result.alpha == 0.10


# ---------------------------------------------------------------------------
# Party-level label-permutation tests.
# Historical names: H2 (bench size × betweenness) and H3 (degree × betweenness).
# Kept as complementary evidence after the hypothesis reformulation.
# ---------------------------------------------------------------------------


def _make_graph(specs: dict[str, list[tuple[float, float]]]) -> ParliamentaryGraph:
    """Build a ParliamentaryGraph with preset per-deputy centralities.

    Args:
        specs: Mapping ``party_code -> [(weighted_degree, betweenness), ...]``.
            One deputy is created per tuple. Graph nodes are added (edges are
            irrelevant: the party aggregation reads the preset Deputy attributes
            while iterating the node set).

    Returns:
        A ready-to-aggregate :class:`ParliamentaryGraph`.
    """
    deputies: dict[int, Deputy] = {}
    next_id = 1
    for party, members in specs.items():
        for weighted_degree, betweenness in members:
            dep = Deputy(
                id=next_id,
                name=f"Dep {next_id}",
                party_code=party,
                state_code="XX",
                weighted_degree=weighted_degree,
                betweenness_centrality=betweenness,
            )
            deputies[next_id] = dep
            next_id += 1

    pg = ParliamentaryGraph(deputies=deputies, year=2024)
    pg.graph.add_nodes_from(deputies.keys())
    return pg


@pytest.fixture
def party_degree_association_graph() -> ParliamentaryGraph:
    """Five parties whose mean degree and mean betweenness rank identically.

    The association lives *at the party level*: party k has a higher mean
    weighted degree AND a higher mean betweenness, so the party-level Spearman
    rho is +1. Crucially, degree and betweenness overlap across parties at the
    individual level (each party mixes a diagonal deputy with two off-diagonal
    ones), so random label permutations genuinely scramble the party means —
    which is what makes the observed rho stand out as significant. If instead
    degree and betweenness were perfectly comonotonic per deputy, every random
    regrouping would also yield rho≈1 and nothing would be significant.
    """
    specs = {
        f"P{k}": [
            (k + 1.0, k + 1.0),  # diagonal
            (k + 1.0, k + 3.0),  # high betweenness, off-diagonal
            (k + 3.0, k + 1.0),  # high degree, off-diagonal
        ]
        for k in range(5)
    }
    return _make_graph(specs)


@pytest.fixture
def party_size_association_graph() -> ParliamentaryGraph:
    """Bench size correlates negatively with mean betweenness.

    Larger benches (more deputies) have lower betweenness — brokers sit in the
    small parties. Sizes 5..1 map to increasing betweenness.
    """
    specs = {}
    for k in range(5):  # party index 0..4
        size = 5 - k              # sizes: 5, 4, 3, 2, 1
        betweenness = 0.10 * (k + 1)  # increases as size decreases
        specs[f"P{k}"] = [(1.0, betweenness)] * size
    return _make_graph(specs)


class TestPermutationResult:
    def test_returns_correct_type(self, party_degree_association_graph):
        result = assess_label_association(
            party_degree_association_graph, party_degree_vs_betweenness_statistic, n_permutations=100
        )
        assert isinstance(result, PermutationResult)

    def test_str_reports_significance(self, party_degree_association_graph):
        result = assess_label_association(
            party_degree_association_graph, party_degree_vs_betweenness_statistic, n_permutations=100
        )
        assert "Label association" in str(result)

    def test_two_sided_flag_recorded(self, party_degree_association_graph):
        result = assess_label_association(
            party_degree_association_graph,
            party_degree_vs_betweenness_statistic,
            n_permutations=50,
            two_sided=False,
        )
        assert result.two_sided is False


class TestLabelsAreRestored:
    def test_party_codes_unchanged_after_test(self, party_degree_association_graph):
        before = {i: d.party_code for i, d in party_degree_association_graph.deputies.items()}
        assess_label_association(
            party_degree_association_graph, party_degree_vs_betweenness_statistic, n_permutations=100
        )
        after = {i: d.party_code for i, d in party_degree_association_graph.deputies.items()}
        assert before == after

    def test_labels_restored_even_when_statistic_raises(self, party_degree_association_graph):
        before = {i: d.party_code for i, d in party_degree_association_graph.deputies.items()}

        def boom(_pg):
            raise ValueError("statistic exploded")

        # The observed call happens first and will raise, but any partial
        # mutation must still be rolled back.
        with pytest.raises(ValueError):
            assess_label_association(party_degree_association_graph, boom, n_permutations=10)

        after = {i: d.party_code for i, d in party_degree_association_graph.deputies.items()}
        assert before == after


class TestPartyDegreeVsBetweenness:
    # Historical name: H3 (echo chambers). Kept as complementary evidence.
    def test_deliberate_association_is_significant(self, party_degree_association_graph):
        result = assess_label_association(
            party_degree_association_graph,
            party_degree_vs_betweenness_statistic,
            n_permutations=500,
            two_sided=True,
        )
        assert result.valid
        assert result.statistic_observed == pytest.approx(1.0)
        assert result.significant
        assert result.p_value < 0.05

    def test_random_labels_not_significant(self, party_degree_association_graph):
        # Reshuffle the real labels once with a fixed seed to obtain a graph
        # whose labels are independent of centrality: a typical draw from the
        # null, which should not be flagged significant.
        import random

        rng = random.Random(7)
        deps = [
            party_degree_association_graph.deputies[n]
            for n in party_degree_association_graph.graph.nodes()
        ]
        labels = [d.party_code for d in deps]
        rng.shuffle(labels)
        for dep, label in zip(deps, labels):
            dep.party_code = label

        result = assess_label_association(
            party_degree_association_graph,
            party_degree_vs_betweenness_statistic,
            n_permutations=500,
            two_sided=True,
        )
        assert result.valid
        assert not result.significant


class TestPartySizeVsBetweenness:
    # Historical name: H2 (broker parties). Kept as complementary evidence.
    def test_negative_association_one_sided_significant(self, party_size_association_graph):
        result = assess_label_association(
            party_size_association_graph,
            partial(party_size_vs_mean_betweenness_statistic, min_party_size=1),
            n_permutations=500,
            two_sided=False,
        )
        assert result.valid
        assert result.statistic_observed < 0
        assert result.significant


class TestSmallSampleGuard:
    def test_fewer_than_three_parties_is_inconclusive(self):
        specs = {
            "A": [(10.0, 0.5), (11.0, 0.4)],
            "B": [(1.0, 0.1), (2.0, 0.2)],
        }
        pg = _make_graph(specs)
        result = assess_label_association(
            pg, party_degree_vs_betweenness_statistic, n_permutations=100
        )
        assert result.valid is False
        assert result.significant is False
        assert result.n_permutations == 0
