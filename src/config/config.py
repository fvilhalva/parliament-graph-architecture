"""Centralized application configuration, loaded and validated from .env variables."""
from pathlib import Path
from typing import ClassVar

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = Path(__file__).parent.parent.parent
_DATA_DIR = _BASE_DIR / "data"


class Config(BaseSettings):
    """Application configuration.

    All settings are read from environment variables (``.env`` file) and
    validated by pydantic at load time. An invalid value (for example a
    non-integer ``API_TIMEOUT``) fails fast with a descriptive error naming
    the offending field, instead of a raw ``ValueError`` raised at import time.

    Legacy (Portuguese) variable names are still accepted through
    ``AliasChoices`` for backwards compatibility.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- PATHS (class constants, not environment-loaded) ---
    BASE_DIR: ClassVar[Path] = _BASE_DIR
    DATA_DIR: ClassVar[Path] = _DATA_DIR

    # --- PATHS (environment-loaded) ---
    CACHE_DIR: Path = _DATA_DIR / "cache"
    GEXF_DIR: Path = _DATA_DIR / "gexf"
    METRICS_DIR: Path = Field(
        default=_DATA_DIR / "metricas",
        validation_alias=AliasChoices("METRICS_DIR", "METRICAS_DIR"),
    )
    PLOTS_DIR: Path = _DATA_DIR / "plots"
    ANALYSIS_DIR: Path = _DATA_DIR / "analysis"

    # --- DATABASE ---
    DB_PATH: str = str(_DATA_DIR / "parliament.db")

    # --- GRAPH ANALYSIS ---
    MAX_AUTHORS_PER_PROPOSAL: int = Field(
        default=30,
        validation_alias=AliasChoices("MAX_AUTHORS_PER_PROPOSAL", "MAX_AUTORES_POR_PROPOSICAO"),
    )

    @classmethod
    def get_coauthorship_csv_url(cls, year: int) -> str:
        """Direct download URL for the proposition-authors (coauthorship) CSV of a year."""
        return f"https://dadosabertos.camara.leg.br/arquivos/proposicoesAutores/csv/proposicoesAutores-{year}.csv"

    @classmethod
    def get_propositions_csv_url(cls, year: int) -> str:
        """Direct download URL for the propositions-metadata CSV of a year."""
        return f"https://dadosabertos.camara.leg.br/arquivos/proposicoes/csv/proposicoes-{year}.csv"
