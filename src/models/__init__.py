# Domain models for parliamentary network analysis
from .deputy import Deputy
from .proposition import Proposition
from .coauthorship_edge import CoauthorshipEdge
from .parliamentary_network import ParliamentaryNetwork

__all__ = [
    'Deputy',
    'Proposition',
    'CoauthorshipEdge',
    'ParliamentaryNetwork'
]