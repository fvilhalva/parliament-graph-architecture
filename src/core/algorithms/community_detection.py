"""Detecção de comunidades e estruturas de influência em redes parlamentares."""

from __future__ import annotations

import networkx as nx
from networkx.algorithms.community import louvain_communities, label_propagation_communities
from sklearn.cluster import SpectralClustering  # type: ignore


class CommunityDetector:
    """
    Detector de comunidades em grafos parlamentares.
    Identifica grupos de deputados com alta coautoria.
    """
    
    def __init__(self):
        """Inicializa o detector de comunidades."""

    @staticmethod
    def _communities_to_partition(communities: list[set]) -> dict[int, int]:
        """Converte comunidades em mapeamento node_id -> community_id."""
        partition: dict[int, int] = {}
        for community_id, nodes in enumerate(communities):
            for node in nodes:
                partition[node] = community_id
        return partition

    @staticmethod
    def _partition_to_communities(partition: dict[int, int]) -> list[set]:
        """Converte mapeamento node_id -> community_id em lista de conjuntos."""
        grouped: dict[int, set] = {}
        for node, community_id in partition.items():
            grouped.setdefault(community_id, set()).add(node)
        return list(grouped.values())

    def detect_louvain(
        self,
        graph: nx.Graph,
        resolution: float = 1.0,
        seed: int | None = 42,
    ) -> dict[int, int]:
        """
        Detecta comunidades usando o algoritmo Louvain (NetworkX).
        
        Args:
            graph: Grafo networkx
            
        Returns:
            Dicionario {node_id: community_id}
        """
        if graph.number_of_nodes() == 0:
            return {}

        communities = louvain_communities(
            graph,
            weight="weight",
            resolution=resolution,
            seed=seed,
        )
        return self._communities_to_partition([set(c) for c in communities])

    def detect_label_propagation(self, graph: nx.Graph) -> dict[int, int]:
        """
        Detecta comunidades por propagacao de rotulos.

        Returns:
            Dicionario {node_id: community_id}
        """
        if graph.number_of_nodes() == 0:
            return {}

        communities = [set(c) for c in label_propagation_communities(graph)]
        return self._communities_to_partition(communities)

    def detect_spectral(self, graph: nx.Graph, n_clusters: int = 5) -> dict[int, int]:
        """
        Detecta comunidades usando clustering espectral (scikit-learn).
        
        Args:
            graph: Grafo networkx
            n_clusters: Número de comunidades esperadas
            
        Returns:
            Dicionario {node_id: community_id}
        """
        if graph.number_of_nodes() == 0:
            return {}

        nodes = list(graph.nodes())
        n_clusters = max(2, min(n_clusters, len(nodes)))
        adj_matrix = nx.adjacency_matrix(graph, nodelist=nodes)

        clustering = SpectralClustering(
            n_clusters=n_clusters,
            affinity="precomputed",
            assign_labels="kmeans",
            random_state=42,
        )
        labels = clustering.fit_predict(adj_matrix.toarray())

        return {node: int(label) for node, label in zip(nodes, labels)}

    def calculate_modularity(self, graph: nx.Graph, partition: dict[int, int]) -> float:
        """
        Calcula modularidade de uma particao.

        Returns:
            Valor de modularidade Q.
        """
        if graph.number_of_edges() == 0 or not partition:
            return 0.0
        communities = self._partition_to_communities(partition)
        return float(nx.algorithms.community.modularity(graph, communities, weight="weight"))


def detect_communities(graph: nx.Graph, method: str = "louvain", **kwargs) -> dict[int, int]:
    """
    Detecta comunidades no grafo usando o método especificado.
    
    Args:
        graph: Grafo networkx
        method: 'louvain', 'label_propagation' ou 'spectral'
        **kwargs: Parâmetros específicos do método
        
    Returns:
        Dicionário {node_id: community_id}
    """
    detector = CommunityDetector()
    
    if method == "louvain":
        return detector.detect_louvain(graph, **kwargs)
    if method == "label_propagation":
        return detector.detect_label_propagation(graph)
    if method == "spectral":
        return detector.detect_spectral(graph, **kwargs)
    raise ValueError(f"Metodo desconhecido: {method}")


def compare_community_methods(graph: nx.Graph) -> dict[str, dict[str, float | int]]:
    """
    Executa metodos de comunidades e compara por modularidade.

    Returns:
        Dicionario com modularidade e numero de comunidades por metodo.
    """
    detector = CommunityDetector()
    methods = {
        "louvain": detector.detect_louvain(graph),
        "label_propagation": detector.detect_label_propagation(graph),
    }

    comparison: dict[str, dict[str, float | int]] = {}
    for method_name, partition in methods.items():
        comparison[method_name] = {
            "modularity": detector.calculate_modularity(graph, partition),
            "num_communities": len(set(partition.values())) if partition else 0,
        }

    return comparison
