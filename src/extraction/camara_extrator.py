import pandas as pd  # type: ignore
from pathlib import Path
from config import Config


class CamaraExtractor:
    def __init__(self, config: Config):
        self.config = config
        self.config.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def extrair_dados_brutos(self, ano: int) -> pd.DataFrame:
        path = self.config.CACHE_DIR / f"proposicoesAutores-{ano}.csv"
        
        if path.exists():
            df_bruto = pd.read_csv(path, sep=";")
            return df_bruto
        url = self.config.get_url_csv(ano)
        df_bruto = pd.read_csv(url, sep=";")
        return df_bruto

    def extrair_metadados_proposicoes(self, ano: int) -> pd.DataFrame:
        path = self.config.CACHE_DIR / f"proposicoes-{ano}.csv"
        if path.exists():
            df_meta = pd.read_csv(path, sep=";")
            return df_meta
        url = self.config.get_url_csv_proposicoes(ano)
        df_meta = pd.read_csv(url, sep=";")
        return df_meta

    def _fazer_requisicao(self, url: str, params: dict) -> dict:
        # Wrapper com retry, timeout, tratamento de erro
        # Rate limit respeitoso
        pass

    def _cachear(self, chave: str, dados: pd.DataFrame):
        # Salva em CSV/pickle para não refazer requisição
        pass
