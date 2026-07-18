"""JSON persistence for :class:`AnalysisResult` instances.

One file per year, human-readable, versionable. The repository is the sole
place where round-tripping between the typed dataclasses of ``core/algorithms``
and their on-disk representation happens — the ``core/`` layer stays serialisation-
agnostic.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from core.algorithms.analysis_result import (
    AnalysisResult,
    MethodSummary,
    PartitionAgreement,
)
from core.algorithms.community_composition import CommunityCompositionResult
from core.algorithms.concentration import ConcentrationResult
from core.algorithms.relatorship import RelatorshipResult
from core.algorithms.validation import NullModelResult, PermutationResult

# Decimal precision for on-disk values. Kept at 6 to preserve enough resolution
# for correlations while keeping JSON files short and legible.
_ROUND_DIGITS = 6


def _round(value: float) -> float:
    """Round while propagating NaN unchanged (JSON does not encode NaN)."""
    if value != value:  # NaN check
        return math.nan
    return round(float(value), _ROUND_DIGITS)


def _encode(obj: Any) -> Any:
    """Recursively convert dataclasses / mappings / floats for JSON dumping."""
    if is_dataclass(obj):
        return _encode(asdict(obj))
    if isinstance(obj, dict):
        return {str(k): _encode(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_encode(v) for v in obj]
    if isinstance(obj, float):
        return _round(obj)
    return obj


class AnalysisRepository:
    """Persist :class:`AnalysisResult` instances to ``data/analysis/*.json``."""

    def __init__(self, output_dir: Path | str) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, year: int) -> Path:
        return self.output_dir / f"analysis_{year}.json"

    def save(self, result: AnalysisResult) -> Path:
        """Serialise ``result`` as ``analysis_{year}.json``. Returns the path."""
        payload = _encode(result)
        # ``allow_nan=False`` would blow up when correlation is undefined; the
        # standard library's default emits ``NaN`` which is not strict JSON but
        # is universally decoded back to NaN by pandas/numpy consumers.
        output_file = self._path_for(result.year)
        output_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return output_file

    def load(self, year: int) -> AnalysisResult:
        """Load ``analysis_{year}.json`` back into a typed AnalysisResult."""
        path = self._path_for(year)
        if not path.exists():
            raise FileNotFoundError(f"Analysis result not found for {year}: {path}")
        raw = json.loads(path.read_text(encoding="utf-8"))
        return _decode(raw)


# --- decoding ---------------------------------------------------------------


def _decode(payload: dict) -> AnalysisResult:
    """Inverse of :func:`_encode` for :class:`AnalysisResult`."""
    concentration_raw = payload.get("concentration") or {}
    concentration = {
        metric: ConcentrationResult(
            metric=data.get("metric", metric),
            gini=float(data.get("gini", 0.0)),
            top_share={
                float(k): float(v) for k, v in (data.get("top_share") or {}).items()
            },
            n=int(data.get("n", 0)),
        )
        for metric, data in concentration_raw.items()
    }

    community_composition_raw = payload.get("community_composition")
    community_composition = (
        CommunityCompositionResult(
            num_communities=int(community_composition_raw.get("num_communities", 0)),
            num_multiparty=int(community_composition_raw.get("num_multiparty", 0)),
            multiparty_fraction=float(community_composition_raw.get("multiparty_fraction", 0.0)),
            mean_purity=float(community_composition_raw.get("mean_purity", 0.0)),
            coalition_fraction=float(community_composition_raw.get("coalition_fraction", 0.0)),
            details=list(community_composition_raw.get("details") or []),
        )
        if community_composition_raw
        else None
    )

    null_model_raw = payload.get("null_model") or {}
    null_model = NullModelResult(
        q_observed=float(null_model_raw.get("q_observed", 0.0)),
        q_null_mean=float(null_model_raw.get("q_null_mean", 0.0)),
        q_null_std=float(null_model_raw.get("q_null_std", 0.0)),
        p_value=float(null_model_raw.get("p_value", 1.0)),
        n_permutations=int(null_model_raw.get("n_permutations", 0)),
        significant=bool(null_model_raw.get("significant", False)),
        alpha=float(null_model_raw.get("alpha", 0.05)),
    )

    def _permutation(name: str) -> PermutationResult | None:
        raw = payload.get(name)
        if not raw:
            return None
        return PermutationResult(
            statistic_observed=float(raw.get("statistic_observed", float("nan"))),
            statistic_null_mean=float(raw.get("statistic_null_mean", float("nan"))),
            statistic_null_std=float(raw.get("statistic_null_std", float("nan"))),
            p_value=float(raw.get("p_value", 1.0)),
            n_permutations=int(raw.get("n_permutations", 0)),
            significant=bool(raw.get("significant", False)),
            two_sided=bool(raw.get("two_sided", True)),
            alpha=float(raw.get("alpha", 0.05)),
            valid=bool(raw.get("valid", True)),
        )

    pp3_raw = payload.get("pp3_relatorship")
    pp3_relatorship = (
        RelatorshipResult(
            metric=str(pp3_raw.get("metric", "betweenness_centrality")),
            spearman_rho=float(pp3_raw.get("spearman_rho", float("nan"))),
            p_value=float(pp3_raw.get("p_value", float("nan"))),
            n=int(pp3_raw.get("n", 0)),
            n_with_relatorship=int(pp3_raw.get("n_with_relatorship", 0)),
            n_off_graph_relators=int(pp3_raw.get("n_off_graph_relators", 0)),
            significant=bool(pp3_raw.get("significant", False)),
            alpha=float(pp3_raw.get("alpha", 0.05)),
            valid=bool(pp3_raw.get("valid", True)),
        )
        if pp3_raw
        else None
    )

    louvain_raw = payload.get("louvain") or {}
    label_prop_raw = payload.get("label_propagation") or {}
    agreement_raw = payload.get("partition_agreement") or {}

    return AnalysisResult(
        year=int(payload["year"]),
        n_nodes=int(payload.get("n_nodes", 0)),
        n_edges=int(payload.get("n_edges", 0)),
        density=float(payload.get("density", 0.0)),
        max_authors=int(payload.get("max_authors", 30)),
        n_permutations=int(payload.get("n_permutations", 0)),
        timestamp=str(payload.get("timestamp", "")),
        louvain=MethodSummary(
            modularity=float(louvain_raw.get("modularity", 0.0)),
            num_communities=int(louvain_raw.get("num_communities", 0)),
        ),
        label_propagation=MethodSummary(
            modularity=float(label_prop_raw.get("modularity", 0.0)),
            num_communities=int(label_prop_raw.get("num_communities", 0)),
        ),
        partition_agreement=PartitionAgreement(
            adjusted_rand_index=float(agreement_raw.get("adjusted_rand_index", 0.0)),
            louvain_num_communities=int(agreement_raw.get("louvain_num_communities", 0)),
            label_propagation_num_communities=int(
                agreement_raw.get("label_propagation_num_communities", 0)
            ),
        ),
        null_model=null_model,
        concentration=concentration,
        community_composition=community_composition,
        party_size_vs_mean_betweenness=_permutation("party_size_vs_mean_betweenness"),
        party_degree_vs_betweenness=_permutation("party_degree_vs_betweenness"),
        pp3_relatorship=pp3_relatorship,
    )
