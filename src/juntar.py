import pandas as pd
import networkx as nx
from itertools import combinations
import os
import time

# =====================================================================
# CONFIGURAÇÃO DE DIRETÓRIOS (Para o TCC ficar organizado)
# =====================================================================
os.makedirs("data/gexf", exist_ok=True)       
os.makedirs("data/metricas", exist_ok=True)   

historico_geral = []
historico_aliancas_principais = [] # Aqui vamos guardar quem trabalha com quem ano a ano!

# Partidos que queremos rastrear ao longo do tempo
partidos_alvo = ['PT', 'PL', 'PMDB', 'MDB', 'PSDB', 'PP', 'UNIÃO', 'PDT']

print("="*70)
print("INICIANDO O MOTOR YGGDRASIL: SÉRIE HISTÓRICA 2006-2026")
print("Mapeando Topologia e Evolução de Alianças Partidárias...")
print("="*70)

for ano in range(2006, 2027):
    start_time = time.time()
    print(f"\n🚀 [ANO {ano}] - Baixando e processando dados...")
    
    try:
        # 1. Carregar Dados da API
        url = f"https://dadosabertos.camara.leg.br/arquivos/proposicoesAutores/csv/proposicoesAutores-{ano}.csv"
        df = pd.read_csv(url, sep=';', encoding='utf-8')
        df.columns = [c.strip().lower() for c in df.columns]

        # 2. Filtrar Deputados e Limpar IDs
        df_dep = df[df['codtipoautor'] == 10000].copy()
        df_dep = df_dep.dropna(subset=['iddeputadoautor'])
        df_dep['iddeputadoautor'] = df_dep['iddeputadoautor'].astype(int)

        # 3. Mapear Metadados (A Estratégia do 'Last')
        df_meta = df_dep.drop_duplicates(subset=['iddeputadoautor'], keep='last')
        mapa_dep = df_meta.set_index('iddeputadoautor')[['nomeautor', 'siglapartidoautor', 'siglaufautor']].to_dict('index')

        # 4. Agrupar Coautorias
        grupos = df_dep.groupby('idproposicao')['iddeputadoautor'].apply(list)
        coautorias = grupos[grupos.apply(len) > 1]

        # 5. Criar o Grafo YGGDRASIL
        G = nx.Graph()
        for autores in coautorias:
            for u, v in combinations(autores, 2):
                if G.has_edge(u, v):
                    G[u][v]['weight'] += 1
                else:
                    G.add_edge(u, v, weight=1)

        # 6. Injetar Metadados nos Nós
        for dep_id in G.nodes():
            info = mapa_dep.get(dep_id, {})
            G.nodes[dep_id]['label'] = str(info.get('nomeautor', dep_id))
            G.nodes[dep_id]['partido'] = str(info.get('siglapartidoautor', 'S/P'))
            G.nodes[dep_id]['uf'] = str(info.get('siglaufautor', 'S/U'))

        # SALVAR GRAFO PRO GEPHI
        nx.write_gexf(G, f"data/gexf/yggdrasil_{ano}.gexf")

        # 7. Calcular Centralidades
        print(f"   -> Grafo montado (Nós: {G.number_of_nodes()} | Arestas: {G.number_of_edges()}). Calculando centralidades...")
        grau = nx.degree_centrality(G)
        intermediacao = nx.betweenness_centrality(G) 

        # 8. Agregar Métricas por Partido
        dados_grafo = []
        for no in G.nodes():
            dados_grafo.append({
                'id': no,
                'partido': G.nodes[no].get('partido', 'S/P'),
                'grau': grau[no],
                'intermediacao': intermediacao[no]
            })
        
        df_metricas = pd.DataFrame(dados_grafo)
        df_partidos = df_metricas.groupby('partido').agg(
            grau_medio=('grau', 'mean'),
            intermediacao_media=('intermediacao', 'mean'),
            tamanho_bancada=('id', 'count')
        ).reset_index()
        
        df_partidos = df_partidos[df_partidos['tamanho_bancada'] >= 5]
        df_partidos.to_csv(f"data/metricas/partidos_{ano}.csv", index=False, sep=';')

        # 9. Matriz de Alianças (Índice de Força Normalizada)
        tamanho_bancada = df_partidos.set_index('partido')['tamanho_bancada'].to_dict()
        aliancas = {}
        
        for u, v, data in G.edges(data=True):
            p_u = G.nodes[u].get('partido', 'S/P')
            p_v = G.nodes[v].get('partido', 'S/P')
            
            if p_u == p_v or p_u not in tamanho_bancada or p_v not in tamanho_bancada:
                continue
                
            par = tuple(sorted([p_u, p_v]))
            peso = data.get('weight', 1)
            aliancas[par] = aliancas.get(par, 0) + peso
            
        ranking_aliancas = []
        for (p1, p2), peso_total in aliancas.items():
            t1 = tamanho_bancada[p1]
            t2 = tamanho_bancada[p2]
            forca = (peso_total / (t1 * t2)) * 100
            
            ranking_aliancas.append({
                'ano': ano,
                'partido_A': p1,
                'partido_B': p2,
                'peso_bruto': peso_total,
                'forca_normalizada': round(forca, 4)
            })
            
        df_aliancas = pd.DataFrame(ranking_aliancas).sort_values(by='forca_normalizada', ascending=False)
        df_aliancas.to_csv(f"data/metricas/aliancas_{ano}.csv", index=False, sep=';')

        # =====================================================================
        # O PULO DO GATO: RASTREADOR DE PARCEIROS NO TERMINAL
        # =====================================================================
        print("   🤝 Principais Parceiros do Ano:")
        for partido in partidos_alvo:
            if partido in tamanho_bancada:
                # Acha onde o partido está (seja na coluna A ou B)
                df_filtro = df_aliancas[(df_aliancas['partido_A'] == partido) | (df_aliancas['partido_B'] == partido)]
                if not df_filtro.empty:
                    top_row = df_filtro.iloc[0]
                    parceiro = top_row['partido_B'] if top_row['partido_A'] == partido else top_row['partido_A']
                    forca = top_row['forca_normalizada']
                    
                    historico_aliancas_principais.append({
                        'Ano': ano,
                        'Partido_Base': partido,
                        'Tamanho_Bancada': tamanho_bancada[partido],
                        'Maior_Parceiro': parceiro,
                        'Forca_da_Alianca': forca
                    })
                    print(f"      -> {partido:<6} escolheu 💍 {parceiro:<8} (Índice: {forca:.2f})")

        # 10. Salvar Resumo Histórico do Ano
        top_1_grau = df_partidos.sort_values(by='grau_medio', ascending=False).iloc[0]['partido'] if not df_partidos.empty else "N/A"
        top_1_inter = df_partidos.sort_values(by='intermediacao_media', ascending=False).iloc[0]['partido'] if not df_partidos.empty else "N/A"
        
        historico_geral.append({
            'Ano': ano,
            'Projetos': len(coautorias),
            'Nos': G.number_of_nodes(),
            'Arestas': G.number_of_edges(),
            'Partido_Mais_Coeso': top_1_grau,
            'Partido_Maior_Ponte': top_1_inter
        })
        
        elapsed = time.time() - start_time
        print(f"   ✅ [CONCLUÍDO] Ano {ano} salvo em {elapsed:.2f} segundos!")

    except Exception as e:
        print(f"   ❌ [ERRO] Falha no processamento do ano {ano}: {e}")

# =====================================================================
# SALVAR OS DOIS RESUMOS DE 20 ANOS
# =====================================================================
df_resumo_final = pd.DataFrame(historico_geral)
df_resumo_final.to_csv("data/resumo_historico_geral.csv", index=False, sep=';')

df_resumo_aliancas = pd.DataFrame(historico_aliancas_principais)
df_resumo_aliancas.to_csv("data/historico_maiores_parceiros.csv", index=False, sep=';')

print("\n" + "="*70)
print("🎉 PIPELINE YGGDRASIL FINALIZADO COM SUCESSO!")
print("Arquivo 'historico_maiores_parceiros.csv' criado para a análise de quem trabalha com quem!")
print("="*70)