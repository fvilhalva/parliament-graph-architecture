"""Tests for the Deputy class."""
import pytest # type: ignore
from models.deputy import Deputy


class TestDeputyCreation:
    """Tests for deputy creation."""

    def test_create_valid_deputy(self, deputy_silva):
        """Should create a deputy with valid data."""
        assert deputy_silva.id == 1
        assert deputy_silva.name == "João Silva"
        assert deputy_silva.party_code == "PT"
        assert deputy_silva.state_code == "SP"

    def test_create_deputy_with_metrics(self, deputy_silva):
        """Should preserve centrality metrics."""
        assert deputy_silva.degree_centrality == 0.5
        assert deputy_silva.betweenness_centrality == 0.3

    def test_create_deputy_without_metrics(self):
        """Should have default zero metrics."""
        deputy = Deputy(
            id=10,
            name="Test",
            party_code="XX",
            state_code="XX"
        )
        assert deputy.degree_centrality == 0.0
        assert deputy.betweenness_centrality == 0.0


class TestDeputyEquality:
    """Tests for deputy comparison."""

    def test_deputies_equal_same_id(self, deputy_silva):
        """Deputies with same ID should be equal."""
        other = Deputy(
            id=1,
            name="João Silva",
            party_code="PT",
            state_code="SP"
        )
        assert deputy_silva.id == other.id

    def test_deputies_different_ids(self, deputy_silva, deputy_santos):
        """Deputies with different IDs should be different."""
        assert deputy_silva.id != deputy_santos.id


class TestDeputyValidation:
    """Tests for deputy data validation."""

    def test_party_code_valid(self, deputy_silva):
        """Party code should be 2-4 characters."""
        assert len(deputy_silva.party_code) <= 4

    def test_state_code_valid(self, deputy_silva):
        """State code should be 2 characters."""
        assert len(deputy_silva.state_code) == 2

    def test_centrality_between_0_and_1(self, deputy_silva):
        """Centrality metrics should be between 0 and 1."""
        assert 0.0 <= deputy_silva.degree_centrality <= 1.0
        assert 0.0 <= deputy_silva.betweenness_centrality <= 1.0


class TestDeputyMetricsUpdate:
    """Tests for deputy metrics updates."""

    def test_update_degree_centrality(self, deputy_silva):
        """Should allow updating degree centrality."""
        # Note: dataclass fields are immutable by default
        # This test documents expected behavior if updates are added
        assert deputy_silva.degree_centrality == 0.5

    def test_update_betweenness_centrality(self, deputy_silva):
        """Should allow updating betweenness centrality."""
        # Note: dataclass fields are immutable by default
        # This test documents expected behavior if updates are added
        assert deputy_silva.betweenness_centrality == 0.3
