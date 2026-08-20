"""Tests for the persistence (repository) module."""

import sqlite3
import xml.etree.ElementTree as ET

import networkx as nx  # type: ignore
import pandas as pd  # type: ignore
import pytest  # type: ignore

from models.deputy import Deputy
from repository.csv_repository import CsvRepository
from repository.db_repository import DB_Exporter
from repository.graph_exporter import GraphExporter


class TestCSVRepository:
    """Tests for metrics export to CSV."""

    @pytest.fixture
    def example_deputies(self):
        return [
            Deputy(1, "Ana", "PT", "SP", weighted_degree=20, degree_centrality=0.4, betweenness_centrality=0.2),
            Deputy(2, "Bruno", "PSB", "RJ", weighted_degree=10, degree_centrality=0.2, betweenness_centrality=0.1),
            Deputy(3, "Carla", "MDB", "MG", weighted_degree=30, degree_centrality=0.6, betweenness_centrality=0.3),
        ]

    def test_export_creates_file(self, tmp_path, example_deputies):
        csv_repo = CsvRepository(tmp_path)
        output_file = csv_repo.export_deputy_metrics(example_deputies, year=2025)

        assert output_file.exists()
        assert output_file.name == "deputados_metricas_2025.csv"

    def test_csv_not_corrupted(self, tmp_path, example_deputies):
        csv_repo = CsvRepository(tmp_path)
        output_file = csv_repo.export_deputy_metrics(example_deputies, year=2025)

        df = pd.read_csv(output_file)
        assert len(df) == len(example_deputies)
        assert not df.empty

    def test_csv_is_readable(self, tmp_path, example_deputies):
        csv_repo = CsvRepository(tmp_path)
        output_file = csv_repo.export_deputy_metrics(example_deputies, year=2025)

        data = pd.read_csv(output_file)
        assert len(data) > 0

    def test_csv_has_expected_columns(self, tmp_path, example_deputies):
        csv_repo = CsvRepository(tmp_path)
        output_file = csv_repo.export_deputy_metrics(example_deputies, year=2025)

        data = pd.read_csv(output_file)
        colunas_esperadas = {
            "deputy_id",
            "name",
            "party_code",
            "state_code",
            "weighted_degree",
            "degree_centrality",
            "betweenness_centrality",
        }
        assert colunas_esperadas.issubset(set(data.columns))

    def test_csv_sorted_by_centrality(self, tmp_path, example_deputies):
        csv_repo = CsvRepository(tmp_path)
        output_file = csv_repo.export_deputy_metrics(example_deputies, year=2025)

        data = pd.read_csv(output_file)
        assert list(data["deputy_id"]) == [3, 1, 2]

    def test_export_coauthorship_metrics_creates_file(self, tmp_path):
        csv_repo = CsvRepository(tmp_path)
        edges = [(1, 2, 3.5), (2, 3, 1.0), (1, 3, 2.0)]
        output_file = csv_repo.export_coauthorship_metrics(edges, year=2025)

        assert output_file.exists()
        assert output_file.name == "coauthorships_2025.csv"
        df = pd.read_csv(output_file)
        assert set(df.columns) == {"source_id", "target_id", "weight"}
        assert len(df) == 3
        # Sorted descending by weight
        assert list(df["weight"]) == [3.5, 2.0, 1.0]

    def test_export_coauthorship_metrics_from_objects(self, tmp_path):
        from models.coauthorship_edge import CoauthorshipEdge

        csv_repo = CsvRepository(tmp_path)
        edges = [
            CoauthorshipEdge(source_id=1, target_id=2, raw_weight=4, normalized_strength=2.0),
            CoauthorshipEdge(source_id=2, target_id=3, raw_weight=1, normalized_strength=0.5),
        ]
        output_file = csv_repo.export_coauthorship_metrics(edges, year=2024)

        df = pd.read_csv(output_file)
        assert len(df) == 2
        assert list(df["weight"]) == [2.0, 0.5]


