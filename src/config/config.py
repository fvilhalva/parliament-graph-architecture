"""Centralized application configuration loaded from .env variables."""
import os
import warnings
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv  # type: ignore

load_dotenv()


def _env(name: str, legacy_name: Optional[str] = None, default: Optional[str] = None) -> Optional[str]:
    """Read an environment variable, falling back to a legacy name with a DeprecationWarning.

    Args:
        name: Canonical (English) environment variable name.
        legacy_name: Older (Portuguese) name kept for one release for backwards compatibility.
        default: Value to return if neither variable is set.

    Returns:
        The resolved string value, or ``default`` if no variable is set.
    """
    value = os.getenv(name)
    if value is not None:
        return value

    if legacy_name is not None:
        legacy_value = os.getenv(legacy_name)
        if legacy_value is not None:
            warnings.warn(
                f"Environment variable '{legacy_name}' is deprecated; rename to '{name}'.",
                DeprecationWarning,
                stacklevel=2,
            )
            return legacy_value

    return default


class Config:
    """Application configuration class.

    All settings are loaded from environment variables (.env file).
    Provides paths, database, API, and analysis parameters.
    """

    # --- PATHS ---
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    CACHE_DIR = Path(_env("CACHE_DIR", default=str(DATA_DIR / "cache")))
    GEXF_DIR = Path(_env("GEXF_DIR", default=str(DATA_DIR / "gexf")))
    METRICS_DIR = Path(_env("METRICS_DIR", legacy_name="METRICAS_DIR", default=str(DATA_DIR / "metricas")))
    PLOTS_DIR = Path(_env("PLOTS_DIR", default=str(DATA_DIR / "plots")))

    # --- DATABASE ---
    DB_PATH = _env("DB_PATH", default=str(DATA_DIR / "parliament.db"))

    # --- LEGISLATURE ---
    CURRENT_LEGISLATURE = int(_env("CURRENT_LEGISLATURE", legacy_name="LEGISLATURA_ATUAL", default="2026"))
    PILOT_LEGISLATURE = int(_env("PILOT_LEGISLATURE", legacy_name="LEGISLATURA_PILOTO", default="2025"))
    LEGISLATURE_START = int(_env("LEGISLATURE_START", legacy_name="LEGISLATURA_INICIO", default="2006"))

    # Backwards-compatible alias for callers still using the old attribute name.
    CURRENT_PILOTO = PILOT_LEGISLATURE

    # --- CHAMBER API ---
    API_BASE_URL = _env("API_BASE_URL", default="https://dadosabertos.camara.leg.br/api/v2")
    API_TIMEOUT = int(_env("API_TIMEOUT", default="30"))

    # --- LOGGING ---
    LOG_LEVEL = _env("LOG_LEVEL", default="INFO")

    # --- GRAPH ANALYSIS ---
    MIN_COAUTHORSHIPS = int(_env("MIN_COAUTHORSHIPS", legacy_name="MIN_COAUTORIAS", default="3"))
    MIN_EDGE_WEIGHT = int(_env("MIN_EDGE_WEIGHT", legacy_name="MIN_PESO_ARESTA", default="1"))
    NUM_COMMUNITIES = int(_env("NUM_COMMUNITIES", legacy_name="NUM_COMUNIDADES", default="5"))
    MAX_AUTHORS_PER_PROPOSAL = int(_env("MAX_AUTHORS_PER_PROPOSAL", default="30"))

    def __init__(self, year: Optional[int] = None) -> None:
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
