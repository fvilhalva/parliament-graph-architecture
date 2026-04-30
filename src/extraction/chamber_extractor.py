"""Data extraction from Chamber of Deputies API and CSV files.

This module handles extraction of parliamentary data including proposition
authors (coauthorships) and proposition metadata from the Chamber's public API
and CSV download endpoints.
"""
import pandas as pd  # type: ignore
from pathlib import Path
from config import Config


class ChamberExtractor:
    """Extractor for parliamentary data from the Chamber of Deputies.

    Handles downloading and caching of proposition and coauthorship data
    from CSV files provided by the Chamber's open data portal.
    """
    
    def __init__(self, config: Config) -> None:
        """Initialize the extractor with configuration.
        
        Args:
            config: Configuration object with API URLs and cache paths
        """
        self.config = config
        self.config.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def extract_raw_coauthorship_data(self, year: int) -> pd.DataFrame:
        """Extract raw coauthorship data for a given year.
        
        Downloads proposition authors CSV from the Chamber's open data portal
        or loads from local cache if available.
        
        Args:
            year: Legislature year
            
        Returns:
            DataFrame with coauthorship data from propositions
        """
        cache_path = self.config.CACHE_DIR / f"proposicoesAutores-{year}.csv"
        
        if cache_path.exists():
            return pd.read_csv(cache_path, sep=";")
        
        url = self.config.get_coauthorship_csv_url(year)
        data_frame = pd.read_csv(url, sep=";")
        return data_frame

    def extract_propositions_metadata(self, year: int) -> pd.DataFrame:
        """Extract proposition metadata for a given year.
        
        Downloads propositions CSV from the Chamber's open data portal
        or loads from local cache if available.
        
        Args:
            year: Legislature year
            
        Returns:
            DataFrame with proposition metadata
        """
        cache_path = self.config.CACHE_DIR / f"proposicoes-{year}.csv"
        
        if cache_path.exists():
            return pd.read_csv(cache_path, sep=";")
        
        url = self.config.get_propositions_csv_url(year)
        data_frame = pd.read_csv(url, sep=";")
        return data_frame

    def _make_request(self, url: str, params: dict) -> dict:
        """Make HTTP request with retry and timeout handling.
        
        Args:
            url: Request URL
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        pass

    def _cache_data(self, key: str, data: pd.DataFrame) -> None:
        """Cache DataFrame to CSV for later retrieval.
        
        Args:
            key: Cache key identifier
            data: DataFrame to cache
        """
        pass
