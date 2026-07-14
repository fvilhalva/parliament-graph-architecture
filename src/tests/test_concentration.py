"""Tests for structural concentration of influence (PP1)."""

import pytest

from core.algorithms.concentration import (
    ConcentrationResult,
    assess_concentration,
    assess_graph_concentration,
    gini,
    top_share,
)
from core.graph import ParliamentaryGraph
from models.deputy import Deputy


class TestGini:
    def test_perfect_equality_is_zero(self):
        assert gini([5.0, 5.0, 5.0, 5.0]) == pytest.approx(0.0)

    def test_empty_is_zero(self):
        assert gini([]) == 0.0

    def test_all_zero_is_zero(self):
        assert gini([0.0, 0.0, 0.0]) == 0.0

    def test_maximal_inequality_approaches_one(self):
        # One holds everything: Gini -> (n-1)/n.
        n = 100
        values = [0.0] * (n - 1) + [1.0]
        assert gini(values) == pytest.approx((n - 1) / n, abs=1e-9)

    def test_concentrated_exceeds_uniform(self):
        uniform = gini([10, 10, 10, 10, 10])
        skewed = gini([1, 1, 1, 1, 96])
        assert skewed > uniform

    def test_negative_values_clamped(self):
        # Negatives clamped to zero -> same as replacing them with 0.
        assert gini([-3.0, 0.0, 0.0]) == 0.0


class TestTopShare:
    def test_uniform_top_fraction_matches_fraction(self):
        values = [1.0] * 100
        assert top_share(values, 0.10) == pytest.approx(0.10)

    def test_concentrated_top_share_is_high(self):
        values = [0.0] * 95 + [1.0] * 5
        # Top 5% holds all of it.
        assert top_share(values, 0.05) == pytest.approx(1.0)

    def test_empty_is_zero(self):
        assert top_share([], 0.1) == 0.0

    def test_at_least_one_element_counted(self):
        # ceil(0.01 * 3) = 1, so top slice is the single largest value.
        assert top_share([1.0, 2.0, 7.0], 0.01) == pytest.approx(0.7)


class TestAssessConcentration:
    def test_structure_and_type(self):
        result = assess_concentration([1, 2, 3, 4], "betweenness_centrality")
        assert isinstance(result, ConcentrationResult)
        assert result.metric == "betweenness_centrality"
        assert result.n == 4
        assert set(result.top_share.keys()) == {0.05, 0.10, 0.20}

    def test_str_is_readable(self):
        result = assess_concentration([1, 2, 3, 4], "weighted_degree")
        assert "Gini" in str(result)


class TestAssessGraphConcentration:
    def test_reads_deputy_attribute(self):
        deputies = {
            i: Deputy(i, f"D{i}", "P", "XX", weighted_degree=float(i), betweenness_centrality=0.0)
            for i in range(1, 6)
        }
        pg = ParliamentaryGraph(deputies=deputies, year=2024)
        pg.graph.add_nodes_from(deputies.keys())

        result = assess_graph_concentration(pg, metric="weighted_degree")
        assert result.n == 5
        assert result.gini > 0.0  # values 1..5 are unequal
