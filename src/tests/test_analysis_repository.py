"""Round-trip tests for AnalysisRepository (JSON persistence)."""

import json
import math

import pytest

from core.algorithms.analysis_result import (
    AnalysisResult,
    MethodSummary,
    PartitionAgreement,
)
from core.algorithms.community_composition import CommunityCompositionResult
from core.algorithms.concentration import ConcentrationResult
from core.algorithms.relatorship import RelatorshipResult
from core.algorithms.validation import NullModelResult, PermutationResult
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
            adjusted_rand_index=0.72,
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
        concentration={
            "weighted_degree": ConcentrationResult(
                metric="weighted_degree",
                gini=0.566,
                top_share={0.05: 0.297, 0.10: 0.439, 0.20: 0.625},
                n=331,
            ),
            "betweenness_centrality": ConcentrationResult(
                metric="betweenness_centrality",
                gini=0.801,
                top_share={0.05: 0.467, 0.10: 0.650, 0.20: 0.838},
                n=331,
            ),
        },
        community_composition=CommunityCompositionResult(
            num_communities=11,
            num_multiparty=10,
            multiparty_fraction=0.9091,
            mean_purity=0.4984,
            coalition_fraction=0.4545,
            details=[
                {"community_id": 0, "size": 30, "num_parties": 5, "dominant_party": "PL", "purity": 0.5}
            ],
        ),
        party_size_vs_mean_betweenness=PermutationResult(
            statistic_observed=0.5121,
            statistic_null_mean=0.194,
            statistic_null_std=0.2138,
            p_value=0.05,
            n_permutations=200,
            significant=False,
            two_sided=False,
        ),
        party_degree_vs_betweenness=PermutationResult(
            statistic_observed=0.2596,
            statistic_null_mean=0.199,
            statistic_null_std=0.2529,
            p_value=0.44,
            n_permutations=200,
            significant=False,
            two_sided=True,
        ),
        pp3_relatorship=RelatorshipResult(
            metric="betweenness_centrality",
            spearman_rho=0.42,
            p_value=0.001,
            n=331,
            n_with_relatorship=275,
            n_off_graph_relators=160,
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

    def test_load_recovers_null_model(self, tmp_path):
        repo = AnalysisRepository(tmp_path)
        repo.save(_sample_result())
        loaded = repo.load(2025)
        assert loaded.null_model.q_observed == pytest.approx(0.6364)
        assert loaded.null_model.significant is True
        assert loaded.null_model.p_value == pytest.approx(0.0)

    def test_load_recovers_concentration(self, tmp_path):
        repo = AnalysisRepository(tmp_path)
        repo.save(_sample_result())
        loaded = repo.load(2025)
        assert set(loaded.concentration.keys()) == {"weighted_degree", "betweenness_centrality"}
        conc = loaded.concentration["betweenness_centrality"]
        assert conc.gini == pytest.approx(0.801)
        assert conc.top_share[0.05] == pytest.approx(0.467)

    def test_load_recovers_composition(self, tmp_path):
        repo = AnalysisRepository(tmp_path)
        repo.save(_sample_result())
        loaded = repo.load(2025)
        composition = loaded.community_composition
        assert composition is not None
        assert composition.num_communities == 11
        assert composition.verdict == "coalizões"

    def test_load_recovers_permutation_tests(self, tmp_path):
        repo = AnalysisRepository(tmp_path)
        repo.save(_sample_result())
        loaded = repo.load(2025)
        assert loaded.party_size_vs_mean_betweenness is not None
        assert loaded.party_size_vs_mean_betweenness.two_sided is False
        assert loaded.party_degree_vs_betweenness is not None
        assert loaded.party_degree_vs_betweenness.two_sided is True

    def test_load_recovers_pp3(self, tmp_path):
        repo = AnalysisRepository(tmp_path)
        repo.save(_sample_result())
        loaded = repo.load(2025)
        assert loaded.pp3_relatorship is not None
        assert loaded.pp3_relatorship.spearman_rho == pytest.approx(0.42)
        assert loaded.pp3_relatorship.n_off_graph_relators == 160
        assert loaded.pp3_relatorship.significant is True

    def test_missing_file_raises(self, tmp_path):
        repo = AnalysisRepository(tmp_path)
        with pytest.raises(FileNotFoundError):
            repo.load(9999)

    def test_json_is_human_readable(self, tmp_path):
        repo = AnalysisRepository(tmp_path)
        path = repo.save(_sample_result())
        text = path.read_text(encoding="utf-8")
        # Indented, valid JSON.
        assert "\n" in text
        parsed = json.loads(text)
        assert parsed["year"] == 2025
        assert parsed["louvain"]["modularity"] == pytest.approx(0.6364)
