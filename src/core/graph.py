import networkx as nx # type: ignore
from itertools import combinations

# No início do arquivo ou dentro da classe
ID_MAPPER = {
    130398: 220657,  # Mapeia o ID fantasma para o ID real do André Fernandes
    # Adicione outros aqui se encontrar mais duplicatas
}

class CamaraGraph:
    def __init__(self, dict_deputados=None, lista_proposicoes=None, lista_coautorias=None, ano=None):
        self.G = nx.Graph()
        self.deputados = dict_deputados or {}
        self.proposicoes = lista_proposicoes or []
        self.coautorias = lista_coautorias or []
        self.ano = ano
    
    def construir_grafo(self):
        pesos = {'PL': 10, 'PEC': 1, 'PLP': 5}

        for prop in self.coautorias:
            # Pega a lista de IDs que está dentro do objeto
            ids_originais = prop.autores_ids
            ids = [ID_MAPPER.get(idx, idx) for idx in ids_originais]

            # Remove duplicatas caso o cara tenha assinado com os dois IDs (raro, mas acontece)
            ids = list(set(ids))

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
        forca = dict(self.G.degree(weight='weight'))
        total_forca = sum(forca.values()) if forca else 1
        deputados_centralidade = sorted(forca.items(), key=lambda x: x[1], reverse=True)

        res = [] 
        for id_dep, valor in deputados_centralidade:
            # Normalizacao por participacao na forca total da rede
            # Mantem comparabilidade entre anos com tamanhos diferentes.
            valor_norm = valor / total_forca
            info = self.deputados.get(id_dep, {})
            info.weighted_degree = valor
            info.degree_centrality = valor_norm
            res.append(info)
        return res

    def filtro_intermediacao(self):
        # intermediacao = nx.betweenness_centrality(self.G)
        intermediacao = nx.betweenness_centrality(self.G, weight='distance')
        deputados_intermediacao = sorted(intermediacao.items(), key=lambda x: x[1], reverse=True)

        res = []
        for id_dep, valor in deputados_intermediacao:
            info = self.deputados.get(id_dep, {})
            info.betweenness_centrality = valor
            res.append(info)

        return res

    def analise_estrutural_avancada(self):
        print("\n" + "!"*60)
        print(f"ANÁLISE ESTRUTURAL AVANÇADA - {self.ano}")
        print("!"*60)
        # 1. Vértices de Corte (Pontos de Articulação)
        pontos_articulacao = list(nx.articulation_points(self.G))
        print(f"\n⚠️ Pontos de Articulação encontrados: {len(pontos_articulacao)}")
        for id_dep in pontos_articulacao[:5]: # Mostrar só os top 5
            info = self.deputados.get(id_dep)
            nome = info.nome if info else id_dep
            print(f" - {nome} é essencial para a conectividade da rede.")
            # 2. Densidade do Grafo
        densidade = nx.density(self.G)
        print(f"\n📊 Densidade da Rede: {densidade:.4f}")

        # 3. Componentes Conectados
        componentes = nx.number_connected_components(self.G)
        print(f"🔗 O grafo possui {componentes} grupos isolados.")
        # 4. Diâmetro (só funciona se o grafo for totalmente conectado)
        if componentes == 1:
            diametro = nx.diameter(self.G, weight='distance')
            print(f"📏 Diâmetro da Rede (menor caminho entre os mais distantes): {diametro:.4f}")

    def identificar_dependentes(self, termo_busca="Luisa Canziani"):
        # 1. Encontrar o ID da deputada
        res = self.search_deputados(termo_busca)
        if not res:
            print(f"❌ Deputado {termo_busca} não encontrado.")
            return
        dep_id = res[0].id_deputado
        nome_alvo = res[0].nome

        # 2. Criar uma cópia para não estragar o grafo original do YGGDRASIL
        G_temp = self.G.copy()
        G_temp.remove_node(dep_id)

        # 3. Pegar os novos componentes isolados
        # O nx.connected_components devolve listas de nós que ainda se falam
        componentes = list(nx.connected_components(G_temp))
        
        # Ordenamos para o maior (Giant Component) ficar primeiro
        componentes.sort(key=len, reverse=True)

        print("\n" + "!"*60)
        print(f"ANÁLISE DE VULNERABILIDADE: {nome_alvo}")
        print("!"*60)

        if len(componentes) > 1:
            print(f"⚠️ A remoção de {nome_alvo} fragmentou o grafo em {len(componentes)} partes.")
            print("\n--- GRUPOS QUE FICARAM ISOLADOS ---")
            
            # O primeiro componente (index 0) é a massa principal, ignoramos ele.
            for i, comp in enumerate(componentes[1:], 1):
                print(f"\nSubgrupo {i} ({len(comp)} deputados):")
                for node_id in comp:
                    info = self.deputados.get(node_id)
                    nome = info.nome if info else f"ID: {node_id}"
                    partido = info.sigla_partido if info else "N/A"
                    print(f" - {nome} ({partido})")
        else:
            print(f"✅ A remoção de {nome_alvo} não isolou nenhum grupo (Rede Resiliente).")
        print("!"*60)

    def filtro_partidos_de_maior_grau(self):
        pass
    def filtro_partidos_de_maior_intermediacao(self):
        pass
