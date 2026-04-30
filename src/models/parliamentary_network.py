"""Data model for a complete parliamentary co-authorship network."""
from dataclasses import dataclass
from typing import Dict

import networkx as nx  # type: ignore

from models.deputy import Deputy


@dataclass
class ParliamentaryNetwork:
    """Represents a complete parliamentary co-authorship network for a given year.
    
    G = (V, E, w) where:
    - V: set of deputies
    - E: set of co-authorship relationships
    - w: edge weight function
    
    Attributes:
        year: Analysis year
        graph: NetworkX Graph instance (simple, undirected, weighted)
        deputies: Mapping of deputy_id -> Deputy object
    """
    year: int
    graph: nx.Graph
    deputies: Dict[int, Deputy]
    
    def total_nodes(self) -> int:
        """Get total number of deputies (nodes) in the network.
        
        Returns:
            Number of nodes in the graph
        """
        return self.graph.number_of_nodes()
        
    def total_edges(self) -> int:
        """Get total number of co-authorship relationships (edges).
        
        Returns:
            Number of edges in the graph
        """
        return self.graph.number_of_edges()
