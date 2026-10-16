"""Tests for the centralized application Config (pydantic-settings)."""
from config import Config


class TestAnalysisYears:
    """Tests for the configurable temporal analysis window."""

    def test_default_window(self):
        """Without an override, the window matches the thesis's 2022-2025 study."""
        assert Config().ANALYSIS_YEARS == [2022, 2023, 2024, 2025]

    def test_override_via_environment_variable(self, monkeypatch):
        """A JSON array in ANALYSIS_YEARS overrides the default window."""
        monkeypatch.setenv("ANALYSIS_YEARS", "[2023,2024]")
        assert Config().ANALYSIS_YEARS == [2023, 2024]

    def test_override_via_legacy_alias(self, monkeypatch):
        """The Portuguese alias ANOS_ANALISE is also accepted.

        AliasChoices resolves the primary name first. In this Docker service,
        ``docker-compose.yml``'s ``env_file: .env`` injects every key from
        ``.env`` -- including ``ANALYSIS_YEARS`` -- as a real OS environment
        variable before Python even starts, so it must be removed explicitly
        for the alias to be reachable.
        """
        monkeypatch.delenv("ANALYSIS_YEARS", raising=False)
        monkeypatch.setenv("ANOS_ANALISE", "[2025]")
        assert Config(_env_file=None).ANALYSIS_YEARS == [2025]


class TestMaxAuthorsPerProposal:
    """Tests for the mass-signature filter threshold."""

    def test_default_value(self):
        """Without an override, the threshold matches the thesis's max_authors=30."""
        assert Config().MAX_AUTHORS_PER_PROPOSAL == 30

    def test_override_via_environment_variable(self, monkeypatch):
        monkeypatch.setenv("MAX_AUTHORS_PER_PROPOSAL", "40")
        assert Config().MAX_AUTHORS_PER_PROPOSAL == 40
