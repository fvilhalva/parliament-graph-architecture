"""Tests for centrality helpers in ``core.algorithms.metrics``."""

import networkx as nx
import pytest

from core.algorithms.metrics import (
    calculate_betweenness_centrality,
    calculate_closeness_centrality,
    calculate_degree_centrality,
    calculate_eigenvector_centrality,
)


@pytest.fixture
def path_graph() -> nx.Graph:
    """A path 1 - 2 - 3 - 4 used for deterministic centrality checks."""
    graph = nx.Graph()
    graph.add_weighted_edges_from(
        [
            (1, 2, 1.0),
            (2, 3, 1.0),
            (3, 4, 1.0),
        ]
    )
    return graph


@pytest.fixture
def star_graph() -> nx.Graph:
    """A star with node 1 at the centre and three leaves."""
    graph = nx.Graph()
    graph.add_weighted_edges_from(
        [
            (1, 2, 1.0),
            (1, 3, 1.0),
            (1, 4, 1.0),
        ]
    )
    return graph


class TestDegreeCentrality:
    def test_returns_value_per_node(self, path_graph):
        result = calculate_degree_centrality(path_graph)
        assert set(result.keys()) == {1, 2, 3, 4}

    def test_star_centre_has_highest_value(self, star_graph):
        result = calculate_degree_centrality(star_graph)
        assert result[1] == max(result.values())

    def test_empty_graph(self):
        assert calculate_degree_centrality(nx.Graph()) == {}


class TestBetweennessCentrality:
    def test_path_middle_nodes_have_higher_betweenness(self, path_graph):
        result = calculate_betweenness_centrality(path_graph)
        assert result[2] > result[1]
        assert result[3] > result[4]

    def test_endpoints_have_zero_betweenness(self, path_graph):
        result = calculate_betweenness_centrality(path_graph)
        assert result[1] == pytest.approx(0)
        assert result[4] == pytest.approx(0)


class TestClosenessCentrality:
    def test_star_centre_has_highest_closeness(self, star_graph):
        result = calculate_closeness_centrality(star_graph)
        assert result[1] == max(result.values())

    def test_values_are_in_unit_interval(self, path_graph):
        result = calculate_closeness_centrality(path_graph)
        for value in result.values():
            assert 0.0 <= value <= 1.0


class TestEigenvectorCentrality:
    def test_star_centre_has_highest_eigenvector(self, star_graph):
        result = calculate_eigenvector_centrality(star_graph)
        assert result[1] == max(result.values())

    def test_handles_disconnected_graph(self):
        graph = nx.Graph()
        graph.add_weighted_edges_from(
            [
                (1, 2, 1.0),
                (3, 4, 1.0),
            ]
        )
        # Should not raise: fallback to the NumPy implementation is exercised here.
        result = calculate_eigenvector_centrality(graph, max_iter=2)
        assert set(result.keys()) == {1, 2, 3, 4}

    def test_empty_graph(self):
        assert calculate_eigenvector_centrality(nx.Graph(), max_iter=2) == {}
