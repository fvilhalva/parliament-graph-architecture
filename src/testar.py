import pandas as pd
import networkx as nx
from itertools import combinations

# 1. Carregar os dados
url = "https://dadosabertos.camara.leg.br/arquivos/proposicoesAutores/csv/proposicoesAutores-2025.csv"
df = pd.read_csv(url, sep=';')

# 2. Filtrar apenas Deputados (codTipoAutor == 10000)
# Agora usando o nome correto da coluna que o seu log mostrou
df_deputados = df[df['codTipoAutor'] == 10000].copy()

# 3. Limpar e converter IDs
df_deputados = df_deputados.dropna(subset=['idDeputadoAutor'])
df_deputados['idDeputadoAutor'] = df_deputados['idDeputadoAutor'].astype(int)

# 4. Agrupar por Proposição e filtrar Coautorias (> 1 autor)
grupos = df_deputados.groupby('idProposicao')['idDeputadoAutor'].apply(list)
coautorias = grupos[grupos.apply(len) > 1]

print(f"Total de projetos com coautoria: {len(coautorias)}")

# 5. Criar o Grafo YGGDRASIL
G = nx.Graph()
for autores in coautorias:
    # Gera todas as combinações de pares de deputados
    for u, v in combinations(autores, 2):
        if G.has_edge(u, v):
            G[u][v]['weight'] += 1
        else:
            G.add_edge(u, v, weight=1)

print(f"Grafo Finalizado! Nós: {G.number_of_nodes()} | Arestas: {G.number_of_edges()}")

# Centralidade de Grau (quem tem mais parceiros diferentes)
grau = nx.degree_centrality(G)
top_10 = sorted(grau.items(), key=lambda x: x[1], reverse=True)[:10]

#print("Top 10 Influentes (Grau):")
#for id_dep, valor in top_10:
#    print(f"ID: {id_dep} | Centralidade: {valor:.4f}")




print("Calculando Intermediação (pode demorar)...")
between = nx.betweenness_centrality(G)
top_bridge = sorted(between.items(), key=lambda x: x[1], reverse=True)[:3]

for id_dep, valor in top_bridge:
    # Se você já tiver o dict de nomes, usa aqui
    print(f"ID: {id_dep} | Intermediação: {valor:.6f}")

nx.write_gexf(G, "data/yggdrasil_2025_inter.gexf")