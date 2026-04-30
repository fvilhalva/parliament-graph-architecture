"""Parliamentary co-authorship network graph construction and analysis."""
from typing import Dict, List, Optional, Tuple
import networkx as nx # type: ignore
from itertools import combinations

# Mapping for duplicate deputy IDs
ID_MAPPER = {
    130398: 220657,  # Maps phantom ID to real André Fernandes ID
}

class ParliamentaryGraph:
    """Builds and analyzes weighted, undirected parliamentary co-authorship networks.
    
    Represents a graph G = (V, E, w) where:
    - V: set of deputies
    - E: set of co-authorship edges
    - w: edge weight function representing co-authorship strength
    
    Attributes:
        graph: NetworkX Graph instance
        deputies: Mapping of deputy_id -> Deputy object
        propositions: List of Proposition objects
        coauthorships: List of CoauthorshipEdge objects
        year: Analysis year
    """
    
    def __init__(
        self,
        deputies: Optional[Dict] = None,
        propositions: Optional[List] = None,
        coauthorships: Optional[List] = None,
        year: Optional[int] = None
    ) -> None:
        """Initialize parliamentary graph with empty structure."""
        self.graph = nx.Graph()
        self.deputies = deputies or {}
        self.propositions = propositions or []
        self.coauthorships = coauthorships or []
        self.year = year
    
    def build(self) -> None:
        """Build the co-authorship network from propositions.
        
        Applies weight normalization by number of authors to mitigate
        distortions caused by propositions with many co-authors.
        """
        # Weights by proposition type (relative importance)
        weights = {'PL': 10, 'PEC': 1, 'PLP': 5}

        for coauthorship in self.coauthorships:
            # Get original author IDs from coauthorship
            original_ids = coauthorship.author_ids
            
            # Apply ID mapper to resolve duplicate entries
            deputy_ids = [ID_MAPPER.get(idx, idx) for idx in original_ids]
            
            # Remove duplicates from mapping
            deputy_ids = list(set(deputy_ids))
            
            # Apply weight by proposition type
            weight_value = weights.get(coauthorship.proposition_type, 1)
            
            # Normalize weight by number of authors to avoid mass-signature distortion
            # w(p)_ij = 1 / (n_authors - 1) * weight_type
            normalization_factor = 1 / (len(deputy_ids) - 1) if len(deputy_ids) > 1 else 1
            normalized_weight = weight_value * normalization_factor
            
            # Add or update edges in graph
            for u, v in combinations(deputy_ids, 2):
                if self.graph.has_edge(u, v):
                    self.graph[u][v]['weight'] += normalized_weight
                else:
                    self.graph.add_edge(u, v, weight=normalized_weight)

        # Enrich nodes with deputy metadata
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

        print(f"✅ Graph built! Nodes: {self.graph.number_of_nodes()} | Edges: {self.graph.number_of_edges()}")

    def search_deputies(self, query: str) -> List:
        """Search for deputies by ID or name.
        
        Args:
            query: Deputy ID (numeric) or name substring
            
        Returns:
            List of matching Deputy objects
        """
        # Search by ID if query is numeric
        if str(query).isdigit():
            deputy_id = int(query)
            deputy = self.deputies.get(deputy_id)
            return [deputy] if deputy else []
        
        # Search by name substring (case-insensitive)
        query_lower = str(query).lower()
        results = []
        for deputy in self.deputies.values():
            if query_lower in deputy.name.lower():
                results.append(deputy)
        return results
    
    def display_deputy_profile(self, query: str) -> None:
        """Display detailed profile of a deputy.
        
        Args:
            query: Deputy ID or name substring to search
        """
        deputies = self.search_deputies(query)
        if not deputies:
            print(f"⚠️  No deputy found for: {query}")
            return
        
        print(f"\n🔍 Search results for '{query}':")
        print("-" * 50)
        for deputy in deputies:
            degree = (
                self.graph.degree(deputy.id, weight='weight') 
                if self.graph.has_node(deputy.id) 
                else 0
            )
            print(f"Name:           {deputy.name}")
            print(f"ID:             {deputy.id}")
            print(f"Party/State:    {deputy.party_code}/{deputy.state_code}")
            print(f"Weighted Degree: {degree:.2f}")
            print("-" * 50)

    def compute_degree_centrality(self) -> List:
        """Compute weighted degree centrality for all deputies.
        
        Returns list of Deputy objects sorted by degree centrality,
        normalized by total network strength.
        
        Returns:
            List of Deputy objects with updated centrality metrics
        """
        weighted_strengths = dict(self.graph.degree(weight='weight'))
        total_strength = sum(weighted_strengths.values()) if weighted_strengths else 1
        
        # Sort by weighted degree (descending)
        sorted_deputies = sorted(weighted_strengths.items(), key=lambda x: x[1], reverse=True)

        results = []
        for deputy_id, strength in sorted_deputies:
            deputy = self.deputies.get(deputy_id, {})
            # Normalize strength by total network strength for cross-year comparability
            normalized_centrality = strength / total_strength
            deputy.weighted_degree = strength
            deputy.degree_centrality = normalized_centrality
            results.append(deputy)
        
        return results

    def compute_betweenness_centrality(self, normalized: bool = True) -> List:
        """Compute betweenness centrality for all deputies.
        
        Betweenness measures how often a deputy lies on shortest paths
        between other pairs in the network.
        
        Args:
            normalized: If True, normalize by (n-1)(n-2)/2 for undirected graphs
            
        Returns:
            List of Deputy objects with updated betweenness metrics
        """
        # Calculate betweenness with weighted edges
        betweenness_scores = nx.betweenness_centrality(
            self.graph, 
            weight='weight',
            normalized=normalized
        )
        
        # Sort by betweenness (descending)
        sorted_deputies = sorted(betweenness_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for deputy_id, betweenness_score in sorted_deputies:
            deputy = self.deputies.get(deputy_id, {})
            deputy.betweenness_centrality = betweenness_score
            results.append(deputy)

        return results

    def advanced_structural_analysis(self) -> None:
        """Perform advanced network structural analysis.
        
        Identifies articulation points (cut vertices), density, 
        connected components, and graph diameter.
        """
        print("\n" + "!"*60)
        print(f"ADVANCED STRUCTURAL ANALYSIS - {self.year}")
        print("!"*60)
        
        # 1. Articulation points (cut vertices)
        articulation_points = list(nx.articulation_points(self.graph))
        print(f"\n⚠️ Articulation points found: {len(articulation_points)}")
        for deputy_id in articulation_points[:5]:  # Show top 5
            deputy_info = self.deputies.get(deputy_id)
            name = deputy_info.name if deputy_info else deputy_id
            print(f" - {name} is essential for network connectivity.")
        
        # 2. Graph density
        density = nx.density(self.graph)
        print(f"\n📊 Network Density: {density:.4f}")

        # 3. Connected components
        num_components = nx.number_connected_components(self.graph)
        print(f"🔗 Number of isolated groups: {num_components}")
        
        # 4. Diameter (only works if graph is fully connected)
        if num_components == 1:
            diameter = nx.diameter(self.graph, weight='weight')
            print(f"📏 Network Diameter: {diameter:.4f}")

    def identify_critical_deputies(self, query: str = "Luisa Canziani") -> None:
        """Identify network dependencies if a deputy is removed.
        
        Shows which deputies/groups become isolated if the target deputy
        is removed from the network (vulnerability analysis).
        
        Args:
            query: Deputy name or ID to analyze
        """
        # 1. Find target deputy ID
        results = self.search_deputies(query)
        if not results:
            print(f"❌ Deputy {query} not found.")
            return
        
        target_deputy_id = results[0].id
        target_name = results[0].name

        # 2. Create temporary copy to avoid modifying original
        temp_graph = self.graph.copy()
        temp_graph.remove_node(target_deputy_id)

        # 3. Get new connected components
        # connected_components returns lists of nodes still connected
        components = list(nx.connected_components(temp_graph))
        
        # Sort by size (largest first = Giant Component)
        components.sort(key=len, reverse=True)

        print("\n" + "!"*60)
        print(f"VULNERABILITY ANALYSIS: {target_name}")
        print("!"*60)

        if len(components) > 1:
            print(f"⚠️ Removing {target_name} fragments graph into {len(components)} parts.")
            print("\n--- ISOLATED GROUPS ---")
            
            # Skip first component (index 0) as it's the main mass
            for i, component in enumerate(components[1:], 1):
                print(f"\nSubgroup {i} ({len(component)} deputies):")
                for node_id in component:
                    deputy_info = self.deputies.get(node_id)
                    name = deputy_info.name if deputy_info else f"ID: {node_id}"
                    party = deputy_info.party_code if deputy_info else "N/A"
                    print(f" - {name} ({party})")
        else:
            print(f"✅ Removing {target_name} doesn't isolate any groups (Resilient Network).")
        print("!"*60)

    def filter_parties_by_degree(self) -> None:
        """Filter and rank parties by average weighted degree."""
        pass
    
    def filter_parties_by_betweenness(self) -> None:
        """Filter and rank parties by average betweenness centrality."""
        pass
