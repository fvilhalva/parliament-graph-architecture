from config import Config
import pandas as pd # type: ignore

class CamaraExtractor:
    def __init__(self, config: Config, ano):
        self.config = config
        self.df = pd.DataFrame
        self.mapa_deputados = {}
        self.df_deputados: pd.DataFrame
        self.grupos = any
        self.coautorias = any
     
    def extrair_dados(self, ano):
        self.url = self.config.get_url_csv(ano)
        self.df = pd.read_csv(self.url, sep=';')

        self.df.columns = [c.strip().lower() for c in self.df.columns]

        self.df_deputados = self.df[self.df['codtipoautor'] == 10000].copy()
        self.df_deputados = self.df_deputados.dropna(subset=['iddeputadoautor'])
        self.df_deputados['iddeputadoautor'] = self.df_deputados['iddeputadoautor'].astype(int)

        df_meta = self.df_deputados.drop_duplicates(subset=['iddeputadoautor'], keep='last')
        self.mapa_deputados = df_meta.set_index('iddeputadoautor')[['nomeautor', 'siglapartidoautor', 'siglaufautor']].to_dict('index')

        self.grupos = self.df_deputados.groupby('idproposicao')['iddeputadoautor'].apply(list) # pega o id da proposição e autores 'id_proposicao': [id_deputado1, iddeputado2]

        self.coautorias = self.grupos[self.grupos.apply(len) > 1]

        return self.mapa_deputados, self.grupos, self.coautorias
    
    def _fazer_requisicao(self, url: str, params: dict) -> dict:
        # Wrapper com retry, timeout, tratamento de erro
        # Rate limit respeitoso
        pass
    
    def _cachear(self, chave: str, dados: pd.DataFrame):
        # Salva em CSV/pickle para não refazer requisição
        pass