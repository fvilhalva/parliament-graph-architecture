"""Integrity tests for the real datasets produced by the pipeline.

These tests load the actual CSV and GEXF files generated under ``data/``
and validate that:
  - Files exist, are well-formed, and contain the expected columns/types
  - Network metrics are within plausible ranges (density, components, etc.)
  - Community structure is statistically meaningful (Q above threshold)
  - Centrality values respect their mathematical bounds

If the dataset for a given year is missing (pipeline not yet run for it),
the corresponding tests are skipped — they do not fail. This lets the
suite run safely in CI or on a fresh checkout while still catching real
data regressions whenever the pipeline has produced output.

Run only these tests:
    pytest src/tests/test_dataset_integrity.py -v

Run a single year:
    pytest src/tests/test_dataset_integrity.py -v -k 2025
"""
from __future__ import annotations

from pathlib import Path

import networkx as nx  # type: ignore
import pandas as pd  # type: ignore
import pytest  # type: ignore

# ── paths ──────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parents[2]
METRICS_DIR = BASE_DIR / "data" / "metricas"
GEXF_DIR = BASE_DIR / "data" / "gexf"

YEARS = [2022, 2023, 2024, 2025]

# Expected columns in the deputy metrics CSV
EXPECTED_CSV_COLUMNS = {
    "id_deputado",
    "nome",
    "sigla_partido",
    "sigla_uf",
    "weighted_degree",
    "degree_centrality",
    "betweenness_centrality",
    "closeness_centrality",
    "eigenvector_centrality",
}

# Sanity thresholds for the parliamentary network
MIN_NODES = 100          # below this the year clearly failed extraction
MAX_DENSITY = 0.50       # density above 50% means the max_authors filter failed
MIN_MODULARITY = 0.30    # accepted lower bound for "meaningful" community structure
MIN_LARGEST_COMPONENT_RATIO = 0.50  # principal component must dominate


# ── helpers ────────────────────────────────────────────────────────────────


def _csv_path(year: int) -> Path:
    return METRICS_DIR / f"deputados_metricas_{year}.csv"


def _gexf_path(year: int) -> Path:
    return GEXF_DIR / f"chamber_graph_{year}.gexf"


def _skip_if_missing(*paths: Path) -> None:
    """Skip the test gracefully when the pipeline hasn't produced the file."""
    missing = [p for p in paths if not p.exists()]
    if missing:
        pytest.skip(f"Dataset not generated yet: {', '.join(str(p) for p in missing)}")


# ── CSV integrity ──────────────────────────────────────────────────────────


@pytest.mark.parametrize("year", YEARS)
class TestDeputyMetricsCSV:
    """Schema and value-range validation for ``deputados_metricas_{year}.csv``."""

    def test_csv_exists_and_not_empty(self, year: int) -> None:
        path = _csv_path(year)
        _skip_if_missing(path)
        df = pd.read_csv(path)
        assert len(df) > 0, f"{path.name} is empty"

    def test_csv_has_required_columns(self, year: int) -> None:
        path = _csv_path(year)
        _skip_if_missing(path)
        df = pd.read_csv(path)
        missing = EXPECTED_CSV_COLUMNS - set(df.columns)
        assert not missing, f"{path.name} missing columns: {missing}"

    def test_deputy_ids_are_unique(self, year: int) -> None:
        path = _csv_path(year)
        _skip_if_missing(path)
        df = pd.read_csv(path)
        assert df["id_deputado"].is_unique, "Duplicate deputy IDs in CSV"

    def test_no_null_critical_fields(self, year: int) -> None:
        path = _csv_path(year)
        _skip_if_missing(path)
        df = pd.read_csv(path)
        for col in ["id_deputado", "nome", "sigla_partido"]:
            assert df[col].notna().all(), f"Nulls found in column '{col}'"

    def test_centrality_values_in_valid_range(self, year: int) -> None:
        """All normalized centralities must lie in [0, 1]."""
        path = _csv_path(year)
        _skip_if_missing(path)
        df = pd.read_csv(path)
        for col in [
            "degree_centrality",
            "betweenness_centrality",
            "closeness_centrality",
            "eigenvector_centrality",
        ]:
            assert (df[col] >= 0).all(), f"Negative values in '{col}'"
            assert (df[col] <= 1.0 + 1e-9).all(), f"Values > 1 in '{col}'"

    def test_weighted_degree_non_negative(self, year: int) -> None:
        path = _csv_path(year)
        _skip_if_missing(path)
        df = pd.read_csv(path)
        assert (df["weighted_degree"] >= 0).all(), "Negative weighted_degree found"

    def test_party_codes_non_empty(self, year: int) -> None:
        path = _csv_path(year)
        _skip_if_missing(path)
        df = pd.read_csv(path)
        assert (df["sigla_partido"].astype(str).str.len() > 0).all(), \
            "Empty party codes found"


