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

    def test_closeness_centrality_computed(self, example_graph):
        result = example_graph.compute_closeness_centrality()
        assert len(result) == 4
        assert all(0.0 <= dep.closeness_centrality <= 1.0 for dep in result)

    def test_eigenvector_centrality_computed(self, example_graph):
        result = example_graph.compute_eigenvector_centrality()
        assert len(result) == 4
        assert all(dep.eigenvector_centrality >= 0 for dep in result)
        assert sum(dep.eigenvector_centrality for dep in result) > 0

    def test_compute_all_centralities_populates_every_field(self, example_graph):
        result = example_graph.compute_all_centralities()
        assert len(result) == 4
        for deputy in result:
            assert deputy.weighted_degree > 0
            assert deputy.degree_centrality > 0
            # closeness/eigenvector/betweenness are >= 0 for any valid graph
            assert deputy.closeness_centrality >= 0
            assert deputy.eigenvector_centrality >= 0
            assert deputy.betweenness_centrality >= 0


class TestParliamentaryGraphCustomWeights:
    def test_custom_proposition_weights_change_edges(self):
        deputies = _build_deputies()
        propositions = _build_propositions()

        custom_weights = {"PL": 1, "PLP": 1, "PEC": 1}
        graph = ParliamentaryGraph(
            deputies=deputies,
            propositions=propositions,
            coauthorships=propositions,
            year=2025,
            proposition_weights=custom_weights,
        )
        graph.build()

        # P1 (PL, 3 authors): each pair gets 1 * 1/2 = 0.5
        # P2 (PLP, 2 authors): pair (1,2) gets 1 * 1/1 = 1.0
        # P3 (PEC, 2 authors): pair (3,4) gets 1 * 1/1 = 1.0
        assert graph.graph[1][2]["weight"] == pytest.approx(0.5 + 1.0)
        assert graph.graph[1][3]["weight"] == pytest.approx(0.5)
        assert graph.graph[2][3]["weight"] == pytest.approx(0.5)
        assert graph.graph[3][4]["weight"] == pytest.approx(1.0)

    def test_default_proposition_weights_when_none_given(self):
        from config.constants import PROPOSITION_TYPE_WEIGHTS

        graph = ParliamentaryGraph()
        assert graph.proposition_weights == PROPOSITION_TYPE_WEIGHTS
        # Defensive copy: mutating the instance attribute must not affect the constant.
        graph.proposition_weights["PL"] = 999
        assert PROPOSITION_TYPE_WEIGHTS["PL"] != 999


class TestDeputyIdAliases:
    def test_alias_collapses_into_canonical_id(self, monkeypatch):
        # Make alias 999 -> 1 so a coauthorship with [999, 2] becomes [1, 2].
        from config import constants
        from core import graph as graph_module
        from models.proposition import Proposition

        monkeypatch.setitem(graph_module.DEPUTY_ID_ALIASES, 999, 1)
        deputies = _build_deputies()
        propositions = [
            Proposition(id=10, year=2025, author_ids=[999, 2], proposition_type="PL"),
        ]
        graph = ParliamentaryGraph(deputies, propositions, propositions, year=2025)
        graph.build()
        # Edge should exist on the canonical IDs.
        assert graph.graph.has_edge(1, 2)
        assert 999 not in graph.graph.nodes

        # Cleanup the patched alias so other tests don't see it.
        graph_module.DEPUTY_ID_ALIASES.pop(999, None)


class TestUnknownDeputies:
    def test_build_marks_unknown_when_metadata_missing(self):
        from models.proposition import Proposition

        # Propositions reference IDs not present in `deputies`.
        propositions = [
            Proposition(id=1, year=2025, author_ids=[10, 20], proposition_type="PL"),
        ]
        graph = ParliamentaryGraph(
            deputies={},
            propositions=propositions,
            coauthorships=propositions,
            year=2025,
        )
        graph.build()
        assert graph.graph.nodes[10]["name"].startswith("Unknown")
        assert graph.graph.nodes[10]["party_code"] == "N/A"

    def test_centrality_skips_missing_deputies(self):
        from models.proposition import Proposition

        propositions = [
            Proposition(id=1, year=2025, author_ids=[10, 20], proposition_type="PL"),
        ]
        graph = ParliamentaryGraph(
            deputies={},
            propositions=propositions,
            coauthorships=propositions,
            year=2025,
        )
        graph.build()
        # No deputies registered -> all methods return empty lists (no crashes).
        assert graph.compute_degree_centrality() == []
        assert graph.compute_betweenness_centrality() == []
        assert graph.compute_closeness_centrality() == []
        assert graph.compute_eigenvector_centrality() == []


class TestPartyFilters:
    def test_filter_parties_by_degree_returns_ranking(self, example_graph):
        example_graph.compute_all_centralities()
        ranking = example_graph.filter_parties_by_degree()
        assert not ranking.empty
        assert list(ranking.columns) == ["party_code", "avg_weighted_degree", "num_deputies"]
        # Verify sorted descending
        values = list(ranking["avg_weighted_degree"])
        assert values == sorted(values, reverse=True)

    def test_filter_parties_by_betweenness_returns_ranking(self, example_graph):
        example_graph.compute_all_centralities()
        ranking = example_graph.filter_parties_by_betweenness()
        assert not ranking.empty
        assert list(ranking.columns) == ["party_code", "avg_betweenness", "num_deputies"]

    def test_filter_parties_respects_min_size(self, example_graph):
        example_graph.compute_all_centralities()
        ranking = example_graph.filter_parties_by_degree(min_party_size=99)
        assert ranking.empty


class TestSearchAndDisplay:
    def test_search_by_id(self, example_graph):
        results = example_graph.search_deputies("1")
        assert len(results) == 1
        assert results[0].id == 1

    def test_search_by_name(self, example_graph):
        results = example_graph.search_deputies("A")
        assert any(dep.name == "A" for dep in results)

    def test_search_missing(self, example_graph):
        assert example_graph.search_deputies("9999") == []
        assert example_graph.search_deputies("ZZZZ") == []

    def test_display_deputy_profile_runs(self, example_graph, caplog):
        # Just ensure no exception and that the logger emits something.
        example_graph.display_deputy_profile("A")
        example_graph.display_deputy_profile("__missing__")


class TestStructuralAnalysis:
    def test_advanced_structural_analysis_runs(self, example_graph):
        # Should run without raising; logs articulation/density/components.
        example_graph.advanced_structural_analysis()

    def test_identify_critical_deputies_missing_query(self, example_graph):
        example_graph.identify_critical_deputies("__nope__")

    def test_identify_critical_deputies_existing(self, example_graph):
        example_graph.identify_critical_deputies("A")

    def test_identify_critical_deputies_fragments_graph(self):
        # Graph in which removing the bridging node isolates a subgroup.
        from models.deputy import Deputy
        from models.proposition import Proposition

        deputies = {
            i: Deputy(id=i, name=str(i), party_code="X", state_code="X") for i in range(1, 6)
        }
        # Star: 1 connects to 2,3; 1 also connects to 4,5 via another prop
        propositions = [
            Proposition(id=1, year=2025, author_ids=[1, 2], proposition_type="PL"),
            Proposition(id=2, year=2025, author_ids=[1, 3], proposition_type="PL"),
            Proposition(id=3, year=2025, author_ids=[1, 4], proposition_type="PL"),
            Proposition(id=4, year=2025, author_ids=[4, 5], proposition_type="PL"),
        ]
        graph = ParliamentaryGraph(deputies, propositions, propositions, year=2025)
        graph.build()
        # Removing deputy 1 should fragment the network.
        graph.identify_critical_deputies("1")
