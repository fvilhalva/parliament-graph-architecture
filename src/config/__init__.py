"""Configuration module for parliamentary network analysis."""
from .config import Config
from .logging_config import setup_logger
from .constants import (
    BRAZILIAN_STATES,
    DEPUTY_ID_ALIASES,
    MAX_AUTHORS_PER_PROPOSAL,
    MIN_COAUTHORSHIPS,
    MIN_EDGE_WEIGHT,
    NUM_COMMUNITIES,
    POLITICAL_PARTIES,
    PROPOSITION_TYPE_WEIGHTS,
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
    'DEPUTY_ID_ALIASES',
    'MAX_AUTHORS_PER_PROPOSAL',
]
