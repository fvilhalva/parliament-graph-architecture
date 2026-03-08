import networkx as nx
import itertools

class GraphNetwork:
    def build_graph(self, projetos=[]):
        G = nx.Graph()

        for projeto in projetos:
            autores = projeto['coautores']
            for u, v in itertools.combinations(autores, 2):
                if G.has_edge(u, v):
                    G[u][v]['weight'] += 1
                else:
                    G.add_edge(u, v, weight=1)
        #print(nx.degree_centrality(G))
        print(len(G.nodes))