import os
from pathlib import Path
from dotenv import load_dotenv  # type: ignore

load_dotenv()

class Config:
     # Paths (estáticos)
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    GEXF_DIR = DATA_DIR / "gexf"
    METRICAS_DIR = DATA_DIR / "metricas"
    PLOTS_DIR = DATA_DIR / "plots"
    
    # API (estático)
    API_BASE_URL = os.getenv("API_BASE_URL", "https://dadosabertos.camara.leg.br/api/v2")
    API_TIMEOUT = 30
    
    # Database (estático)
    DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "parliament.db"))
    
    # Legislatura (estático)
    LEGISLATURA_ATUAL = os.getenv("LEGISLATURA_ATUAL", 2026)
    LEGISLATURA_INICIO = 2006
    
    # Logging (estático)
    LOG_LEVEL = "INFO"
    
    # Análise (estático)
    MIN_COAUTORIAS = 3
    MIN_PESO_ARESTA = 1
    NUM_COMUNIDADES = 5
    
    def __init__(self, ano: int = None):
        """
        Inicializa configurações com um ano específico.
        
        Args:
            ano: Ano da legislatura (padrão: LEGISLATURA_ATUAL)
        """
        self.ano = ano or int(self.LEGISLATURA_ATUAL)
        self.url_csv = f"https://dadosabertos.camara.leg.br/arquivos/proposicoesAutores/csv/proposicoesAutores-{self.ano}.csv"

    @classmethod
    def set_ano(self, ano):
        self.ano = ano
    @classmethod
    def get_ano(self):
        return self.ano
    @classmethod
    def get_url_csv(cls, ano: int) -> str:
        """Retorna URL do CSV para um ano específico"""
        return f"https://dadosabertos.camara.leg.br/arquivos/proposicoesAutores/csv/proposicoesAutores-{ano}.csv"