"""Community detection algorithms for parliamentary networks."""

from __future__ import annotations

import networkx as nx
from networkx.algorithms.community import label_propagation_communities, louvain_communities
from sklearn.cluster import SpectralClustering  # type: ignore


class CommunityDetector:
    """Detects communities of deputies with strong co-authorship ties."""

    def __init__(self) -> None:
        """Initialize the community detector."""

    @staticmethod
    def _communities_to_partition(communities: list[set]) -> dict[int, int]:
        """Convert a list of node-sets into a ``{node_id: community_id}`` mapping."""
        partition: dict[int, int] = {}
        for community_id, nodes in enumerate(communities):
            for node in nodes:
                partition[node] = community_id
        return partition

    @staticmethod
    def _partition_to_communities(partition: dict[int, int]) -> list[set]:
        """Convert a ``{node_id: community_id}`` mapping into a list of node-sets."""
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
        """Detect communities using the Louvain algorithm.

        Args:
            graph: A NetworkX graph.
            resolution: Louvain resolution parameter.
            seed: Random seed for reproducibility.

        Returns:
            Mapping of ``{node_id: community_id}``.
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
        """Detect communities using label propagation.

        Returns:
            Mapping of ``{node_id: community_id}``.
        """
        if graph.number_of_nodes() == 0:
            return {}

        communities = [set(c) for c in label_propagation_communities(graph)]
        return self._communities_to_partition(communities)

    def detect_spectral(self, graph: nx.Graph, n_clusters: int = 5) -> dict[int, int]:
        """Detect communities using spectral clustering (scikit-learn).

        Args:
            graph: A NetworkX graph.
            n_clusters: Expected number of communities.

        Returns:
            Mapping of ``{node_id: community_id}``.
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
        """Calculate the modularity ``Q`` of a partition.

        Returns:
            Modularity score in ``[-0.5, 1]``.
        """
        if graph.number_of_edges() == 0 or not partition:
            return 0.0
        communities = self._partition_to_communities(partition)
        return float(nx.algorithms.community.modularity(graph, communities, weight="weight"))


def detect_communities(graph: nx.Graph, method: str = "louvain", **kwargs) -> dict[int, int]:
    """Detect communities using the specified method.

    Args:
        graph: A NetworkX graph.
        method: One of ``'louvain'``, ``'label_propagation'``, ``'spectral'``.
        **kwargs: Method-specific parameters.

    Returns:
        Mapping of ``{node_id: community_id}``.
    """
    detector = CommunityDetector()

    if method == "louvain":
        return detector.detect_louvain(graph, **kwargs)
    if method == "label_propagation":
        return detector.detect_label_propagation(graph)
    if method == "spectral":
        return detector.detect_spectral(graph, **kwargs)
    raise ValueError(f"Unknown community detection method: {method}")


def compare_community_methods(graph: nx.Graph) -> dict[str, dict[str, float | int]]:
    """Run multiple community detection methods and compare them by modularity.

    Returns:
        Mapping of method name to ``{'modularity': value, 'num_communities': count}``.
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
