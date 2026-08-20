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

    # --- LEGISLATURE ---
    CURRENT_LEGISLATURE: int = Field(
        default=2026,
        validation_alias=AliasChoices("CURRENT_LEGISLATURE", "LEGISLATURA_ATUAL"),
    )
    PILOT_LEGISLATURE: int = Field(
        default=2025,
        validation_alias=AliasChoices("PILOT_LEGISLATURE", "LEGISLATURA_PILOTO"),
    )
    LEGISLATURE_START: int = Field(
        default=2006,
        validation_alias=AliasChoices("LEGISLATURE_START", "LEGISLATURA_INICIO"),
    )

    # --- CHAMBER API ---
    API_BASE_URL: str = "https://dadosabertos.camara.leg.br/api/v2"
    API_TIMEOUT: int = 30

    # --- LOGGING ---
    LOG_LEVEL: str = "INFO"

    # --- GRAPH ANALYSIS ---
    MIN_COAUTHORSHIPS: int = Field(
        default=3, validation_alias=AliasChoices("MIN_COAUTHORSHIPS", "MIN_COAUTORIAS")
    )
    MIN_EDGE_WEIGHT: int = Field(
        default=1, validation_alias=AliasChoices("MIN_EDGE_WEIGHT", "MIN_PESO_ARESTA")
    )
    NUM_COMMUNITIES: int = Field(
        default=5, validation_alias=AliasChoices("NUM_COMMUNITIES", "NUM_COMUNIDADES")
    )
    MAX_AUTHORS_PER_PROPOSAL: int = 30

    @classmethod
    def get_coauthorship_csv_url(cls, year: int) -> str:
        """Direct download URL for the proposition-authors (coauthorship) CSV of a year."""
        return f"https://dadosabertos.camara.leg.br/arquivos/proposicoesAutores/csv/proposicoesAutores-{year}.csv"

    @classmethod
    def get_propositions_csv_url(cls, year: int) -> str:
        """Direct download URL for the propositions-metadata CSV of a year."""
        return f"https://dadosabertos.camara.leg.br/arquivos/proposicoes/csv/proposicoes-{year}.csv"
