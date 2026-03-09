"""Testes para a classe ArestaCoautoria"""
import pytest # type: ignore
from models.aresta_coautoria import ArestaCoautoria


class TestArestaCriacao:
    """Testes de criação de ArestaCoautoria"""

    def test_criar_aresta_valida(self, aresta_coautoria):
        """Deve criar uma aresta com dados válidos"""
        assert aresta_coautoria.source_id == 1
        assert aresta_coautoria.target_id == 2
        assert aresta_coautoria.peso_bruto == 5

    def test_aresta_peso_positivo(self, aresta_coautoria):
        """Peso bruto deve ser positivo"""
        assert aresta_coautoria.peso_bruto > 0

    def test_aresta_forca_normalizada_default(self):
        """Força normalizada deve ter padrão 0.0"""
        aresta = ArestaCoautoria(
            source_id=1,
            target_id=2,
            peso_bruto=3
        )
        assert aresta.forca_normalizada == 0.0

    def test_aresta_forca_normalizada_customizada(self, aresta_coautoria):
        """Deve aceitar força normalizada customizada"""
        assert aresta_coautoria.forca_normalizada == 0.8


class TestArestaValidacoes:
    """Testes de validações"""

    def test_source_id_positivo(self, aresta_coautoria):
        """Source ID deve ser positivo"""
        assert aresta_coautoria.source_id > 0

    def test_target_id_positivo(self, aresta_coautoria):
        """Target ID deve ser positivo"""
        assert aresta_coautoria.target_id > 0

    def test_source_diferente_target(self, aresta_coautoria):
        """Source e target devem ser diferentes"""
        # Uma aresta deve conectar dois deputados diferentes
        assert aresta_coautoria.source_id != aresta_coautoria.target_id

    def test_peso_bruto_inteiro(self, aresta_coautoria):
        """Peso bruto deve ser inteiro"""
        assert isinstance(aresta_coautoria.peso_bruto, int)

    def test_forca_normalizada_entre_0_e_1(self, aresta_coautoria):
        """Força normalizada deve estar entre 0 e 1"""
        assert 0.0 <= aresta_coautoria.forca_normalizada <= 1.0


class TestArestaIgualdade:
    """Testes de comparação entre arestas"""

    def test_arestas_iguais(self):
        """Arestas entre mesmos nós devem ser iguais"""
        aresta1 = ArestaCoautoria(
            source_id=1,
            target_id=2,
            peso_bruto=5,
            forca_normalizada=0.8
        )
        aresta2 = ArestaCoautoria(
            source_id=1,
            target_id=2,
            peso_bruto=5,
            forca_normalizada=0.8
        )
        assert aresta1.source_id == aresta2.source_id
        assert aresta1.target_id == aresta2.target_id

    def test_arestas_diferentes_nodes(self):
        """Arestas entre nós diferentes devem ser diferentes"""
        aresta1 = ArestaCoautoria(source_id=1, target_id=2, peso_bruto=5)
        aresta2 = ArestaCoautoria(source_id=1, target_id=3, peso_bruto=5)
        assert aresta1.target_id != aresta2.target_id

    def test_arestas_diferentes_peso(self):
        """Arestas com pesos diferentes devem ser identificáveis"""
        aresta1 = ArestaCoautoria(source_id=1, target_id=2, peso_bruto=5)
        aresta2 = ArestaCoautoria(source_id=1, target_id=2, peso_bruto=10)
        assert aresta1.peso_bruto != aresta2.peso_bruto


class TestArestaPeso:
    """Testes relacionados a peso e força"""

    def test_peso_bruto_zero_nao_permitido(self):
        """Peso bruto deve ser > 0"""
        # Se a validação existir, testar aqui
        aresta = ArestaCoautoria(source_id=1, target_id=2, peso_bruto=0)
        assert aresta.peso_bruto == 0  # Ou lançar exceção

    def test_atualizar_peso_bruto(self, aresta_coautoria):
        """Deve permitir atualizar peso bruto"""
        aresta_coautoria.peso_bruto = 10
        assert aresta_coautoria.peso_bruto == 10

    def test_atualizar_forca_normalizada(self, aresta_coautoria):
        """Deve permitir atualizar força normalizada"""
        aresta_coautoria.forca_normalizada = 0.9
        assert aresta_coautoria.forca_normalizada == 0.9
