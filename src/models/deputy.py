"""Data model for a member of the Chamber of Deputies."""
from dataclasses import dataclass


@dataclass
class Deputy:
    """Represents a member of parliament.
    
    Attributes:
        id: Unique identifier from Câmara API
        name: Full name of the deputy
        party_code: Political party abbreviation
        state_code: Brazilian state code
        weighted_degree: Sum of edge weights (coauthorship strength)
        degree_centrality: Normalized degree centrality metric
        betweenness_centrality: Betweenness centrality metric
    """
    id: int
    name: str
    party_code: str
    state_code: str
    weighted_degree: float = 0.0
    degree_centrality: float = 0.0
    betweenness_centrality: float = 0.0
