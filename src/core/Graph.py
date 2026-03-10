import networkx as nx
from itertools import combinations

class CamaraGraph:
    def __init__(self, dict_deputados, lista_proposicoes, lista_coautorias):
        self.G = nx.Graph()
        self.deputados = dict_deputados
        self.proposicoes = lista_proposicoes
        self.coautorias = lista_coautorias
    
    def construir_grafo(self):
        for prop in self.coautorias:
            # Pega a lista de IDs que está dentro do objeto
            ids = prop.autores_ids
            for u, v in combinations(ids, 2):
                if self.G.has_edge(u, v):
                   self.G[u][v]['weight'] += 1
                else:
                   self.G.add_edge(u, v, weight=1)

        for deputado_id in self.G.nodes():
            info = self.deputados.get(deputado_id)
            if info:
                # Se o objeto existe, usamos a notação de ponto (.)
                self.G.nodes[deputado_id]['label'] = info.nome
                self.G.nodes[deputado_id]['partido'] = info.sigla_partido
                self.G.nodes[deputado_id]['uf'] = info.sigla_uf
            else:
                # Fallback de segurança caso o deputado não esteja no mapeamento
                self.G.nodes[deputado_id]['label'] = f"Desconhecido ({deputado_id})"
                self.G.nodes[deputado_id]['partido'] = "N/A"
                self.G.nodes[deputado_id]['uf'] = "N/A"

        print(f"Grafo Finalizado! Nós: {self.G.number_of_nodes()} | Arestas: {self.G.number_of_edges()}")

    def search_deputados(self):
        pass