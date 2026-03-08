import pandas as pd
import networkx as nx
from itertools import combinations

# 1. Carregar APENAS o arquivo principal
url = "https://dadosabertos.camara.leg.br/arquivos/proposicoesAutores/csv/proposicoesAutores-2026.csv"
df = pd.read_csv(url, sep=';')

# Normalizar colunas para minúsculo para evitar erro de Case Sensitivity
df.columns = [c.strip().lower() for c in df.columns]

# 2. Filtrar apenas Deputados (codtipoautor == 10000)
df_deputados = df[df['codtipoautor'] == 10000].copy()
df_deputados = df_deputados.dropna(subset=['iddeputadoautor'])
df_deputados['iddeputadoautor'] = df_deputados['iddeputadoautor'].astype(int)

# =====================================================================
# O PULO DO GATO: CRIAR O MAPA DE DEPUTADOS USANDO O PRÓPRIO ARQUIVO
# Como um deputado assina vários projetos, pegamos a última assinatura dele
# no ano para garantir o Partido e UF mais recentes daquele ano.
# =====================================================================
df_meta = df_deputados.drop_duplicates(subset=['iddeputadoautor'], keep='last')
mapa_deputados = df_meta.set_index('iddeputadoautor')[['nomeautor', 'siglapartidoautor', 'siglaufautor']].to_dict('index')

# 3. Agrupar por Proposição e filtrar Coautorias (> 1 autor)
grupos = df_deputados.groupby('idproposicao')['iddeputadoautor'].apply(list)
coautorias = grupos[grupos.apply(len) > 1]

print(f"Total de projetos com coautoria: {len(coautorias)}")

# 4. Criar o Grafo YGGDRASIL
G = nx.Graph()

for autores in coautorias:
    for u, v in combinations(autores, 2):
        if G.has_edge(u, v):
            G[u][v]['weight'] += 1
        else:
            G.add_edge(u, v, weight=1)

# 5. Injetar os Nomes, Partidos e UF históricos!
for deputado_id in G.nodes():
    info = mapa_deputados.get(deputado_id, {})
    G.nodes[deputado_id]['label'] = info.get('nomeautor', str(deputado_id))
    G.nodes[deputado_id]['partido'] = info.get('siglapartidoautor', 'S/P')
    G.nodes[deputado_id]['uf'] = info.get('siglaufautor', 'S/U')

print(f"Grafo Finalizado! Nós: {G.number_of_nodes()} | Arestas: {G.number_of_edges()}")

# 6. Centralidade de Grau
grau = nx.degree_centrality(G)
top_10 = sorted(grau.items(), key=lambda x: x[1], reverse=True)[:10]

print("\n" + "="*60)
print(f"RANKING YGGDRASIL - TOP 10 INFLUENTES (GRAU)")
print("="*60)

for id_dep, valor in top_10:
    info = mapa_deputados.get(id_dep, {})
    nome = str(info.get('nomeautor', "NOME NÃO ENCONTRADO"))
    partido = str(info.get('siglapartidoautor', "S/P"))
    uf = str(info.get('siglaufautor', "??"))
    
    # Formatação alinhada
    print(f"ID: {id_dep:<6} | {nome[:25]:<25} | {partido:6}/{uf:2} | Centralidade: {valor:.4f}")

print("="*60)