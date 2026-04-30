"""Centralized application configuration loaded from .env variables."""
import os
from pathlib import Path
from dotenv import load_dotenv  # type: ignore

load_dotenv()


class Config:
    """Application configuration class.
    
    All settings are loaded from environment variables (.env file).
    Provides paths, database, API, and analysis parameters.
    """
    
    # --- PATHS ---
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    CACHE_DIR = Path(os.getenv("CACHE_DIR", str(DATA_DIR / "cache")))
    GEXF_DIR = Path(os.getenv("GEXF_DIR", str(DATA_DIR / "gexf")))
    METRICS_DIR = Path(os.getenv("METRICAS_DIR", str(DATA_DIR / "metricas")))
    PLOTS_DIR = Path(os.getenv("PLOTS_DIR", str(DATA_DIR / "plots")))
    
    # --- DATABASE ---
    DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "parliament.db"))
    
    # --- LEGISLATURE ---
    CURRENT_LEGISLATURE = int(os.getenv("LEGISLATURA_ATUAL", "2026"))
    LEGISLATURE_START = int(os.getenv("LEGISLATURA_INICIO", "2006"))
    
    # --- CÂMARA API ---
    API_BASE_URL = os.getenv("API_BASE_URL", "https://dadosabertos.camara.leg.br/api/v2")
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
    
    # --- LOGGING ---
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # --- GRAPH ANALYSIS ---
    MIN_COAUTHORSHIPS = int(os.getenv("MIN_COAUTORIAS", "3"))
    MIN_EDGE_WEIGHT = int(os.getenv("MIN_PESO_ARESTA", "1"))
    NUM_COMMUNITIES = int(os.getenv("NUM_COMUNIDADES", "5"))
    
    def __init__(self, year: int = None) -> None:
        """Initialize configuration with a specific legislature year.
        
        Args:
            year: Legislature year (default: CURRENT_LEGISLATURE)
        """
        self.year = year or self.CURRENT_LEGISLATURE
        self.coauthorship_csv_url = self.get_coauthorship_csv_url(self.year)
        self.propositions_csv_url = self.get_propositions_csv_url(self.year)

    @classmethod
    def get_coauthorship_csv_url(cls, year: int) -> str:
        """Get CSV download URL for proposition authors (coauthorships) for a given year.
        
        Args:
            year: Legislature year
            
        Returns:
            Direct download URL for coauthorship CSV
        """
        return f"https://dadosabertos.camara.leg.br/arquivos/proposicoesAutores/csv/proposicoesAutores-{year}.csv"
    
    @classmethod
    def get_propositions_csv_url(cls, year: int) -> str:
        """Get CSV download URL for propositions metadata for a given year.
        
        Args:
            year: Legislature year
            
        Returns:
            Direct download URL for propositions CSV
        """
        return f"https://dadosabertos.camara.leg.br/arquivos/proposicoes/csv/proposicoes-{year}.csv"
