"""Round-trip tests for AnalysisRepository (JSON persistence)."""

import json

import pytest

from core.algorithms.analysis_result import (
    AnalysisResult,
    MethodSummary,
    PartitionAgreement,
)
from core.algorithms.validation import NullModelResult
from repository import AnalysisRepository


def _sample_result(year: int = 2025) -> AnalysisResult:
    return AnalysisResult(
        year=year,
        n_nodes=331,
        n_edges=5396,
        density=0.0988,
        max_authors=30,
        n_permutations=200,
        timestamp="2026-05-25T22:00:00+00:00",
        louvain=MethodSummary(modularity=0.6364, num_communities=17),
        label_propagation=MethodSummary(modularity=0.4850, num_communities=11),
        partition_agreement=PartitionAgreement(
            adjusted_rand_index=0.442,
            louvain_num_communities=17,
            label_propagation_num_communities=11,
        ),
        null_model=NullModelResult(
            q_observed=0.6364,
            q_null_mean=0.1168,
            q_null_std=0.0028,
            p_value=0.0,
            n_permutations=200,
            significant=True,
        ),
    )


class TestAnalysisRepositoryRoundTrip:
    def test_save_creates_file(self, tmp_path):
        repo = AnalysisRepository(tmp_path)
        path = repo.save(_sample_result())
        assert path.exists()
        assert path.name == "analysis_2025.json"

    def test_load_recovers_scalars(self, tmp_path):
        repo = AnalysisRepository(tmp_path)
        repo.save(_sample_result())
        loaded = repo.load(2025)
        assert loaded.year == 2025
        assert loaded.n_nodes == 331
        assert loaded.n_edges == 5396
        assert loaded.max_authors == 30
        assert loaded.n_permutations == 200

    def test_load_recovers_louvain_summary(self, tmp_path):
        repo = AnalysisRepository(tmp_path)
        repo.save(_sample_result())
        loaded = repo.load(2025)
        assert loaded.louvain.modularity == pytest.approx(0.6364)
        assert loaded.louvain.num_communities == 17

    def test_load_recovers_label_propagation(self, tmp_path):
        repo = AnalysisRepository(tmp_path)
        repo.save(_sample_result())
        loaded = repo.load(2025)
        assert loaded.label_propagation.modularity == pytest.approx(0.4850)
        assert loaded.label_propagation.num_communities == 11

    def test_load_recovers_partition_agreement(self, tmp_path):
        repo = AnalysisRepository(tmp_path)
        repo.save(_sample_result())
        loaded = repo.load(2025)
        assert loaded.partition_agreement.adjusted_rand_index == pytest.approx(0.442)

    def test_load_recovers_null_model(self, tmp_path):
        repo = AnalysisRepository(tmp_path)
        repo.save(_sample_result())
        loaded = repo.load(2025)
        assert loaded.null_model.q_observed == pytest.approx(0.6364)
        assert loaded.null_model.significant is True
        assert loaded.null_model.p_value == pytest.approx(0.0)

    def test_missing_file_raises(self, tmp_path):
        repo = AnalysisRepository(tmp_path)
        with pytest.raises(FileNotFoundError):
            repo.load(9999)

    def test_json_is_human_readable(self, tmp_path):
        repo = AnalysisRepository(tmp_path)
        path = repo.save(_sample_result())
        text = path.read_text(encoding="utf-8")
        assert "\n" in text
        parsed = json.loads(text)
        assert parsed["year"] == 2025
        assert parsed["louvain"]["modularity"] == pytest.approx(0.6364)
