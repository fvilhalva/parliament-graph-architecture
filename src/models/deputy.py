"""Data model for a member of the Chamber of Deputies."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Deputy:
    """Represents a member of parliament.

    Centrality fields are populated by ``ParliamentaryGraph`` after the
    network has been built; they default to ``0.0`` so the dataclass can be
    constructed before any graph computation has run.

    ``community_louvain`` is populated by
    :meth:`ParliamentaryGraph.assign_communities` and defaults to ``None`` so
    unenriched instances remain valid.

    Attributes:
        id: Unique identifier from Câmara API.
        name: Full name of the deputy.
        party_code: Political party abbreviation.
        state_code: Brazilian state code.
        weighted_degree: Sum of incident edge weights (co-authorship strength).
        degree_centrality: Weighted degree normalized by total network strength.
        betweenness_centrality: Betweenness centrality.
        closeness_centrality: Closeness centrality.
        eigenvector_centrality: Eigenvector centrality.
        community_louvain: Louvain community assignment id, or ``None`` when
            not yet computed / not a node in the analysed network.
    """

    id: int
    name: str
    party_code: str
    state_code: str
    weighted_degree: float = 0.0
    degree_centrality: float = 0.0
    betweenness_centrality: float = 0.0
    closeness_centrality: float = 0.0
    eigenvector_centrality: float = 0.0
    community_louvain: Optional[int] = None
