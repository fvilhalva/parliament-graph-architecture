"""Configuration module for parliamentary network analysis."""
from .config import Config
from .logging_config import setup_logger
from .constants import (
    DEPUTY_ID_ALIASES,
    MAX_AUTHORS_PER_PROPOSAL,
    PROPOSITION_TYPE_WEIGHTS,
)

__all__ = [
    'Config',
    'setup_logger',
    'PROPOSITION_TYPE_WEIGHTS',
    'DEPUTY_ID_ALIASES',
    'MAX_AUTHORS_PER_PROPOSAL',
]
