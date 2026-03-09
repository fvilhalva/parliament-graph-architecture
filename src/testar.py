import pandas as pd # type: ignore
import networkx as nx
from itertools import combinations

ano = 2026

# 1. Carregar APENAS o arquivo principal
url = f"https://dadosabertos.camara.leg.br/arquivos/proposicoesAutores/csv/proposicoesAutores-{ano}.csv"
df = pd.read_csv(url, sep=';')

# Normalizar colunas para minúsculo para evitar erro de Case Sensitivity
df.columns = [c.strip().lower() for c in df.columns]

# 2. Filtrar apenas Deputados (codtipoautor == 10000)
df_deputados = df[df['codtipoautor'] == 10000].copy()
df_deputados = df_deputados.dropna(subset=['iddeputadoautor'])
df_deputados['iddeputadoautor'] = df_deputados['iddeputadoautor'].astype(int)

df_meta = df_deputados.drop_duplicates(subset=['iddeputadoautor'], keep='last')
mapa_deputados = df_meta.set_index('iddeputadoautor')[['nomeautor', 'siglapartidoautor', 'siglaufautor']].to_dict('index')

# 3. Agrupar por Proposição e filtrar Coautorias (> 1 autor)
grupos = df_deputados.groupby('idproposicao')['iddeputadoautor'].apply(list) # pega o id da proposição e autores 'id_proposicao': [id_deputado1, iddeputado2]
coautorias = grupos[grupos.apply(len) > 1] # pega só as coautorias

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
print(f"RANKING YGGDRASIL - TOP 10 INFLUENTES (GRAU) - {ano}")
print("="*60)

for id_dep, valor in top_10:
    info = mapa_deputados.get(id_dep, {})
    nome = str(info.get('nomeautor', "NOME NÃO ENCONTRADO"))
    partido = str(info.get('siglapartidoautor', "S/P"))
    uf = str(info.get('siglaufautor', "??"))
    
    # Formatação alinhada
    print(f"ID: {id_dep:<6} | {nome[:25]:<25} | {partido:6}/{uf:2} | Centralidade: {valor:.4f}")

print("="*60)

print("Calculando Intermediação (Betweenness) para os partidos - aguarde uns segundos...")
intermediacao = nx.betweenness_centrality(G)

# 1. Extrair os dados dos nós para o Pandas
dados_grafo = []
for no in G.nodes():
    dados_grafo.append({
        'id': no,
        'partido': G.nodes[no].get('partido', 'S/P'),
        'grau': grau[no],               # Já calculado lá em cima!
        'intermediacao': intermediacao[no]
    })

df_metricas = pd.DataFrame(dados_grafo)

# 2. Agrupar por Partido e calcular as médias
df_partidos = df_metricas.groupby('partido').agg(
    grau_medio=('grau', 'mean'),
    intermediacao_media=('intermediacao', 'mean'),
    tamanho_bancada=('id', 'count')
).reset_index()

# Filtrar partidos nanicos (menos de 5 deputados) para não distorcer a média
df_partidos = df_partidos[df_partidos['tamanho_bancada'] >= 5]

# 3. Gerar os Rankings
ranking_grau = df_partidos.sort_values(by='grau_medio', ascending=False).head(5)
ranking_bridge = df_partidos.sort_values(by='intermediacao_media', ascending=False).head(5)

# 4. Prints Formatados
print("\n" + "="*60)
print(f"TOP 5 PARTIDOS - MAIOR GRAU MÉDIO (COESÃO) - {ano}")
print("="*60)
for _, row in ranking_grau.iterrows():
    print(f"Partido: {row['partido']:<8} | Grau Médio: {row['grau_medio']:.4f} | Tamanho: {row['tamanho_bancada']}")

print("\n" + "="*60)
print(f"TOP 5 PARTIDOS - MAIOR INTERMEDIAÇÃO (PONTES/ARTICULADORES) - {ano}")
print("="*60)
for _, row in ranking_bridge.iterrows():
    print(f"Partido: {row['partido']:<8} | Intermediação: {row['intermediacao_media']:.6f} | Tamanho: {row['tamanho_bancada']}")
print("="*60)


# =====================================================================
# MATRIZ DE ALIANÇAS PARTIDÁRIAS (QUEM TRABALHA COM QUEM)
# =====================================================================
print("\nCalculando Matriz de Afinidade Interpartidária (O 'Tinder' da Câmara)...")

