"""Tests for the ParliamentaryGraph class (core)."""

import pytest  # type: ignore

from core import ParliamentaryGraph
from models.deputy import Deputy
from models.proposition import Proposition


def _build_deputies() -> dict[int, Deputy]:
    return {
        1: Deputy(id=1, name="A", party_code="PT", state_code="SP"),
        2: Deputy(id=2, name="B", party_code="PSB", state_code="RJ"),
        3: Deputy(id=3, name="C", party_code="MDB", state_code="MG"),
        4: Deputy(id=4, name="D", party_code="UNI", state_code="BA"),
    }


def _build_propositions() -> list[Proposition]:
    # Deterministic pattern for weight validation:
    # P1 (PL): [1,2,3] -> (1,2),(1,3),(2,3) += 10
    # P2 (PLP): [1,2]   -> (1,2) += 5
    # P3 (PEC): [3,4]   -> (3,4) += 1
    return [
        Proposition(id=100, year=2025, author_ids=[1, 2, 3], proposition_type="PL"),
        Proposition(id=101, year=2025, author_ids=[1, 2], proposition_type="PLP"),
        Proposition(id=102, year=2025, author_ids=[3, 4], proposition_type="PEC"),
    ]


@pytest.fixture
def example_graph() -> ParliamentaryGraph:
    deputies = _build_deputies()
    propositions = _build_propositions()
    graph = ParliamentaryGraph(
        deputies=deputies,
        propositions=propositions,
        coauthorships=propositions,
        year=2025,
    )
    graph.build()
    return graph


class TestParliamentaryGraphStructure:
    def test_create_empty_graph(self):
        graph = ParliamentaryGraph()
        assert graph.graph.number_of_nodes() == 0
        assert graph.graph.number_of_edges() == 0

    def test_build_graph_with_nodes_and_edges(self, example_graph):
        assert example_graph.graph.number_of_nodes() == 4
        assert example_graph.graph.number_of_edges() == 4

    def test_no_self_loops(self, example_graph):
        for u, v in example_graph.graph.edges():
            assert u != v


class TestParliamentaryGraphWeights:
    def test_weight_aggregation_by_pair(self, example_graph):
        assert example_graph.graph[1][2]["weight"] == pytest.approx(10/2 + 5/1)
        assert example_graph.graph[1][3]["weight"] == pytest.approx(10/2)
        assert example_graph.graph[2][3]["weight"] == pytest.approx(10/2)
        assert example_graph.graph[3][4]["weight"] == pytest.approx(1/1)

    def test_normalization_by_author_count(self, example_graph):
        # With 3 authors in P1: normalization factor = 1/(3-1) = 0.5
        # With 2 authors in P2: normalization factor = 1/(2-1) = 1.0
        # P1 (PL): 10 * 0.5 = 5 per edge
        # P2 (PLP): 5 * 1.0 = 5 per edge
        assert example_graph.graph[1][2]["weight"] == pytest.approx(5 + 5)


class TestParliamentaryGraphNodeAttributes:
    def test_node_attributes_populated(self, example_graph):
        node_data = example_graph.graph.nodes[1]
        assert node_data["name"] == "A"
        assert node_data["party_code"] == "PT"
        assert node_data["state_code"] == "SP"

    def test_degree_centrality_normalized(self, example_graph):
        result = example_graph.compute_degree_centrality()
        assert len(result) == 4
        total = sum(dep.degree_centrality for dep in result)
        assert total == pytest.approx(1.0)
        top = max(result, key=lambda dep: dep.weighted_degree)
        assert top.id == 1

    def test_betweenness_centrality_computed(self, example_graph):
        result = example_graph.compute_betweenness_centrality()
        assert len(result) == 4
        assert all(dep.betweenness_centrality >= 0 for dep in result)
