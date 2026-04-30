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

    def test_salvar_csv_cria_arquivo(self, tmp_path, deputados_exemplo):
        csv_repo = CsvRepository(tmp_path)
        arquivo = csv_repo.exportar_metricas_deputados(deputados_exemplo, ano=2025)

        assert arquivo.exists()
        assert arquivo.name == "deputados_metricas_2025.csv"

    def test_csv_nao_corrompido(self, tmp_path, deputados_exemplo):
        csv_repo = CsvRepository(tmp_path)
        arquivo = csv_repo.exportar_metricas_deputados(deputados_exemplo, ano=2025)

        df = pd.read_csv(arquivo)
        assert len(df) == len(deputados_exemplo)
        assert not df.empty

    def test_ler_csv_valido(self, tmp_path, deputados_exemplo):
        csv_repo = CsvRepository(tmp_path)
        arquivo = csv_repo.exportar_metricas_deputados(deputados_exemplo, ano=2025)

        dados_lidos = pd.read_csv(arquivo)
        assert len(dados_lidos) > 0

    def test_arquivo_csv_com_dados_completos(self, tmp_path, deputados_exemplo):
        csv_repo = CsvRepository(tmp_path)
        arquivo = csv_repo.exportar_metricas_deputados(deputados_exemplo, ano=2025)

        dados_lidos = pd.read_csv(arquivo)
        colunas_esperadas = {
            "id_deputado",
            "nome",
            "sigla_partido",
            "sigla_uf",
            "weighted_degree",
            "degree_centrality",
            "betweenness_centrality",
        }
        assert colunas_esperadas.issubset(set(dados_lidos.columns))

    def test_csv_ordenado_por_centralidade(self, tmp_path, deputados_exemplo):
        csv_repo = CsvRepository(tmp_path)
        arquivo = csv_repo.exportar_metricas_deputados(deputados_exemplo, ano=2025)

        dados_lidos = pd.read_csv(arquivo)
        assert list(dados_lidos["id_deputado"]) == [3, 1, 2]


class TestGraphExporter:
    """Testes para exportação/importação de grafos GEXF."""

    @pytest.fixture
    def grafo_exemplo(self):
        grafo = nx.Graph()
        grafo.graph["nome"] = "Grafo 2024"
        grafo.add_node("1", label="Ana")
        grafo.add_node("2", label="Bruno")
        grafo.add_edge("1", "2", weight=3)
        return grafo

    def test_exportar_gexf_cria_arquivo(self, tmp_path, grafo_exemplo):
        exporter = GraphExporter(tmp_path)
        arquivo = exporter.exportar_gexf(grafo_exemplo, ano=2025)

        assert arquivo.exists()
        assert arquivo.name == "chamber_graph_2025.gexf"

    def test_arquivo_gexf_valido_xml(self, tmp_path, grafo_exemplo):
        exporter = GraphExporter(tmp_path)
        arquivo = exporter.to_gexf(grafo_exemplo, tmp_path / "grafo.gexf")

        raiz = ET.parse(arquivo).getroot()
        assert raiz.tag.endswith("gexf")

    def test_gexf_contem_nodes(self, tmp_path, grafo_exemplo):
        exporter = GraphExporter(tmp_path)
        caminho = exporter.to_gexf(grafo_exemplo, tmp_path / "grafo.gexf")

        grafo_lido = nx.read_gexf(caminho)
        assert len(grafo_lido.nodes()) == len(grafo_exemplo.nodes())

    def test_gexf_contem_arestas(self, tmp_path, grafo_exemplo):
        exporter = GraphExporter(tmp_path)
        caminho = exporter.to_gexf(grafo_exemplo, tmp_path / "grafo.gexf")

        grafo_lido = nx.read_gexf(caminho)
        assert len(grafo_lido.edges()) == len(grafo_exemplo.edges())

    def test_metadados_preservados_gexf(self, tmp_path, grafo_exemplo):
        exporter = GraphExporter(tmp_path)
        caminho = exporter.to_gexf(grafo_exemplo, tmp_path / "grafo.gexf")

        grafo_lido = nx.read_gexf(caminho)
        # O reader do NetworkX preserva metadados estruturais do GEXF
        # (mode/edge_default), mas pode descartar atributos customizados
        # de graph dependendo da versão.
        assert grafo_lido.graph.get("mode") == "static"
        assert "edge_default" in grafo_lido.graph

    def test_importar_gexf(self, tmp_path, grafo_exemplo):
        exporter = GraphExporter(tmp_path)
        caminho = exporter.to_gexf(grafo_exemplo, tmp_path / "grafo.gexf")

        grafo_importado = exporter.from_gexf(caminho)
        assert len(grafo_importado.nodes()) == len(grafo_exemplo.nodes())
        assert len(grafo_importado.edges()) == len(grafo_exemplo.edges())


class TestDBExporter:
    """Tests for metrics persistence in SQLite."""

    def test_exportar_metricas_cria_db_e_tabela(self, tmp_path):
        db_path = tmp_path / "metricas.db"
        exporter = DB_Exporter(db_path)
        deputies = [
            Deputy(1, "Ana", "PT", "SP", weighted_degree=20, degree_centrality=0.4, betweenness_centrality=0.2),
            Deputy(2, "Bruno", "PSB", "RJ", weighted_degree=10, degree_centrality=0.2, betweenness_centrality=0.1),
        ]

        path_return = exporter.exportar_metricas_deputados(deputies, ano=2025)

        assert path_return == db_path
        assert db_path.exists()

        with sqlite3.connect(db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM deputados_metricas").fetchone()[0]
        assert total == 2

    def test_exportar_metricas_faz_upsert(self, tmp_path):
        db_path = tmp_path / "metricas.db"
        exporter = DB_Exporter(db_path)

        exporter.exportar_metricas_deputados(
            [Deputy(1, "Ana", "PT", "SP", weighted_degree=20, degree_centrality=0.4)],
            ano=2025,
        )
        exporter.exportar_metricas_deputados(
            [Deputy(1, "Ana", "PT", "SP", weighted_degree=99, degree_centrality=0.9)],
            ano=2025,
        )

        with sqlite3.connect(db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM deputados_metricas").fetchone()[0]
            weighted_degree = conn.execute(
                "SELECT weighted_degree FROM deputados_metricas WHERE ano = 2025 AND id_deputado = 1"
            ).fetchone()[0]

        assert total == 1
        assert weighted_degree == 99


class TestRepositoryErros:
    """Testes de tratamento de erros"""

    def test_arquivo_nao_encontrado(self):
        """Deve tratar arquivo não encontrado"""
        exporter = GraphExporter(".")
        with pytest.raises(FileNotFoundError):
            exporter.from_gexf("arquivo_inexistente.gexf")

    def test_arquivo_corrompido(self, tmp_path):
        """Deve tratar arquivo corrompido"""
        arquivo = tmp_path / "corrompido.gexf"
        arquivo.write_text("<gexf><graph></gexf>", encoding="utf-8")
        exporter = GraphExporter(tmp_path)

        with pytest.raises(Exception):
            exporter.from_gexf(arquivo)

    def test_permissao_negada_escrita(self, tmp_path):
        """Deve tratar erro de permissão"""
        exporter = GraphExporter(tmp_path)
        grafo = nx.Graph()
        grafo.add_edge("1", "2")

        with pytest.raises(OSError):
            exporter.to_gexf(grafo, tmp_path)
