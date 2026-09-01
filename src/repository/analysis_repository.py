"""JSON persistence for :class:`AnalysisResult` instances.

One file per year, human-readable, versionable. The repository is the sole
place where round-tripping between the typed dataclasses of ``core/algorithms``
and their on-disk representation happens — the ``core/`` layer stays
serialisation-agnostic.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from core.algorithms.analysis_result import (
    AnalysisResult,
    ConcentrationSummary,
    MethodSummary,
    PartitionAgreement,
)
from core.algorithms.validation import NullModelResult

# Decimal precision for on-disk values. Kept at 6 to preserve enough resolution
# while keeping JSON files short and legible.
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

    louvain_raw = payload.get("louvain") or {}
    label_prop_raw = payload.get("label_propagation") or {}
    agreement_raw = payload.get("partition_agreement") or {}

    concentration = {
        str(metric): ConcentrationSummary(
            gini=float(summary.get("gini", 0.0)),
            top10_share=float(summary.get("top10_share", 0.0)),
        )
        for metric, summary in (payload.get("concentration") or {}).items()
    }

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
    )
