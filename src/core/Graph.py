import networkx as nx

class CamaraGraph:
    def __init__(self, dict_deputados, lista_proposicoes):
        self._G = nx.Graph()
        self.dict_deputados = dict_deputados
        self.lista_proposicoes = lista_proposicoes
    def search_deputados(self):
        ...