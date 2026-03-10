import pandas as pd # type: ignore
import logging
from typing import List, Tuple
from models.deputado import Deputado
from models.proposicao import Proposicao
from models.aresta_coautoria import ArestaCoautoria

class CamaraProcessor:
    def __init__(self, bool = True):
        self.logger = self._setup_logger()
        self.df_original = None
        self.df_limpo = None
        self.deputados: List[Deputado] = []
        self.proposicoes: List[Proposicao] = []
        self.arestas: List[ArestaCoautoria] = []

    def _setup_logger(self) -> logging.Logger:
        """Configura logging para o processamento"""
        pass
    def processar_dados_brutos(self, df_bruto: pd.DataFrame, df_proposicoes: pd.DataFrame, filtro=[]):
        # 1. Padronização
        df_a = df_bruto.copy()
        df_p = df_proposicoes.copy()

        df_a.columns = [c.strip().lower() for c in df_a.columns]
        df_p.columns = [c.strip().lower() for c in df_p.columns]

        # 2. Filtro de Visão (Manter apenas o que tem valor político real)
        # Selecionamos apenas Projetos de Lei, Emendas à Constituição e Leis Complementares
        df_p_filtrado = df_p[df_p['siglatipo'].isin(filtro)]

        # 3. Cruzamento (Merge): O "filtro atômico"
        # O inner join remove instantaneamente os 90 mil registros de requerimentos e ofícios
        df = df_a.merge(
            df_p_filtrado[['id', 'siglatipo']], 
            left_on='idproposicao', 
            right_on='id', 
            how='inner'
        )

        mapa_tipos = df.drop_duplicates('idproposicao').set_index('idproposicao')['siglatipo'].to_dict()

        # 2. Filtros de Domínio (Só Deputados Federais)
        df_dep = df[df['codtipoautor'] == 10000].copy()
        df_dep = df_dep.dropna(subset=['iddeputadoautor'])
        df_dep['iddeputadoautor'] = df_dep['iddeputadoautor'].astype(int)

        # 3. Metadados dos Nós (Vértices)
        df_meta = df_dep.drop_duplicates(subset=['iddeputadoautor'], keep='last')
        mapa_deputados = df_meta.set_index('iddeputadoautor')[['nomeautor', 'siglapartidoautor', 'siglaufautor']].to_dict('index')

        # 4. Agrupamento (Arestas)
        grupos = df_dep.groupby('idproposicao')['iddeputadoautor'].apply(list) # todos os projetos
        coautorias = grupos[grupos.apply(len) > 1]

        return mapa_deputados, grupos, coautorias, mapa_tipos
    
    def processar_dados_brutos_sem_filtros(self, df_bruto: pd.DataFrame): # não recomendo, polui mt o grafo, basicamente é todo movimento de um deputado kkkk
        # 1. Padronização
        df = df_bruto.copy()

        df.columns = [c.strip().lower() for c in df.columns]

        # 2. Filtros de Domínio (Só Deputados Federais)
        df_dep = df[df['codtipoautor'] == 10000].copy()
        df_dep = df_dep.dropna(subset=['iddeputadoautor'])
        df_dep['iddeputadoautor'] = df_dep['iddeputadoautor'].astype(int)

        # 3. Metadados dos Nós (Vértices)
        df_meta = df_dep.drop_duplicates(subset=['iddeputadoautor'], keep='last')
        mapa_deputados = df_meta.set_index('iddeputadoautor')[['nomeautor', 'siglapartidoautor', 'siglaufautor']].to_dict('index')

        # 4. Agrupamento (Arestas)
        grupos = df_dep.groupby('idproposicao')['iddeputadoautor'].apply(list) # todos os projetos
        coautorias = grupos[grupos.apply(len) > 1]

        return mapa_deputados, grupos, coautorias
    
    def converter_para_modelos(self, mapa_deputados: dict, grupos: pd.Series, coautorias: pd.Series, mapa_tipos: dict, ano: int):
        # 1. Mapeamento de Deputados (Vértices)
        dict_deputados = {}
        for id_dep, info in mapa_deputados.items():
            dict_deputados[id_dep] = Deputado(
                id_deputado=id_dep,
                nome=info['nomeautor'],
                sigla_partido=info['siglapartidoautor'],
                sigla_uf=info['siglaufautor']
            )
        # 2. Subconjunto: Só o que vira aresta no Grafo
        lista_coautorias = []
        for id_prop, autores in coautorias.items():
            lista_coautorias.append(Proposicao(
                id_proposicao=id_prop,
                ano=ano,
                # ementa="Ementa temporária",
                autores_ids=autores,
                sigla_tipo=mapa_tipos.get(id_prop, "N/A")
        ))
        
        # 3. Catálogo Geral: Todos os projetos (Individuais + Coletivos)
        lista_proposicoes = []
        for id_prop, autores in grupos.items():
            lista_proposicoes.append(Proposicao(
                id_proposicao=id_prop,
                ano=ano,
                # ementa="Ementa temporária",
                autores_ids=autores,
                sigla_tipo=mapa_tipos.get(id_prop, "N/A")
        ))
        return dict_deputados, lista_proposicoes, lista_coautorias