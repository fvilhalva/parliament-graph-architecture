import pandas as pd # type: ignore
from config import Config

class CamaraExtractor:
    def __init__(self, config: Config):
        self.config = config
        
    def extrair_dados_brutos(self, ano: int) -> pd.DataFrame:
        url = self.config.get_url_csv(ano)
        df_bruto = pd.read_csv(url, sep=';')
        return df_bruto
    
    def _fazer_requisicao(self, url: str, params: dict) -> dict:
        # Wrapper com retry, timeout, tratamento de erro
        # Rate limit respeitoso
        pass
    
    def _cachear(self, chave: str, dados: pd.DataFrame):
        # Salva em CSV/pickle para não refazer requisição
        pass