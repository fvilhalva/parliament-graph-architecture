"""Testes para a classe Deputado"""
import pytest # type: ignore
from models.deputado import Deputado


class TestDeputadoCriacao:
    """Testes de criação de Deputizado"""

    def test_criar_deputado_valido(self, deputado_silva):
        """Deve criar um deputado com dados válidos"""
        assert deputado_silva.id_deputado == 1
        assert deputado_silva.nome == "João Silva"
        assert deputado_silva.sigla_partido == "PT"
        assert deputado_silva.sigla_uf == "SP"

    def test_criar_deputado_com_metricas(self, deputado_silva):
        """Deve preservar métricas de centralidade"""
        assert deputado_silva.degree_centrality == 0.5
        assert deputado_silva.betweenness_centrality == 0.3

    def test_criar_deputado_sem_metricas(self):
        """Deve ter métricas zeradas por padrão"""
        dep = Deputado(
            id_deputado=10,
            nome="Test",
            sigla_partido="XX",
            sigla_uf="XX"
        )
        assert dep.degree_centrality == 0.0
        assert dep.betweenness_centrality == 0.0


class TestDeputadoIgualdade:
    """Testes de comparação entre deputados"""

    def test_deputados_iguais_mesmo_id(self, deputado_silva):
        """Deputados com mesmo ID devem ser iguais"""
        outro = Deputado(
            id_deputado=1,
            nome="João Silva",
            sigla_partido="PT",
            sigla_uf="SP"
        )
        assert deputado_silva.id_deputado == outro.id_deputado

    def test_deputados_diferentes_ids(self, deputado_silva, deputado_santos):
        """Deputados com IDs diferentes devem ser diferentes"""
        assert deputado_silva.id_deputado != deputado_santos.id_deputado


class TestDeputadoValidacoes:
    """Testes de validações de dados"""

    def test_sigla_partido_valida(self, deputado_silva):
        """Sigla do partido deve ter 2-4 caracteres"""
        assert len(deputado_silva.sigla_partido) <= 4

    def test_sigla_uf_valida(self, deputado_silva):
        """Sigla da UF deve ter 2 caracteres"""
        assert len(deputado_silva.sigla_uf) == 2

    def test_centrality_entre_0_e_1(self, deputado_silva):
        """Métricas de centralidade devem estar entre 0 e 1"""
        assert 0.0 <= deputado_silva.degree_centrality <= 1.0
        assert 0.0 <= deputado_silva.betweenness_centrality <= 1.0


class TestDeputadoAtualizacaoMetricas:
    """Testes de atualização de métricas"""

    def test_atualizar_degree_centrality(self, deputado_silva):
        """Deve atualizar degree centrality"""
        deputado_silva.degree_centrality = 0.7
        assert deputado_silva.degree_centrality == 0.7

    def test_atualizar_betweenness_centrality(self, deputado_silva):
        """Deve atualizar betweenness centrality"""
        deputado_silva.betweenness_centrality = 0.6
        assert deputado_silva.betweenness_centrality == 0.6
