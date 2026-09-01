"""Centrality and network metric calculations."""

from typing import Dict, Iterable

import networkx as nx
import numpy as np


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


def gini_coefficient(values: Iterable[float]) -> float:
    """Gini coefficient of a distribution of non-negative values.

    Measures inequality/concentration: ``0`` is perfect equality (every deputy
    holds the same centrality) and values approaching ``1`` indicate that a few
    deputies concentrate the whole distribution. Implemented directly (no
    external dependency) from the standard mean-difference formulation.

    Args:
        values: Distribution of values (e.g. one centrality per deputy).

    Returns:
        Gini coefficient in ``[0, 1]``; ``0.0`` for an empty or all-zero input.
    """
    x = np.sort(np.asarray(list(values), dtype=float))
    n = x.size
    total = x.sum()
    if n == 0 or total == 0:
        return 0.0
    index = np.arange(1, n + 1)
    return float((2.0 * np.sum(index * x) - (n + 1) * total) / (n * total))


def top_k_share(values: Iterable[float], k: int) -> float:
    """Fraction of the total concentrated in the ``k`` largest values.

    Args:
        values: Distribution of values (e.g. one centrality per deputy).
        k: Number of largest values to sum.

    Returns:
        Share in ``[0, 1]``; ``0.0`` when the total is non-positive or ``k <= 0``.
    """
    x = np.sort(np.asarray(list(values), dtype=float))[::-1]
    total = x.sum()
    if total <= 0 or k <= 0:
        return 0.0
    return float(x[:k].sum() / total)
