"""Testes para a classe Proposicao"""
import pytest # type: ignore
from models.proposicao import Proposicao


class TestProposicaoCriacao:
    """Testes de criação de Proposicao"""

    def test_criar_proposicao_valida(self, proposicao_exemplo):
        """Deve criar uma proposição com dados válidos"""
        assert proposicao_exemplo.id_proposicao == 100
        assert proposicao_exemplo.ano == 2024
        assert proposicao_exemplo.ementa == "PL que trata de segurança na internet"

    def test_autores_ids_lista(self, proposicao_exemplo):
        """Autores devem ser uma lista de IDs"""
        assert isinstance(proposicao_exemplo.autores_ids, list)
        assert all(isinstance(id, int) for id in proposicao_exemplo.autores_ids)

    def test_proposicao_sem_autores(self):
        """Deve permitir proposição sem autores (ou com lista vazia)"""
        prop = Proposicao(
            id_proposicao=50,
            ano=2024,
            ementa="Proposição sem autores",
            autores_ids=[]
        )
        assert len(prop.autores_ids) == 0

    def test_proposicao_multiplos_autores(self, proposicao_exemplo):
        """Deve suportar múltiplos autores"""
        assert len(proposicao_exemplo.autores_ids) == 3
        assert 1 in proposicao_exemplo.autores_ids
        assert 2 in proposicao_exemplo.autores_ids


class TestProposicaoValidacoes:
    """Testes de validações de dados"""

    def test_ano_valido(self, proposicao_exemplo):
        """Ano deve ser um inteiro válido"""
        assert isinstance(proposicao_exemplo.ano, int)
        assert 1988 <= proposicao_exemplo.ano <= 2026

    def test_ementa_nao_vazia(self, proposicao_exemplo):
        """Ementa não deve estar vazia"""
        assert len(proposicao_exemplo.ementa) > 0

    def test_id_proposicao_positivo(self, proposicao_exemplo):
        """ID da proposição deve ser positivo"""
        assert proposicao_exemplo.id_proposicao > 0


class TestProposicaoIgualdade:
    """Testes de comparação entre proposições"""

    def test_proposicoes_mesmo_id(self):
        """Proposições com mesmo ID devem ser iguais"""
        prop1 = Proposicao(
            id_proposicao=100,
            ano=2024,
            ementa="PL sobre X",
            autores_ids=[1, 2]
        )
        prop2 = Proposicao(
            id_proposicao=100,
            ano=2024,
            ementa="PL sobre X",
            autores_ids=[1, 2]
        )
        assert prop1.id_proposicao == prop2.id_proposicao

    def test_proposicoes_ids_diferentes(self, proposicao_exemplo, proposicao_outro):
        """Proposições com IDs diferentes devem ser diferentes"""
        assert proposicao_exemplo.id_proposicao != proposicao_outro.id_proposicao


class TestProposicaoAutorias:
    """Testes relacionados a autorias"""

    def test_deputado_eh_autor(self, proposicao_exemplo):
        """Deve verificar se deputado é autor"""
        assert 1 in proposicao_exemplo.autores_ids
        assert 2 in proposicao_exemplo.autores_ids
        assert 3 in proposicao_exemplo.autores_ids

    def test_deputado_nao_eh_autor(self, proposicao_exemplo):
        """Deve verificar se deputado não é autor"""
        assert 999 not in proposicao_exemplo.autores_ids

    def test_numero_de_autores(self, proposicao_exemplo):
        """Deve contar número de autores corretamente"""
        assert len(proposicao_exemplo.autores_ids) == 3
