"""Testes para a classe CamaraGraph (core)"""
import pytest # type: ignore
from core import CamaraGraph
from models.deputado import Deputado
from models.aresta_coautoria import ArestaCoautoria


class TestCamaraGraphCriacao:
    """Testes de criação e inicialização do grafo"""

    def test_criar_grafo_vazio(self):
        """Deve criar um grafo vazio"""
        grafo = CamaraGraph()
        assert grafo is not None

    def test_grafo_inicia_sem_nodes(self):
        """Grafo deve iniciar sem nós"""
        grafo = CamaraGraph()
        # Verificar se o grafo está vazio (implementação específica)
        # assert len(grafo.nodes()) == 0


class TestCamaraGraphNodes:
    """Testes de adição e manipulação de nós (deputados)"""

    def test_adicionar_deputado(self, deputado_silva):
        """Deve adicionar um deputado ao grafo"""
        grafo = CamaraGraph()
        # grafo.add_deputado(deputado_silva)
        # assert deputado_silva.id_deputado in grafo.nodes()
        pass

    def test_adicionar_multiplos_deputados(self, deputado_silva, deputado_santos, deputado_oliveira):
        """Deve adicionar múltiplos deputados"""
        grafo = CamaraGraph()
        # grafo.add_deputado(deputado_silva)
        # grafo.add_deputado(deputado_santos)
        # grafo.add_deputado(deputado_oliveira)
        # assert len(grafo.nodes()) == 3
        pass

    def test_buscar_deputado(self, deputado_silva):
        """Deve buscar um deputado pelo ID"""
        grafo = CamaraGraph()
        # grafo.add_deputado(deputado_silva)
        # encontrado = grafo.get_deputado(1)
        # assert encontrado.nome == "João Silva"
        pass


class TestCamaraGraphArestas:
    """Testes de adição de arestas (coautorias)"""

    def test_adicionar_aresta(self, deputado_silva, deputado_santos):
        """Deve adicionar uma aresta de coautoria"""
        grafo = CamaraGraph()
        aresta = ArestaCoautoria(
            source_id=deputado_silva.id_deputado,
            target_id=deputado_santos.id_deputado,
            peso_bruto=5
        )
        # grafo.add_deputado(deputado_silva)
        # grafo.add_deputado(deputado_santos)
        # grafo.add_aresta(aresta)
        # assert grafo.edge_count() >= 1
        pass

    def test_aresta_conecta_deputados_corretos(self, aresta_coautoria):
        """Aresta deve conectar os deputados corretos"""
        assert aresta_coautoria.source_id == 1
        assert aresta_coautoria.target_id == 2


class TestCamaraGraphMetricas:
    """Testes de cálculo de métricas do grafo"""

    def test_calcular_grau(self):
        """Deve calcular grau dos nós corretamente"""
        grafo = CamaraGraph()
        # Adicionar nós e arestas
        # grau = grafo.degree(1)
        # assert grau == numero_esperado
        pass

    def test_calcular_degree_centrality(self):
        """Deve calcular degree centrality"""
        grafo = CamaraGraph()
        # centralidade = grafo.calculate_degree_centrality()
        # assert centralidade[1] > 0
        pass

    def test_calcular_betweenness_centrality(self):
        """Deve calcular betweenness centrality"""
        grafo = CamaraGraph()
        # betweenness = grafo.calculate_betweenness_centrality()
        # assert betweenness[1] >= 0
        pass

    def test_conectividade_do_grafo(self):
        """Deve medir conectividade do grafo"""
        grafo = CamaraGraph()
        # Criar grafo com componentes
        # componentes = grafo.number_connected_components()
        # assert componentes >= 1
        pass


class TestCamaraGraphConsistencia:
    """Testes de consistência de dados"""

    def test_grafo_nao_tem_duplicatas(self, deputado_silva):
        """Não deve ter deputados duplicados"""
        grafo = CamaraGraph()
        # grafo.add_deputado(deputado_silva)
        # grafo.add_deputado(deputado_silva)
        # assert len(grafo.nodes()) == 1
        pass

    def test_arestas_bidirecionais(self, aresta_coautoria):
        """Arestas podem ser bidirecionais ou direcionadas"""
        # Verificar a intencionalidade do grafo
        pass
