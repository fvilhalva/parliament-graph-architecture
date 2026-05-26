"""Tests for community detection helpers in ``core.algorithms.community_detection``."""

import networkx as nx
import pytest

from core.algorithms.community_detection import (
    CommunityDetector,
    compare_community_methods,
    detect_communities,
)


@pytest.fixture
def empty_graph() -> nx.Graph:
    return nx.Graph()


@pytest.fixture
def two_clusters() -> nx.Graph:
    """Two K3 cliques connected by a single bridge edge."""
    graph = nx.Graph()
    # Clique A: {1, 2, 3}
    graph.add_weighted_edges_from(
        [
            (1, 2, 5.0),
            (1, 3, 5.0),
            (2, 3, 5.0),
        ]
    )
    # Clique B: {4, 5, 6}
    graph.add_weighted_edges_from(
        [
            (4, 5, 5.0),
            (4, 6, 5.0),
            (5, 6, 5.0),
        ]
    )
    # Bridge
    graph.add_edge(3, 4, weight=0.1)
    return graph


class TestCommunityDetectorEmptyGraph:
    def test_louvain_returns_empty(self, empty_graph):
        detector = CommunityDetector()
        assert detector.detect_louvain(empty_graph) == {}

    def test_label_propagation_returns_empty(self, empty_graph):
        detector = CommunityDetector()
        assert detector.detect_label_propagation(empty_graph) == {}

    def test_spectral_returns_empty(self, empty_graph):
        detector = CommunityDetector()
        assert detector.detect_spectral(empty_graph) == {}

    def test_modularity_empty_returns_zero(self, empty_graph):
        detector = CommunityDetector()
        assert detector.calculate_modularity(empty_graph, {}) == 0.0

    def test_modularity_empty_partition_returns_zero(self, two_clusters):
        detector = CommunityDetector()
        assert detector.calculate_modularity(two_clusters, {}) == 0.0


class TestCommunityDetectorTwoClusters:
    def test_louvain_finds_two_communities(self, two_clusters):
        detector = CommunityDetector()
        partition = detector.detect_louvain(two_clusters)
        # Each clique should land in its own community.
        assert partition[1] == partition[2] == partition[3]
        assert partition[4] == partition[5] == partition[6]
        assert partition[1] != partition[4]

    def test_louvain_modularity_above_threshold(self, two_clusters):
        detector = CommunityDetector()
        partition = detector.detect_louvain(two_clusters)
        modularity = detector.calculate_modularity(two_clusters, partition)
        assert modularity > 0.3

    def test_modularity_is_in_valid_range(self, two_clusters):
        detector = CommunityDetector()
        partition = detector.detect_louvain(two_clusters)
        modularity = detector.calculate_modularity(two_clusters, partition)
        assert -0.5 <= modularity <= 1.0

    def test_label_propagation_returns_partition(self, two_clusters):
        detector = CommunityDetector()
        partition = detector.detect_label_propagation(two_clusters)
        assert set(partition.keys()) == set(two_clusters.nodes())

    def test_spectral_returns_partition(self, two_clusters):
        detector = CommunityDetector()
        partition = detector.detect_spectral(two_clusters, n_clusters=2)
        assert set(partition.keys()) == set(two_clusters.nodes())
        assert set(partition.values()) <= {0, 1}


class TestDetectCommunitiesFacade:
    def test_louvain_method(self, two_clusters):
        partition = detect_communities(two_clusters, method="louvain")
        assert set(partition.keys()) == set(two_clusters.nodes())

    def test_label_propagation_method(self, two_clusters):
        partition = detect_communities(two_clusters, method="label_propagation")
        assert set(partition.keys()) == set(two_clusters.nodes())

    def test_spectral_method(self, two_clusters):
        partition = detect_communities(two_clusters, method="spectral", n_clusters=2)
        assert set(partition.keys()) == set(two_clusters.nodes())

    def test_unknown_method_raises(self, two_clusters):
        with pytest.raises(ValueError):
            detect_communities(two_clusters, method="unknown")


class TestCompareCommunityMethods:
    def test_returns_modularity_and_count_per_method(self, two_clusters):
        report = compare_community_methods(two_clusters)
        assert set(report.keys()) == {"louvain", "label_propagation"}
        for method, summary in report.items():
            assert "modularity" in summary
            assert "num_communities" in summary
            assert -0.5 <= summary["modularity"] <= 1.0
            assert summary["num_communities"] >= 1

    def test_empty_graph_reports_zero(self, empty_graph):
        report = compare_community_methods(empty_graph)
        for summary in report.values():
            assert summary["modularity"] == 0.0
            assert summary["num_communities"] == 0