aliancas = {}
# Criar um dicionário rápido para o tamanho das bancadas (já calculamos no df_partidos)
# Usamos apenas os partidos que passaram no filtro de nanicos (>= 5 deputados)
tamanho_bancada = df_partidos.set_index('partido')['tamanho_bancada'].to_dict()

for u, v, data in G.edges(data=True):
    partido_u = G.nodes[u].get('partido', 'S/P')
    partido_v = G.nodes[v].get('partido', 'S/P')

    # 1. Ignorar conexões do deputado com ele mesmo (self-loops caso existam)
    # 2. Ignorar conexões DENTRO do mesmo partido (queremos apenas pontes externas)
    # 3. Ignorar partidos que foram filtrados por serem nanicos
    if partido_u == partido_v or partido_u not in tamanho_bancada or partido_v not in tamanho_bancada:
        continue

    # Ordenar alfabeticamente para a chave do dicionário ficar única. 
    # Assim (PT, PL) e (PL, PT) contam pro mesmo balde.
    par = tuple(sorted([partido_u, partido_v]))
    
    peso_aresta = data.get('weight', 1)
    
    if par not in aliancas:
        aliancas[par] = 0
    aliancas[par] += peso_aresta

# Calcular o "Índice de Força" para não favorecer apenas os partidos gigantes
ranking_aliancas = []
for (p1, p2), peso_total in aliancas.items():
    tam1 = tamanho_bancada[p1]
    tam2 = tamanho_bancada[p2]
    
    # Índice = (Total de Coautorias) / (Tamanho P1 * Tamanho P2)
    # Multiplicamos por 100 apenas para o número não ficar muito pequeno na tela (virar algo tipo 2.5 em vez de 0.025)
    forca = (peso_total / (tam1 * tam2)) * 100 
    
    ranking_aliancas.append({
        'partido_A': p1,
        'partido_B': p2,
        'peso_bruto': peso_total,
        'forca_normalizada': round(forca, 4)
    })

df_aliancas = pd.DataFrame(ranking_aliancas)
# Ordena do maior índice de amizade pro menor
df_aliancas = df_aliancas.sort_values(by='forca_normalizada', ascending=False)

print("\n" + "="*70)
print(f"🤝 TOP 10 MAIORES ALIANÇAS INTERPARTIDÁRIAS (NORMALIZADAS) - {ano}")
print("="*70)
print(f"{'PARTIDO A':<10} | {'PARTIDO B':<10} | {'PESO BRUTO':<12} | {'FORÇA (ÍNDICE)':<15}")
print("-" * 70)
for _, row in df_aliancas.head(10).iterrows():
    print(f"{row['partido_A']:<10} | {row['partido_B']:<10} | {row['peso_bruto']:<12} | {row['forca_normalizada']:.4f}")
print("="*70)

# BÔNUS PRO TCC: Quem é o maior aliado do PT e do PL?
def ver_aliados(partido_alvo):
    print(f"\n🔍 Top 3 Parceiros do {partido_alvo}:")
    df_filtrado = df_aliancas[(df_aliancas['partido_A'] == partido_alvo) | (df_aliancas['partido_B'] == partido_alvo)]
    for _, row in df_filtrado.head(3).iterrows():
        parceiro = row['partido_B'] if row['partido_A'] == partido_alvo else row['partido_A']
        print(f"  -> {parceiro:<8} (Força: {row['forca_normalizada']:.4f})")

if 'PT' in tamanho_bancada: ver_aliados('PT')
if 'PL' in tamanho_bancada: ver_aliados('PL')
if 'UNIÃO' in tamanho_bancada: ver_aliados('UNIÃO')

print("\n" + "="*70)
print(f"🤝 TOP 10 MAIORES ALIANÇAS INTERPARTIDÁRIAS (NORMALIZADAS) - {ano}")
print("="*70)

# ideais:
# pegar o maior partido do ano baseado na centralidade e intermediação de 2006-2026 ou anual
# pegar os politcos mais influentes(intermediação e centralidade) nos ultimos 20 anos(2006-2026)
# detectar a influencia do 'centrão' nas proposições, como saber qual politico é de centrão?
{
    deputado_id: {
        
    }
}