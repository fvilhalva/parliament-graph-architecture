"""Configuration module for parliamentary network analysis."""
from .config import Config
from .logging_config import setup_logger
from .constants import (
    POLITICAL_PARTIES,
    BRAZILIAN_STATES,
    MIN_COAUTHORSHIPS,
    MIN_EDGE_WEIGHT,
    NUM_COMMUNITIES,
    PROPOSITION_TYPE_WEIGHTS
)

__all__ = [
    'Config',
    'setup_logger',
    'POLITICAL_PARTIES',
    'BRAZILIAN_STATES',
    'MIN_COAUTHORSHIPS',
    'MIN_EDGE_WEIGHT',
    'NUM_COMMUNITIES',
    'PROPOSITION_TYPE_WEIGHTS',
]