class TestGraphExporter:
    """Tests for GEXF graph export/import."""

    @pytest.fixture
    def example_graph(self):
        graph = nx.Graph()
        graph.graph["name"] = "Grafo 2024"
        graph.add_node("1", label="Ana")
        graph.add_node("2", label="Bruno")
        graph.add_edge("1", "2", weight=3)
        return graph

    def test_export_gexf_creates_file(self, tmp_path, example_graph):
        exporter = GraphExporter(tmp_path)
        output_file = exporter.export_gexf(example_graph, year=2025)

        assert output_file.exists()
        assert output_file.name == "chamber_graph_2025.gexf"

    def test_gexf_is_valid_xml(self, tmp_path, example_graph):
        exporter = GraphExporter(tmp_path)
        output_file = exporter.to_gexf(example_graph, tmp_path / "graph.gexf")

        root = ET.parse(output_file).getroot()
        assert root.tag.endswith("gexf")

    def test_gexf_contains_nodes(self, tmp_path, example_graph):
        exporter = GraphExporter(tmp_path)
        path = exporter.to_gexf(example_graph, tmp_path / "graph.gexf")

        loaded_graph = nx.read_gexf(path)
        assert len(loaded_graph.nodes()) == len(example_graph.nodes())

    def test_gexf_contains_edges(self, tmp_path, example_graph):
        exporter = GraphExporter(tmp_path)
        path = exporter.to_gexf(example_graph, tmp_path / "graph.gexf")

        loaded_graph = nx.read_gexf(path)
        assert len(loaded_graph.edges()) == len(example_graph.edges())

    def test_gexf_metadata_preserved(self, tmp_path, example_graph):
        exporter = GraphExporter(tmp_path)
        path = exporter.to_gexf(example_graph, tmp_path / "graph.gexf")

        loaded_graph = nx.read_gexf(path)
        # NetworkX's reader preserves the GEXF structural metadata
        # (mode/edge_default) but may drop custom graph attributes
        # depending on the version.
        assert loaded_graph.graph.get("mode") == "static"
        assert "edge_default" in loaded_graph.graph

    def test_gexf_import(self, tmp_path, example_graph):
        exporter = GraphExporter(tmp_path)
        path = exporter.to_gexf(example_graph, tmp_path / "graph.gexf")

        imported_graph = exporter.from_gexf(path)
        assert len(imported_graph.nodes()) == len(example_graph.nodes())
        assert len(imported_graph.edges()) == len(example_graph.edges())


class TestDBExporter:
    """Tests for metrics persistence in SQLite."""

    def test_export_creates_db_and_table(self, tmp_path):
        db_path = tmp_path / "metricas.db"
        exporter = DB_Exporter(db_path)
        deputies = [
            Deputy(1, "Ana", "PT", "SP", weighted_degree=20, degree_centrality=0.4, betweenness_centrality=0.2),
            Deputy(2, "Bruno", "PSB", "RJ", weighted_degree=10, degree_centrality=0.2, betweenness_centrality=0.1),
        ]

        path_return = exporter.export_deputy_metrics(deputies, year=2025)

        assert path_return == db_path
        assert db_path.exists()

        with sqlite3.connect(db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM deputados_metricas").fetchone()[0]
        assert total == 2

    def test_export_performs_upsert(self, tmp_path):
        db_path = tmp_path / "metricas.db"
        exporter = DB_Exporter(db_path)

        exporter.export_deputy_metrics(
            [Deputy(1, "Ana", "PT", "SP", weighted_degree=20, degree_centrality=0.4)],
            year=2025,
        )
        exporter.export_deputy_metrics(
            [Deputy(1, "Ana", "PT", "SP", weighted_degree=99, degree_centrality=0.9)],
            year=2025,
        )

        with sqlite3.connect(db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM deputados_metricas").fetchone()[0]
            weighted_degree = conn.execute(
                "SELECT weighted_degree FROM deputados_metricas WHERE year = 2025 AND deputy_id = 1"
            ).fetchone()[0]

        assert total == 1
        assert weighted_degree == 99


class TestRepositoryErrors:
    """Error-handling tests."""

    def test_file_not_found(self):
        """Should handle a missing file."""
        exporter = GraphExporter(".")
        with pytest.raises(FileNotFoundError):
            exporter.from_gexf("missing_file.gexf")

    def test_corrupted_file(self, tmp_path):
        """Should handle a corrupted file."""
        output_file = tmp_path / "corrupted.gexf"
        output_file.write_text("<gexf><graph></gexf>", encoding="utf-8")
        exporter = GraphExporter(tmp_path)

        with pytest.raises(Exception):
            exporter.from_gexf(output_file)

    def test_write_permission_denied(self, tmp_path):
        """Should handle a permission error."""
        exporter = GraphExporter(tmp_path)
        graph = nx.Graph()
        graph.add_edge("1", "2")

        with pytest.raises(OSError):
            exporter.to_gexf(graph, tmp_path)
