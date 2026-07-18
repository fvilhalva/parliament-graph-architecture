"""Tests for the relatorship correlation (PP3)."""

import math

import pytest

from core.algorithms.relatorship import RelatorshipResult, assess_graph_relatorship
from core.graph import ParliamentaryGraph
from models.deputy import Deputy
from models.proposition import Proposition


def _graph_with_deputies(deputies_specs, off_graph_relator_ids=()):
    """Build a ParliamentaryGraph containing the given deputies as isolated nodes.

    ``deputies_specs`` is a list of tuples ``(id, betweenness, relatorship_count)``.
    ``off_graph_relator_ids`` seeds the private ``_off_graph_relators`` attribute.
    """
    deputies = {}
    for dep_id, betweenness, rel_count in deputies_specs:
        deputies[dep_id] = Deputy(
            id=dep_id,
            name=f"Dep {dep_id}",
            party_code="P",
            state_code="XX",
            betweenness_centrality=betweenness,
            relatorship_count=rel_count,
        )
    pg = ParliamentaryGraph(deputies=deputies, year=2024)
    pg.graph.add_nodes_from(deputies.keys())
    pg._off_graph_relators = set(off_graph_relator_ids)  # type: ignore[attr-defined]
    return pg


class TestRelatorshipResultType:
    def test_returns_result_dataclass(self):
        pg = _graph_with_deputies(
            [(i, i * 0.1, i) for i in range(1, 6)]
        )
        result = assess_graph_relatorship(pg)
        assert isinstance(result, RelatorshipResult)

    def test_result_has_metric_name(self):
        pg = _graph_with_deputies(
            [(i, i * 0.1, i) for i in range(1, 6)]
        )
        result = assess_graph_relatorship(pg, metric="betweenness_centrality")
        assert result.metric == "betweenness_centrality"

    def test_str_reports_significance(self):
        pg = _graph_with_deputies(
            [(i, i * 0.1, i) for i in range(1, 6)]
        )
        result = assess_graph_relatorship(pg)
        assert "Relatorship" in str(result)


class TestRelatorshipCorrelation:
    def test_perfect_positive_correlation(self):
        # Betweenness and relatorship_count rank identically.
        pg = _graph_with_deputies(
            [(i, i * 0.1, i) for i in range(1, 11)]
        )
        result = assess_graph_relatorship(pg)
        assert result.valid
        assert result.spearman_rho == pytest.approx(1.0)
        assert result.significant
        assert result.p_value < 0.05

    def test_perfect_negative_correlation(self):
        # Highest betweenness has zero relatorships.
        pg = _graph_with_deputies(
            [(i, i * 0.1, 11 - i) for i in range(1, 11)]
        )
        result = assess_graph_relatorship(pg)
        assert result.valid
        assert result.spearman_rho == pytest.approx(-1.0)
        assert result.significant

    def test_no_correlation_not_significant(self):
        # 10 deputies whose betweenness and relatorship_count are, by rank,
        # essentially uncorrelated (Spearman rho ≈ 0). Enough samples that a
        # weak association is not incidentally flagged as significant.
        specs = [
            (1, 0.10, 3),
            (2, 0.20, 1),
            (3, 0.30, 4),
            (4, 0.40, 2),
            (5, 0.50, 5),
            (6, 0.60, 1),
            (7, 0.70, 3),
            (8, 0.80, 4),
            (9, 0.90, 2),
            (10, 1.00, 5),
        ]
        pg = _graph_with_deputies(specs)
        result = assess_graph_relatorship(pg)
        assert result.valid
        assert abs(result.spearman_rho) < 0.6  # weak association at most
        assert not result.significant


class TestSampleCounts:
    def test_n_matches_graph_nodes(self):
        pg = _graph_with_deputies(
            [(i, i * 0.1, i) for i in range(1, 8)]
        )
        result = assess_graph_relatorship(pg)
        assert result.n == 7

    def test_n_with_relatorship_counts_only_positive(self):
        specs = [(1, 0.1, 0), (2, 0.2, 0), (3, 0.3, 5), (4, 0.4, 2)]
        pg = _graph_with_deputies(specs)
        result = assess_graph_relatorship(pg)
        assert result.n == 4
        assert result.n_with_relatorship == 2

    def test_off_graph_relators_reported(self):
        pg = _graph_with_deputies(
            [(i, i * 0.1, i) for i in range(1, 6)],
            off_graph_relator_ids=[9001, 9002, 9003],
        )
        result = assess_graph_relatorship(pg)
        assert result.n_off_graph_relators == 3


