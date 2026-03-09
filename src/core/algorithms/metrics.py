"""Cálculo de métricas de centralidade e outras análises de rede"""

import networkx as nx
from typing import Dict, Any


def calculate_degree_centrality(graph: nx.Graph) -> Dict[int, float]:
    """
    Calcula o degree centrality para todos os nós do grafo.
    
    Args:
        graph: Grafo networkx
        
    Returns:
        Dicionário com {node_id: centrality_value}
    """
    return nx.degree_centrality(graph)


def calculate_betweenness_centrality(graph: nx.Graph) -> Dict[int, float]:
    """
    Calcula o betweenness centrality para todos os nós.
    Indica o quão importante um nó é para conectar diferentes partes do grafo.
    
    Args:
        graph: Grafo networkx
        
    Returns:
        Dicionário com {node_id: centrality_value}
    """
    return nx.betweenness_centrality(graph)


def calculate_closeness_centrality(graph: nx.Graph) -> Dict[int, float]:
    """
    Calcula o closeness centrality para todos os nós.
    Indica o quão próximo um nó está de todos os outros.
    
    Args:
        graph: Grafo networkx
        
    Returns:
        Dicionário com {node_id: centrality_value}
    """
    return nx.closeness_centrality(graph)


def calculate_eigenvector_centrality(graph: nx.Graph, max_iter: int = 100) -> Dict[int, float]:
    """
    Calcula o eigenvector centrality para todos os nós.
    Indica a importância de um nó baseada na importância de seus vizinhos.
    
    Args:
        graph: Grafo networkx
        max_iter: Número máximo de iterações
        
    Returns:
        Dicionário com {node_id: centrality_value}
    """
    return nx.eigenvector_centrality(graph, max_iter=max_iter)
