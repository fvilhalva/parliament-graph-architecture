"""Tests for the Proposition class."""
import pytest # type: ignore
from models.proposition import Proposition


class TestPropositionCreation:
    """Tests for proposition creation."""

    def test_create_valid_proposition(self, proposition_example):
        """Should create a proposition with valid data."""
        assert proposition_example.id == 100
        assert proposition_example.year == 2024

    def test_author_ids_list(self, proposition_example):
        """Authors should be a list of IDs."""
        assert isinstance(proposition_example.author_ids, list)
        assert all(isinstance(id, int) for id in proposition_example.author_ids)

    def test_proposition_no_authors(self):
        """Should allow proposition with no authors."""
        proposition = Proposition(
            id=50,
            year=2024,
            author_ids=[]
        )
        assert len(proposition.author_ids) == 0

    def test_proposition_multiple_authors(self, proposition_example):
        """Should support multiple authors."""
        assert len(proposition_example.author_ids) == 3
        assert 1 in proposition_example.author_ids
        assert 2 in proposition_example.author_ids


class TestPropositionValidation:
    """Tests for data validation."""

    def test_valid_year(self, proposition_example):
        """Year should be a valid integer."""
        assert isinstance(proposition_example.year, int)
        assert 1988 <= proposition_example.year <= 2026

    def test_positive_proposition_id(self, proposition_example):
        """Proposition ID should be positive."""
        assert proposition_example.id > 0


class TestPropositionEquality:
    """Tests for proposition comparison."""

    def test_propositions_same_id(self):
        """Propositions with same ID should be equal."""
        proposition1 = Proposition(
            id=100,
            year=2024,
            author_ids=[1, 2],
            proposition_type="PL"
        )
        proposition2 = Proposition(
            id=100,
            year=2024,
            author_ids=[1, 2],
            proposition_type="PL"
        )
        assert proposition1.id == proposition2.id

    def test_propositions_different_ids(self, proposition_example, proposition_other):
        """Propositions with different IDs should be different."""
        assert proposition_example.id != proposition_other.id


class TestPropositionAuthorship:
    """Tests related to authorship."""

    def test_deputy_is_author(self, proposition_example):
        """Should verify if deputy is an author."""
        assert 1 in proposition_example.author_ids
        assert 2 in proposition_example.author_ids
        assert 3 in proposition_example.author_ids

    def test_deputy_not_author(self, proposition_example):
        """Should verify if deputy is not an author."""
        assert 999 not in proposition_example.author_ids

    def test_number_of_authors(self, proposition_example):
        """Should count authors correctly."""
        assert len(proposition_example.author_ids) == 3