class TestEdgeCases:
    def test_all_zero_relatorships_marks_invalid(self):
        # No relator picked from graph nodes -> constant vector -> NaN rho.
        pg = _graph_with_deputies([(i, i * 0.1, 0) for i in range(1, 6)])
        result = assess_graph_relatorship(pg)
        assert result.valid is False
        assert math.isnan(result.spearman_rho)
        assert result.significant is False

    def test_constant_metric_marks_invalid(self):
        pg = _graph_with_deputies([(i, 0.42, i) for i in range(1, 6)])
        result = assess_graph_relatorship(pg)
        assert result.valid is False

    def test_empty_graph_marks_invalid(self):
        pg = ParliamentaryGraph(deputies={}, year=2024)
        result = assess_graph_relatorship(pg)
        assert result.valid is False
        assert result.n == 0


class TestGraphIntegration:
    """Verifies assign_relatorship_counts + assess_graph_relatorship end-to-end."""

    def test_end_to_end_populates_correlation(self):
        deputies = {
            i: Deputy(
                id=i,
                name=f"Dep {i}",
                party_code="P",
                state_code="XX",
                betweenness_centrality=i * 0.1,
            )
            for i in range(1, 6)
        }
        propositions = [
            Proposition(id=100 + i, year=2024, author_ids=[i], proposition_type="PL", relator_id=i)
            for i in range(1, 6)
        ]
        # Add extra relatorships so counts spread: dep 5 relates 3 times, dep 4 twice, dep 3 once.
        propositions.extend([
            Proposition(id=200, year=2024, author_ids=[5], proposition_type="PL", relator_id=5),
            Proposition(id=201, year=2024, author_ids=[5], proposition_type="PL", relator_id=5),
            Proposition(id=202, year=2024, author_ids=[4], proposition_type="PL", relator_id=4),
        ])

        pg = ParliamentaryGraph(deputies=deputies, propositions=propositions, year=2024)
        pg.graph.add_nodes_from(deputies.keys())

        pg.assign_relatorship_counts(propositions)
        assert deputies[5].relatorship_count == 3
        assert deputies[4].relatorship_count == 2
        assert deputies[1].relatorship_count == 1

        result = assess_graph_relatorship(pg)
        assert result.valid
        assert result.n_with_relatorship == 5

    def test_off_graph_relator_not_counted_but_reported(self):
        # Deputy 99 is not in the graph but is designated as relator.
        deputies = {
            i: Deputy(id=i, name=f"Dep {i}", party_code="P", state_code="XX", betweenness_centrality=i * 0.1)
            for i in range(1, 4)
        }
        propositions = [
            Proposition(id=1, year=2024, author_ids=[1], proposition_type="PL", relator_id=99),
            Proposition(id=2, year=2024, author_ids=[2], proposition_type="PL", relator_id=1),
        ]
        pg = ParliamentaryGraph(deputies=deputies, year=2024)
        pg.graph.add_nodes_from(deputies.keys())
        pg.assign_relatorship_counts(propositions)

        assert deputies[1].relatorship_count == 1
        assert deputies[2].relatorship_count == 0
        assert pg.off_graph_relator_count == 1

    def test_reset_between_calls(self):
        deputies = {1: Deputy(id=1, name="A", party_code="P", state_code="XX")}
        propositions = [
            Proposition(id=1, year=2024, author_ids=[1], proposition_type="PL", relator_id=1),
        ]
        pg = ParliamentaryGraph(deputies=deputies, year=2024)
        pg.graph.add_nodes_from([1])
        pg.assign_relatorship_counts(propositions)
        assert deputies[1].relatorship_count == 1
        pg.assign_relatorship_counts(propositions)
        # Not doubled — reset first, then aggregated.
        assert deputies[1].relatorship_count == 1
