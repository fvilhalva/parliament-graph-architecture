"""Parliamentary co-authorship network graph construction and analysis."""
from __future__ import annotations

from itertools import combinations
from typing import Dict, List, Optional

import networkx as nx  # type: ignore
import pandas as pd  # type: ignore

from config import setup_logger
from config.constants import DEPUTY_ID_ALIASES, PROPOSITION_TYPE_WEIGHTS
from core.algorithms.metrics import (
    calculate_closeness_centrality,
    calculate_eigenvector_centrality,
)
from models.deputy import Deputy

logger = setup_logger(__name__)


class ParliamentaryGraph:
    """Builds and analyses a weighted, undirected parliamentary co-authorship network.

    Represents a graph ``G = (V, E, w)`` where:

    * ``V``: set of deputies.
    * ``E``: set of co-authorship edges.
    * ``w``: edge weight function representing co-authorship strength.

    Attributes:
        graph: NetworkX ``Graph`` instance.
        deputies: Mapping ``deputy_id -> Deputy``.
        propositions: List of ``Proposition`` objects.
        coauthorships: List of co-authorship objects.
        year: Analysis year.
        proposition_weights: Per-type weight multipliers used during graph build.
    """

    def __init__(
        self,
        deputies: Optional[Dict] = None,
        propositions: Optional[List] = None,
        coauthorships: Optional[List] = None,
        year: Optional[int] = None,
        proposition_weights: Optional[Dict[str, float]] = None,
    ) -> None:
        """Initialize parliamentary graph with empty structure.

        Args:
            deputies: Mapping of deputy IDs to ``Deputy`` instances.
            propositions: List of propositions.
            coauthorships: List of co-authorship records (proposition-like objects
                exposing ``author_ids`` and ``proposition_type``).
            year: Reference year.
            proposition_weights: Optional override for the per-type weight
                multipliers. Defaults to :data:`PROPOSITION_TYPE_WEIGHTS`.
        """
        self.graph = nx.Graph()
        self.deputies = deputies or {}
        self.propositions = propositions or []
        self.coauthorships = coauthorships or []
        self.year = year
        self.proposition_weights = (
            dict(proposition_weights) if proposition_weights is not None else dict(PROPOSITION_TYPE_WEIGHTS)
        )

    # ------------------------------------------------------------------ build
    def build(self) -> None:
        """Build the co-authorship network from propositions.

        Applies weight normalization by number of authors to mitigate
        distortions caused by propositions with many co-authors.
        """
        for coauthorship in self.coauthorships:
            original_ids = coauthorship.author_ids

            # Apply ID aliases to resolve duplicate Chamber entries.
            deputy_ids = [DEPUTY_ID_ALIASES.get(idx, idx) for idx in original_ids]

            # Remove duplicates introduced by aliasing.
            deputy_ids = list(set(deputy_ids))

            # Look up per-type weight (defaults to 1 if the type is unknown).
            weight_value = self.proposition_weights.get(coauthorship.proposition_type, 1)

            # Normalize by number of authors to avoid mass-signature distortion:
            # w(p)_ij = 1 / (n_authors - 1) * weight_type
            normalization_factor = 1 / (len(deputy_ids) - 1) if len(deputy_ids) > 1 else 1
            normalized_weight = weight_value * normalization_factor

            for u, v in combinations(deputy_ids, 2):
                if self.graph.has_edge(u, v):
                    self.graph[u][v]['weight'] += normalized_weight
                else:
                    self.graph.add_edge(u, v, weight=normalized_weight)

        # Enrich nodes with deputy metadata.
        for deputy_id in self.graph.nodes():
            deputy_info = self.deputies.get(deputy_id)
            if deputy_info:
                self.graph.nodes[deputy_id]['name'] = deputy_info.name
                self.graph.nodes[deputy_id]['party_code'] = deputy_info.party_code
                self.graph.nodes[deputy_id]['state_code'] = deputy_info.state_code
            else:
                self.graph.nodes[deputy_id]['name'] = f"Unknown ({deputy_id})"
                self.graph.nodes[deputy_id]['party_code'] = "N/A"
                self.graph.nodes[deputy_id]['state_code'] = "N/A"

        logger.info(
            "Graph built. Nodes: %d | Edges: %d",
            self.graph.number_of_nodes(),
            self.graph.number_of_edges(),
        )

    # ----------------------------------------------------------------- search
    def search_deputies(self, query: str) -> List[Deputy]:
        """Search for deputies by ID or name substring."""
        if str(query).isdigit():
            deputy_id = int(query)
            deputy = self.deputies.get(deputy_id)
            return [deputy] if deputy else []

        query_lower = str(query).lower()
        results = []
        for deputy in self.deputies.values():
            if query_lower in deputy.name.lower():
                results.append(deputy)
        return results

    def display_deputy_profile(self, query: str) -> None:
        """Print a detailed profile of a deputy matching ``query``."""
        deputies = self.search_deputies(query)
        if not deputies:
            logger.warning("No deputy found for: %s", query)
            return

        logger.info("Search results for '%s':", query)
        for deputy in deputies:
            degree = (
                self.graph.degree(deputy.id, weight='weight')
                if self.graph.has_node(deputy.id)
                else 0
            )
            logger.info(
                "Name: %s | ID: %s | %s/%s | Weighted degree: %.2f",
                deputy.name,
                deputy.id,
                deputy.party_code,
                deputy.state_code,
                degree,
            )

    # ------------------------------------------------------- helper utilities
    def _resolve_deputy(self, deputy_id: int) -> Optional[Deputy]:
        """Return the ``Deputy`` for ``deputy_id`` or ``None`` if missing.

        Used by centrality methods so that ID misses do not crash the pipeline
        (a previous version assigned attributes to an empty ``dict`` fallback).
        """
        return self.deputies.get(deputy_id)

    # --------------------------------------------------------- centrality API
    # Note: each ``compute_*_centrality`` method mutates the matching ``Deputy``
    # objects in ``self.deputies`` AND returns a sorted list. The pipeline
    # should prefer :meth:`compute_all_centralities`, which runs every metric
    # in a single pass and returns the canonical ordered list.

    def compute_degree_centrality(self) -> List[Deputy]:
        """Compute weighted degree centrality.

        Returns:
            Deputies sorted by descending weighted degree.
        """
        weighted_strengths = dict(self.graph.degree(weight='weight'))
        total_strength = sum(weighted_strengths.values()) if weighted_strengths else 1

        sorted_pairs = sorted(weighted_strengths.items(), key=lambda x: x[1], reverse=True)

        results: List[Deputy] = []
        for deputy_id, strength in sorted_pairs:
            deputy = self._resolve_deputy(deputy_id)
            if deputy is None:
                continue
            deputy.weighted_degree = strength
            deputy.degree_centrality = strength / total_strength
            results.append(deputy)

        return results

    def compute_betweenness_centrality(self, normalized: bool = True) -> List[Deputy]:
        """Compute betweenness centrality.

        Args:
            normalized: If True, normalize by ``(n-1)(n-2)/2`` for undirected graphs.

        Returns:
            Deputies sorted by descending betweenness.
        """
        betweenness_scores = nx.betweenness_centrality(
            self.graph,
            weight='weight',
            normalized=normalized,
        )

        sorted_pairs = sorted(betweenness_scores.items(), key=lambda x: x[1], reverse=True)

        results: List[Deputy] = []
        for deputy_id, score in sorted_pairs:
            deputy = self._resolve_deputy(deputy_id)
            if deputy is None:
                continue
            deputy.betweenness_centrality = score
            results.append(deputy)

        return results

    def compute_closeness_centrality(self) -> List[Deputy]:
        """Compute closeness centrality and store it on each Deputy.

        Returns:
            Deputies sorted by descending closeness centrality.
        """
        scores = calculate_closeness_centrality(self.graph)
        sorted_pairs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results: List[Deputy] = []
        for deputy_id, score in sorted_pairs:
            deputy = self._resolve_deputy(deputy_id)
            if deputy is None:
                continue
            deputy.closeness_centrality = score
            results.append(deputy)
        return results

    def compute_eigenvector_centrality(self) -> List[Deputy]:
        """Compute eigenvector centrality and store it on each Deputy.

        The underlying NetworkX power-iteration solver can fail to converge
        on disconnected graphs; the metrics helper falls back to the NumPy
        implementation in that case.

        Returns:
            Deputies sorted by descending eigenvector centrality.
        """
        scores = calculate_eigenvector_centrality(self.graph)
        sorted_pairs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results: List[Deputy] = []
        for deputy_id, score in sorted_pairs:
            deputy = self._resolve_deputy(deputy_id)
            if deputy is None:
                continue
            deputy.eigenvector_centrality = score
            results.append(deputy)
        return results

    def compute_all_centralities(self) -> List[Deputy]:
        """Compute every centrality metric in sequence.

        Runs degree → betweenness → closeness → eigenvector, mutating each
        ``Deputy`` object exactly once per metric. Prefer this method in the
        pipeline; the per-metric methods are kept for unit testing.

        Returns:
            Deputies sorted by descending weighted degree (canonical order
            used by exports/visualisation).
        """
        ordered = self.compute_degree_centrality()
        self.compute_betweenness_centrality()
        self.compute_closeness_centrality()
        self.compute_eigenvector_centrality()
        return ordered

    # ------------------------------------------------------- structural views
    def advanced_structural_analysis(self) -> None:
        """Log a high-level structural summary (articulation points, density,
        components, diameter).
        """
        logger.info("ADVANCED STRUCTURAL ANALYSIS - %s", self.year)

        articulation_points = list(nx.articulation_points(self.graph))
        logger.info("Articulation points found: %d", len(articulation_points))
        for deputy_id in articulation_points[:5]:
            deputy_info = self.deputies.get(deputy_id)
            name = deputy_info.name if deputy_info else deputy_id
            logger.info("- %s is essential for network connectivity.", name)

        density = nx.density(self.graph)
        logger.info("Network density: %.4f", density)

        num_components = nx.number_connected_components(self.graph)
        logger.info("Number of isolated groups: %d", num_components)

        if num_components == 1:
            diameter = nx.diameter(self.graph, weight='weight')
            logger.info("Network diameter: %.4f", diameter)

    def identify_critical_deputies(self, query: str = "Luisa Canziani") -> None:
        """Report the network fragmentation caused by removing a target deputy."""
        results = self.search_deputies(query)
        if not results:
            logger.warning("Deputy %s not found.", query)
            return

        target_deputy_id = results[0].id
        target_name = results[0].name

        temp_graph = self.graph.copy()
        temp_graph.remove_node(target_deputy_id)

        components = list(nx.connected_components(temp_graph))
        components.sort(key=len, reverse=True)

        logger.info("VULNERABILITY ANALYSIS: %s", target_name)

        if len(components) > 1:
            logger.warning(
                "Removing %s fragments graph into %d parts.",
                target_name,
                len(components),
            )
            for i, component in enumerate(components[1:], 1):
                logger.info("Subgroup %d (%d deputies):", i, len(component))
                for node_id in component:
                    deputy_info = self.deputies.get(node_id)
                    name = deputy_info.name if deputy_info else f"ID: {node_id}"
                    party = deputy_info.party_code if deputy_info else "N/A"
                    logger.info(" - %s (%s)", name, party)
        else:
            logger.info(
                "Removing %s does not isolate any groups (resilient network).",
                target_name,
            )

    # -------------------------------------------------------- party analytics
    def filter_parties_by_degree(self, min_party_size: int = 1) -> pd.DataFrame:
        """Rank parties by mean weighted degree.

        Args:
            min_party_size: Drop parties whose number of deputies in the
                network is strictly below this threshold.

        Returns:
            DataFrame with columns ``party_code``, ``avg_weighted_degree``,
            ``num_deputies``, sorted by mean weighted degree (descending).
        """
        return self._aggregate_party_metric("weighted_degree", min_party_size, "avg_weighted_degree")

    def filter_parties_by_betweenness(self, min_party_size: int = 1) -> pd.DataFrame:
        """Rank parties by mean betweenness centrality.

        Args:
            min_party_size: Drop parties whose number of deputies in the
                network is strictly below this threshold.

        Returns:
            DataFrame with columns ``party_code``, ``avg_betweenness``,
            ``num_deputies``, sorted by mean betweenness (descending).
        """
        return self._aggregate_party_metric("betweenness_centrality", min_party_size, "avg_betweenness")

    def _aggregate_party_metric(
        self,
        metric_attr: str,
        min_party_size: int,
        output_column: str,
    ) -> pd.DataFrame:
        """Aggregate a per-deputy centrality field into a per-party ranking."""
        rows = []
        for deputy_id in self.graph.nodes():
            deputy = self.deputies.get(deputy_id)
            if deputy is None:
                continue
            rows.append(
                {
                    "party_code": deputy.party_code,
                    "value": getattr(deputy, metric_attr, 0.0),
                }
            )

        if not rows:
            return pd.DataFrame(columns=["party_code", output_column, "num_deputies"])

        frame = pd.DataFrame(rows)
        grouped = (
            frame.groupby("party_code")
            .agg(**{output_column: ("value", "mean"), "num_deputies": ("value", "count")})
            .reset_index()
        )
        grouped = grouped[grouped["num_deputies"] >= min_party_size]
        return grouped.sort_values(by=output_column, ascending=False).reset_index(drop=True)
