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
        pesos = {'PL': 10, 'PEC': 1, 'PLP': 5}

        for prop in self.coautorias:
            # Pega a lista de IDs que está dentro do objeto
            ids = prop.autores_ids

            valor_articulacao = pesos.get(prop.sigla_tipo, 1)
            distancia = 1 / valor_articulacao

            for u, v in combinations(ids, 2):
                if self.G.has_edge(u, v):
                   self.G[u][v]['weight'] += valor_articulacao
                   self.G[u][v]['distance'] += distancia
                else:
                    self.G.add_edge(u, v, weight=valor_articulacao, distance=distancia)

        for deputado_id in self.G.nodes():
            info = self.deputados.get(deputado_id)
            if info:
                self.G.nodes[deputado_id]['label'] = info.nome
                self.G.nodes[deputado_id]['partido'] = info.sigla_partido
                self.G.nodes[deputado_id]['uf'] = info.sigla_uf
            else:
                self.G.nodes[deputado_id]['label'] = f"Desconhecido ({deputado_id})"
                self.G.nodes[deputado_id]['partido'] = "N/A"
                self.G.nodes[deputado_id]['uf'] = "N/A"

        print(f"Grafo Finalizado! Nós: {self.G.number_of_nodes()} | Arestas: {self.G.number_of_edges()}")


    def search_deputados(self, termo):
        if str(termo).isdigit():
            dep_id = int(termo)
            info = self.deputados.get(dep_id)
            return [info] if info else []
        
        termo_lower = str(termo).lower()
        res = []
        for info in self.deputados.values():
            if termo_lower in info.nome.lower():
               res.append(info)
        return res
    
    def exibir_perfil_deputado(self, termo):
        deps = self.search_deputados(termo)
        if not deps:
            print(f"⚠️ Nenhum deputado encontrado para: {termo}")
            return
        print(f"\n🔍 Resultados da busca para '{termo}':")
        print("-" * 40)
        for d in deps:
            centralidade = self.G.degree(d.id_deputado) if self.G.has_node(d.id_deputado) else 0
            print(f"Nome:    {d.nome}")
            print(f"ID:      {d.id_deputado}")
            print(f"Partido: {d.sigla_partido}/{d.sigla_uf}")
            print(f"Conexões no Grafo Atual: {centralidade}")
            print("-" * 40)


    def filtro_centralidade(self):
        # grau = nx.degree_centrality(self.G)
        forca = dict(self.G.degree(weight='weight'))
        max_forca_encontrada = max(forca.values()) if forca else 1
        top_10 = sorted(forca.items(), key=lambda x: x[1], reverse=True)[:10]

        print("\n" + "="*60)
        print(f"RANKING YGGDRASIL - TOP 10 INFLUENTES (GRAU) - {self.ano}")
        print("="*60)

        for id_dep, valor in top_10:
            valor_norm = valor / max_forca_encontrada
            info = self.deputados.get(id_dep, {})
            nome = info.nome if info else f"ID: {id_dep}"
            partido = info.sigla_partido if info else "N/A"
            uf = info.sigla_uf if info else "N/A"
    
            # Formatação alinhada
            print(f"ID: {id_dep:<6} | {nome[:25]:<25} | {partido:6}/{uf:2} | Centralidade: {valor_norm:.4f}")

        print("="*60)

    def filtro_intermediacao(self):
        # intermediacao = nx.betweenness_centrality(self.G)
        intermediacao = nx.betweenness_centrality(self.G, weight='distance')
        top_10 = sorted(intermediacao.items(), key=lambda x: x[1], reverse=True)[:10]

        print("\n" + "="*60)
        print(f"RANKING YGGDRASIL - TOP 10 PONTES (BETWEENNESS) - {self.ano}")
        print("="*60)

        for id_dep, valor in top_10:
            info = self.deputados.get(id_dep, {})
            nome = info.nome if info else f"ID: {id_dep}"
            partido = info.sigla_partido if info else "N/A"
            uf = info.sigla_uf if info else "N/A"

            print(f"ID: {id_dep:<6} | {nome[:25]:<25} | {partido:6}/{uf:2} | Intermediação: {valor:.4f}")
        print("="*60)


