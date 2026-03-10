import networkx as nx
from itertools import combinations

class CamaraGraph:
    def __init__(self, dict_deputados, lista_proposicoes, lista_coautorias, ano):
        self.G = nx.Graph()
        self.deputados = dict_deputados
        self.proposicoes = lista_proposicoes
        self.coautorias = lista_coautorias
        self.ano = ano
    
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

    def filtro_centralidade(self):
        grau = nx.degree_centrality(self.G)
        top_10 = sorted(grau.items(), key=lambda x: x[1], reverse=True)[:10]

        print("\n" + "="*60)
        print(f"RANKING YGGDRASIL - TOP 10 INFLUENTES (GRAU) - {self.ano}")
        print("="*60)

        for id_dep, valor in top_10:
            info = self.deputados.get(id_dep, {})

            if info:
               nome = info.nome
               partido = info.sigla_partido
               uf = info.sigla_uf
            else:
                nome = f"Desconhecido ({id_dep})"
                partido = "N/A"
                uf = "N/A"
    
            # Formatação alinhada
            print(f"ID: {id_dep:<6} | {nome[:25]:<25} | {partido:6}/{uf:2} | Centralidade: {valor:.4f}")

        print("="*60)

    def filtro_intermediacao(self):
        intermediacao = nx.betweenness_centrality(self.G)
        top_10 = sorted(intermediacao.items(), key=lambda x: x[1], reverse=True)[:10]

        print("\n" + "="*60)
        print(f"RANKING YGGDRASIL - TOP 10 PONTES (BETWEENNESS) - {self.ano}")
        print("="*60)

        for id_dep, valor in top_10:
            info = self.deputados.get(id_dep)
            if info:
                nome = info.nome
                partido = info.sigla_partido
                uf = info.sigla_uf
            else:
                nome = f"Desconhecido ({id_dep})"
                partido = "N/A"
                uf = "N/A"

            print(f"ID: {id_dep:<6} | {nome[:25]:<25} | {partido:6}/{uf:2} | Intermediação: {valor:.4f}")
        print("="*60)


    def search_deputados(self):
        pass