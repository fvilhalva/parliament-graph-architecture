"""Centrality and network metric calculations."""

from typing import Dict

import networkx as nx


def calculate_degree_centrality(graph: nx.Graph) -> Dict[int, float]:
    """Compute degree centrality for every node.

    Args:
        graph: A NetworkX graph.

    Returns:
        Mapping of ``{node_id: centrality_value}``.
    """
    return nx.degree_centrality(graph)


def calculate_betweenness_centrality(graph: nx.Graph) -> Dict[int, float]:
    """Compute betweenness centrality for every node.

    Measures how often a node lies on shortest paths between other pairs.

    Args:
        graph: A NetworkX graph.

    Returns:
        Mapping of ``{node_id: centrality_value}``.
    """
    return nx.betweenness_centrality(graph)


def calculate_closeness_centrality(graph: nx.Graph) -> Dict[int, float]:
    """Compute closeness centrality for every node.

    Measures how close a node is to all other reachable nodes.

    Args:
        graph: A NetworkX graph.

    Returns:
        Mapping of ``{node_id: centrality_value}``.
    """
    return nx.closeness_centrality(graph)


def calculate_eigenvector_centrality(graph: nx.Graph, max_iter: int = 100) -> Dict[int, float]:
    """Compute eigenvector centrality for every node.

    Measures the importance of a node based on the importance of its neighbours.
    Falls back to the NumPy implementation when the power iteration does not converge
    (e.g., disconnected graphs).

    Args:
        graph: A NetworkX graph.
        max_iter: Maximum number of iterations for the power method.

    Returns:
        Mapping of ``{node_id: centrality_value}``.
    """
    try:
        return nx.eigenvector_centrality(graph, max_iter=max_iter, weight="weight")
    except (nx.PowerIterationFailedConvergence, nx.NetworkXException):
        if graph.number_of_nodes() == 0:
            return {}
        return nx.eigenvector_centrality_numpy(graph, weight="weight")
