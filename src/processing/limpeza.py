import pandas as pd # type: ignore

class CamaraProcessor:
    def processar_coautorias(self, df_bruto: pd.DataFrame):
        # 1. Padronização
        df = df_bruto.copy()
        df.columns = [c.strip().lower() for c in df.columns] # deixar tudo minusculo

        # 2. Filtros de Domínio (Só Deputados Federais)
        df_dep = df[df['codtipoautor'] == 10000].copy()
        df_dep = df_dep.dropna(subset=['iddeputadoautor'])
        df_dep['iddeputadoautor'] = df_dep['iddeputadoautor'].astype(int)

        # 3. Metadados dos Nós (Vértices)
        df_meta = df_dep.drop_duplicates(subset=['iddeputadoautor'], keep='last')
        mapa_deputados = df_meta.set_index('iddeputadoautor')[['nomeautor', 'siglapartidoautor', 'siglaufautor']].to_dict('index')

        # 4. Agrupamento (Arestas)
        grupos = df_dep.groupby('idproposicao')['iddeputadoautor'].apply(list)
        coautorias = grupos[grupos.apply(len) > 1]

        return mapa_deputados, grupos, coautorias