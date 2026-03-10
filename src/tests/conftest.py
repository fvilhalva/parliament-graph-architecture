"""Fixtures compartilhadas para todos os testes"""
import pytest # type: ignore
from models.deputado import Deputado
from models.proposicao import Proposicao
from models.aresta_coautoria import ArestaCoautoria


@pytest.fixture
def deputado_silva():
    """Cria um deputado para testes"""
    return Deputado(
        id_deputado=1,
        nome="João Silva",
        sigla_partido="PT",
        sigla_uf="SP",
        degree_centrality=0.5,
        betweenness_centrality=0.3
    )


@pytest.fixture
def deputado_santos():
    """Cria outro deputado para testes"""
    return Deputado(
        id_deputado=2,
        nome="Maria Santos",
        sigla_partido="PSDB",
        sigla_uf="MG",
        degree_centrality=0.6,
        betweenness_centrality=0.4
    )


@pytest.fixture
def deputado_oliveira():
    """Cria um terceiro deputado para testes"""
    return Deputado(
        id_deputado=3,
        nome="Carlos Oliveira",
        sigla_partido="PT",
        sigla_uf="RJ",
        degree_centrality=0.4,
        betweenness_centrality=0.2
    )


@pytest.fixture
def proposicao_exemplo():
    """Cria uma proposição para testes"""
    return Proposicao(
        id_proposicao=100,
        ano=2024,
        # ementa="PL que trata de segurança na internet",
        autores_ids=[1, 2, 3]
    )


@pytest.fixture
def proposicao_outro():
    """Cria outra proposição para testes"""
    return Proposicao(
        id_proposicao=101,
        ano=2024,
        # ementa="PL sobre reforma tributária",
        autores_ids=[1, 2]
    )


@pytest.fixture
def aresta_coautoria():
    """Cria uma aresta de coautoria para testes"""
    return ArestaCoautoria(
        source_id=1,
        target_id=2,
        peso_bruto=5,
        forca_normalizada=0.8
    )
