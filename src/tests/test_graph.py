"""Testes para a classe CamaraGraph (core)."""

import pytest  # type: ignore

from core import CamaraGraph
from models.deputado import Deputado
from models.proposicao import Proposicao


def _build_deputados() -> dict[int, Deputado]:
    return {
        1: Deputado(id_deputado=1, nome="A", sigla_partido="PT", sigla_uf="SP"),
        2: Deputado(id_deputado=2, nome="B", sigla_partido="PSB", sigla_uf="RJ"),
        3: Deputado(id_deputado=3, nome="C", sigla_partido="MDB", sigla_uf="MG"),
        4: Deputado(id_deputado=4, nome="D", sigla_partido="UNI", sigla_uf="BA"),
    }


def _build_proposicoes() -> list[Proposicao]:
    # Padrão determinístico para validar pesos:
    # P1 (PL): [1,2,3] -> (1,2),(1,3),(2,3) += 10
    # P2 (PLP): [1,2]   -> (1,2) += 5
    # P3 (PEC): [3,4]   -> (3,4) += 1
    return [
        Proposicao(id_proposicao=100, ano=2025, autores_ids=[1, 2, 3], sigla_tipo="PL"),
        Proposicao(id_proposicao=101, ano=2025, autores_ids=[1, 2], sigla_tipo="PLP"),
        Proposicao(id_proposicao=102, ano=2025, autores_ids=[3, 4], sigla_tipo="PEC"),
    ]


@pytest.fixture
def grafo_exemplo() -> CamaraGraph:
    deputados = _build_deputados()
    proposicoes = _build_proposicoes()
    grafo = CamaraGraph(
        dict_deputados=deputados,
        lista_proposicoes=proposicoes,
        lista_coautorias=proposicoes,
        ano=2025,
    )
    grafo.construir_grafo()
    return grafo


class TestCamaraGraphEstrutura:
    def test_criar_grafo_vazio(self):
        grafo = CamaraGraph()
        assert grafo.G.number_of_nodes() == 0
        assert grafo.G.number_of_edges() == 0

    def test_construir_grafo_com_nos_e_arestas(self, grafo_exemplo):
        assert grafo_exemplo.G.number_of_nodes() == 4
        assert grafo_exemplo.G.number_of_edges() == 4

    def test_arestas_sem_self_loop(self, grafo_exemplo):
        for u, v in grafo_exemplo.G.edges():
            assert u != v


class TestCamaraGraphPesosEDistancias:
    def test_agregacao_de_peso_por_par(self, grafo_exemplo):
        assert grafo_exemplo.G[1][2]["weight"] == 15
        assert grafo_exemplo.G[1][3]["weight"] == 10
        assert grafo_exemplo.G[2][3]["weight"] == 10
        assert grafo_exemplo.G[3][4]["weight"] == 1

    def test_distancia_inversa_ao_peso_da_proposicao(self, grafo_exemplo):
        assert grafo_exemplo.G[1][2]["distance"] == pytest.approx(1 / 10 + 1 / 5)
        assert grafo_exemplo.G[1][3]["distance"] == pytest.approx(1 / 10)
        assert grafo_exemplo.G[3][4]["distance"] == pytest.approx(1 / 1)


class TestCamaraGraphAtributosEMetricas:
    def test_atributos_de_no_preenchidos(self, grafo_exemplo):
        node_data = grafo_exemplo.G.nodes[1]
        assert node_data["label"] == "A"
        assert node_data["partido"] == "PT"
        assert node_data["uf"] == "SP"

    def test_filtro_centralidade_normalizado(self, grafo_exemplo):
        resultado = grafo_exemplo.filtro_centralidade()
        assert len(resultado) == 4
        total = sum(dep.degree_centrality for dep in resultado)
        assert total == pytest.approx(1.0)
        top = max(resultado, key=lambda dep: dep.weighted_degree)
        assert top.id_deputado == 1
        assert top.weighted_degree == 25

    def test_filtro_intermediacao_preenche_campo(self, grafo_exemplo):
        resultado = grafo_exemplo.filtro_intermediacao()
        assert len(resultado) == 4
        assert all(dep.betweenness_centrality >= 0 for dep in resultado)
        top = max(resultado, key=lambda dep: dep.betweenness_centrality)
        assert top.id_deputado == 3
