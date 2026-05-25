"""Data extraction from the Chamber of Deputies CSV endpoints.

Handles downloading and on-disk caching of proposition and coauthorship
datasets from the Chamber's open-data portal so that re-runs are
reproducible without depending on the network.
"""
from pathlib import Path

import pandas as pd  # type: ignore

from config import Config, setup_logger

logger = setup_logger(__name__)


class ChamberExtractor:
    """Extractor for parliamentary data from the Chamber of Deputies."""

    def __init__(self, config: Config) -> None:
        """Initialize the extractor with configuration.

        Args:
            config: Configuration object with API URLs and cache paths.
        """
        self.config = config
        self.config.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def extract_raw_coauthorship_data(self, year: int) -> pd.DataFrame:
        """Extract raw coauthorship data for ``year``.

        Returns the cached CSV when available; otherwise downloads from the
        Chamber's open-data portal and persists the response so subsequent
        runs are deterministic.
        """
        cache_path = self.config.CACHE_DIR / f"proposicoesAutores-{year}.csv"
        url = self.config.get_coauthorship_csv_url(year)
        return self._read_or_download(cache_path, url, dataset="coauthorships", year=year)

    def extract_propositions_metadata(self, year: int) -> pd.DataFrame:
        """Extract proposition metadata for ``year``.

        Same cache-or-download semantics as
        :meth:`extract_raw_coauthorship_data`.
        """
        cache_path = self.config.CACHE_DIR / f"proposicoes-{year}.csv"
        url = self.config.get_propositions_csv_url(year)
        return self._read_or_download(cache_path, url, dataset="propositions", year=year)

    def _read_or_download(
        self,
        cache_path: Path,
        url: str,
        *,
        dataset: str,
        year: int,
    ) -> pd.DataFrame:
        """Load ``cache_path`` if present, otherwise download from ``url`` and cache."""
        if cache_path.exists():
            logger.info("Loading %s for %s from cache (%s).", dataset, year, cache_path)
            return pd.read_csv(cache_path, sep=";")

        logger.info("Downloading %s for %s from %s.", dataset, year, url)
        data_frame = pd.read_csv(url, sep=";")
        self._cache_data(cache_path, data_frame)
        logger.info("Cached %s for %s at %s.", dataset, year, cache_path)
        return data_frame

    def _cache_data(self, cache_path: Path, data: pd.DataFrame) -> None:
        """Persist a DataFrame to ``cache_path`` as semicolon-separated CSV."""
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(cache_path, sep=";", index=False)
