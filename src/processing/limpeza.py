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
    def processar_dados_brutos(self, df_bruto: pd.DataFrame):
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
    
    def converter_para_modelos(self, mapa_deputados: dict, coautorias: pd.Series, ano: int):
        dict_deputados = {}
        for id_dep, info in mapa_deputados.items():
            dict_deputados[id_dep] = Deputado(
                id_deputado=id_dep,
                nome=info['nomeautor'],
                sigla_partido=info['siglapartidoautor'],
                sigla_uf=info['siglaufautor']
            )
        lista_proposicoes = []
        for id_prop, autores in coautorias.items():
            lista_proposicoes.append(Proposicao(
                id_proposicao=id_prop,
                ano=ano,
                # ementa="Ementa temporária",
                autores_ids=autores
        ))
        return dict_deputados, lista_proposicoes