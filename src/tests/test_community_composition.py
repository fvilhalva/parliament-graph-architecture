"""Tests for community party composition (PP2)."""

from core.algorithms.community_composition import (
    CommunityCompositionResult,
    assess_community_composition,
    assess_graph_community_composition,
)
from core.graph import ParliamentaryGraph
from models.deputy import Deputy


def _party_map(assignments: dict[int, str]) -> dict[int, str]:
    return dict(assignments)


class TestPureCommunities:
    """Each community is a single party -> communities ARE parties."""

    def test_single_party_communities(self):
        # Community 0 = all party A, community 1 = all party B.
        partition = {1: 0, 2: 0, 3: 0, 4: 1, 5: 1, 6: 1}
        node_party = {1: "A", 2: "A", 3: "A", 4: "B", 5: "B", 6: "B"}
        result = assess_community_composition(partition, node_party, min_size=3)

        assert isinstance(result, CommunityCompositionResult)
        assert result.num_communities == 2
        assert result.mean_purity == 1.0
        assert result.multiparty_fraction == 0.0
        assert result.coalition_fraction == 0.0
        assert result.verdict == "partidos"


class TestCoalitionCommunities:
    """Each community mixes many parties -> communities ARE coalitions."""

    def test_mixed_communities(self):
        # Two communities, each with 4 distinct parties (purity 0.25).
        partition = {i: (0 if i <= 4 else 1) for i in range(1, 9)}
        node_party = {
            1: "A", 2: "B", 3: "C", 4: "D",
            5: "E", 6: "F", 7: "G", 8: "H",
        }
        result = assess_community_composition(partition, node_party, min_size=3)

        assert result.num_communities == 2
        assert result.mean_purity == 0.25
        assert result.multiparty_fraction == 1.0
        assert result.coalition_fraction == 1.0
        assert result.verdict == "coalizões"


class TestMinSizeFilter:
    def test_small_communities_ignored(self):
        # Community 1 has only 2 members -> dropped at min_size=3.
        partition = {1: 0, 2: 0, 3: 0, 4: 1, 5: 1}
        node_party = {1: "A", 2: "A", 3: "A", 4: "B", 5: "B"}
        result = assess_community_composition(partition, node_party, min_size=3)
        assert result.num_communities == 1
        assert result.details[0]["dominant_party"] == "A"


class TestEmptyPartition:
    def test_empty_is_indeterminate(self):
        result = assess_community_composition({}, {}, min_size=3)
        assert result.num_communities == 0
        assert result.verdict == "indeterminado"


class TestGraphConvenience:
    def test_reads_party_from_deputies(self):
        deputies = {
            1: Deputy(1, "D1", "A", "XX"),
            2: Deputy(2, "D2", "A", "XX"),
            3: Deputy(3, "D3", "A", "XX"),
        }
        pg = ParliamentaryGraph(deputies=deputies, year=2024)
        pg.graph.add_nodes_from(deputies.keys())
        partition = {1: 0, 2: 0, 3: 0}

        result = assess_graph_community_composition(pg, partition, min_size=3)
        assert result.num_communities == 1
        assert result.mean_purity == 1.0
        assert result.verdict == "partidos"
