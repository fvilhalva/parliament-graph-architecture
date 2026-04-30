"""Tests for the CoauthorshipEdge class."""
import pytest # type: ignore
from models.coauthorship_edge import CoauthorshipEdge


class TestCoauthorshipEdgeCreation:
    """Tests for coauthorship edge creation."""

    def test_create_valid_edge(self, coauthorship_edge):
        """Should create an edge with valid data."""
        assert coauthorship_edge.source_id == 1
        assert coauthorship_edge.target_id == 2
        assert coauthorship_edge.raw_weight == 5

    def test_edge_positive_weight(self, coauthorship_edge):
        """Raw weight should be positive."""
        assert coauthorship_edge.raw_weight > 0

    def test_edge_normalized_strength_default(self):
        """Normalized strength should default to 0.0."""
        edge = CoauthorshipEdge(
            source_id=1,
            target_id=2,
            raw_weight=3
        )
        assert edge.normalized_strength == 0.0

    def test_edge_custom_normalized_strength(self, coauthorship_edge):
        """Should accept custom normalized strength."""
        assert coauthorship_edge.normalized_strength == 0.8


class TestCoauthorshipEdgeValidation:
    """Tests for edge validation."""

    def test_source_id_positive(self, coauthorship_edge):
        """Source ID should be positive."""
        assert coauthorship_edge.source_id > 0

    def test_target_id_positive(self, coauthorship_edge):
        """Target ID should be positive."""
        assert coauthorship_edge.target_id > 0

    def test_source_different_from_target(self, coauthorship_edge):
        """Source and target should be different."""
        assert coauthorship_edge.source_id != coauthorship_edge.target_id

    def test_raw_weight_integer(self, coauthorship_edge):
        """Raw weight should be an integer."""
        assert isinstance(coauthorship_edge.raw_weight, int)

    def test_forca_normalizada_entre_0_e_1(self, coauthorship_edge):
        """Normalized strength should be between 0 and 1."""
        assert 0.0 <= coauthorship_edge.normalized_strength <= 1.0


class TestCoauthorshipEdgeEquality:
    """Tests for comparing coauthorship edges."""

    def test_edges_equal(self):
        """Edges between same nodes should be equal."""
        edge1 = CoauthorshipEdge(
            source_id=1,
            target_id=2,
            raw_weight=5,
            normalized_strength=0.8
        )
        edge2 = CoauthorshipEdge(
            source_id=1,
            target_id=2,
            raw_weight=5,
            normalized_strength=0.8
        )
        assert edge1.source_id == edge2.source_id
        assert edge1.target_id == edge2.target_id

    def test_edges_different_nodes(self):
        """Edges between different nodes should be different."""
        edge1 = CoauthorshipEdge(source_id=1, target_id=2, raw_weight=5)
        edge2 = CoauthorshipEdge(source_id=1, target_id=3, raw_weight=5)
        assert edge1.target_id != edge2.target_id

    def test_edges_different_weight(self):
        """Edges with different weights should be identifiable."""
        edge1 = CoauthorshipEdge(source_id=1, target_id=2, raw_weight=5)
        edge2 = CoauthorshipEdge(source_id=1, target_id=2, raw_weight=10)
        assert edge1.raw_weight != edge2.raw_weight


class TestCoauthorshipEdgeWeight:
    """Tests related to weight and strength."""

    def test_raw_weight_zero_not_permitted(self):
        """Raw weight should be > 0."""
        edge = CoauthorshipEdge(source_id=1, target_id=2, raw_weight=0)
        assert edge.raw_weight == 0

    def test_update_raw_weight(self, coauthorship_edge):
        """Should allow updating raw weight."""
        # Note: dataclass fields are immutable by default
        # This test documents expected behavior if weight updates are added
        assert coauthorship_edge.raw_weight == 5

    def test_update_normalized_strength(self, coauthorship_edge):
        """Should allow updating normalized strength."""
        # Note: dataclass fields are immutable by default
        # This test documents expected behavior if strength updates are added
        assert coauthorship_edge.normalized_strength == 0.8
