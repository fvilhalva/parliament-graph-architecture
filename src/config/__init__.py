# config/__init__.py
from .configs import Config
from .logging_config import setup_logger
from .constants import PARTIDOS, ESTADOS, MIN_COAUTORIAS, MIN_PESO_ARESTA

__all__ = [
    'Config',
    'setup_logger',
    'PARTIDOS',
    'ESTADOS',
    'MIN_COAUTORIAS',
    'MIN_PESO_ARESTA',
    'NUM_COMUNIDADES',
    'METODO_COMUNIDADE',
]