"""Tests for the null-model community significance validation."""

import networkx as nx
import pytest

from core.algorithms.validation import NullModelResult, assess_community_significance


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
