import pandas as pd  # type: ignore
from config import Config


class CamaraExtractor:
    def __init__(self, config: Config):
        self.config = config

    def extrair_dados_brutos(self, ano: int) -> pd.DataFrame:
        url = "https://dadosabertos.camara.leg.br/arquivos/proposicoes/csv/proposicoes-{ano}.csv"
        df_bruto = pd.read_csv(url, sep=";")
        return df_bruto

    def extrair_metadados_proposicoes(self, ano: int) -> pd.DataFrame:
        """Extrai o CSV de Proposições (onde está a siglaTipo e Ementa)"""
        url = "https://dadosabertos.camara.leg.br/arquivos/proposicoes/csv/proposicoes-{ano}.csvs"
        df_meta = pd.read_csv(url, sep=";")
        return df_meta

    def _fazer_requisicao(self, url: str, params: dict) -> dict:
        # Wrapper com retry, timeout, tratamento de erro
        # Rate limit respeitoso
        pass

    def _cachear(self, chave: str, dados: pd.DataFrame):
        # Salva em CSV/pickle para não refazer requisição
        pass