# ── GEXF / graph integrity ─────────────────────────────────────────────────


@pytest.mark.parametrize("year", YEARS)
class TestGraphGEXF:
    """Structural validation for ``chamber_graph_{year}.gexf``."""

    def test_gexf_exists_and_loadable(self, year: int) -> None:
        path = _gexf_path(year)
        _skip_if_missing(path)
        graph = nx.read_gexf(path)
        assert graph is not None

    def test_graph_has_nodes(self, year: int) -> None:
        path = _gexf_path(year)
        _skip_if_missing(path)
        graph = nx.read_gexf(path)
        assert graph.number_of_nodes() >= MIN_NODES, (
            f"Only {graph.number_of_nodes()} nodes — extraction likely failed"
        )

    def test_graph_has_edges(self, year: int) -> None:
        path = _gexf_path(year)
        _skip_if_missing(path)
        graph = nx.read_gexf(path)
        assert graph.number_of_edges() > 0, "Graph has no edges"

    def test_density_within_plausible_range(self, year: int) -> None:
        """Density above 50% indicates the max_authors filter failed."""
        path = _gexf_path(year)
        _skip_if_missing(path)
        graph = nx.read_gexf(path)
        density = nx.density(graph)
        assert 0 < density < MAX_DENSITY, (
            f"Density {density:.4f} out of plausible range "
            f"(expected 0 < d < {MAX_DENSITY})"
        )

    def test_edge_weights_positive(self, year: int) -> None:
        path = _gexf_path(year)
        _skip_if_missing(path)
        graph = nx.read_gexf(path)
        weights = [d.get("weight", 0) for _, _, d in graph.edges(data=True)]
        assert all(w > 0 for w in weights), "Non-positive edge weight found"

    def test_largest_component_dominates(self, year: int) -> None:
        """At least 50% of nodes must lie in the principal component."""
        path = _gexf_path(year)
        _skip_if_missing(path)
        graph = nx.read_gexf(path)
        components = (
            nx.weakly_connected_components(graph)
            if graph.is_directed()
            else nx.connected_components(graph)
        )
        largest = max((len(c) for c in components), default=0)
        ratio = largest / graph.number_of_nodes()
        assert ratio >= MIN_LARGEST_COMPONENT_RATIO, (
            f"Largest component covers only {ratio:.1%} of nodes "
            f"(expected ≥ {MIN_LARGEST_COMPONENT_RATIO:.0%})"
        )


# ── Community structure (cross-file: GEXF + Louvain) ───────────────────────


@pytest.mark.parametrize("year", YEARS)
class TestCommunityStructure:
    """Validates that detected communities exceed the random-graph threshold."""

    def test_modularity_above_threshold(self, year: int) -> None:
        """Louvain Q must exceed 0.3 — the conventional 'meaningful' floor."""
        path = _gexf_path(year)
        _skip_if_missing(path)

        # Import lazily so test collection doesn't fail if the module path
        # changes during refactoring.
        from core.algorithms.community_detection import CommunityDetector

        graph = nx.read_gexf(path)
        detector = CommunityDetector()
        partition = detector.detect_louvain(graph, seed=42)
        q = detector.calculate_modularity(graph, partition)

        assert q >= MIN_MODULARITY, (
            f"Modularity {q:.4f} below threshold {MIN_MODULARITY} — "
            f"community structure may be artefactual"
        )

    def test_more_than_one_community(self, year: int) -> None:
        """A meaningful partition must yield ≥ 2 communities."""
        path = _gexf_path(year)
        _skip_if_missing(path)

        from core.algorithms.community_detection import CommunityDetector

        graph = nx.read_gexf(path)
        detector = CommunityDetector()
        partition = detector.detect_louvain(graph, seed=42)
        n_communities = len(set(partition.values()))

        assert n_communities >= 2, (
            f"Only {n_communities} community detected — "
            f"partition is degenerate"
        )


# ── Cross-file coherence (CSV ↔ GEXF) ──────────────────────────────────────


@pytest.mark.parametrize("year", YEARS)
class TestCsvGexfCoherence:
    """The CSV must be consistent with the GEXF graph for the same year."""

    def test_csv_deputies_cover_graph_nodes(self, year: int) -> None:
        """Every node in the graph must have a row in the metrics CSV."""
        csv_path = _csv_path(year)
        gexf_path = _gexf_path(year)
        _skip_if_missing(csv_path, gexf_path)

        df = pd.read_csv(csv_path)
        graph = nx.read_gexf(gexf_path)

        csv_ids = set(df["id_deputado"].astype(str))
        # GEXF node IDs are strings; the CSV's id_deputado is numeric.
        graph_ids = {str(n) for n in graph.nodes()}

        missing_in_csv = graph_ids - csv_ids
        assert not missing_in_csv, (
            f"{len(missing_in_csv)} graph nodes have no row in CSV "
            f"(sample: {list(missing_in_csv)[:5]})"
        )
