"""CSV persistence for deputy and coauthorship metrics."""
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

import pandas as pd  # type: ignore


class CsvRepository:
    """Persists computed network metrics to CSV files."""

    def __init__(self, output_dir: Path | str) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_deputy_metrics(self, deputies: list, year: int) -> Path:
        """Export per-deputy centrality metrics for the given year.

        Args:
            deputies: List of Deputy dataclasses with computed metrics.
            year: Reference year used in the output filename.

        Returns:
            Path to the generated CSV file.
        """
        records = []

        for deputy in deputies:
            deputy_dict = asdict(deputy)
            records.append(
                {
                    "id_deputado": deputy_dict.get("id"),
                    "nome": deputy_dict.get("name"),
                    "sigla_partido": deputy_dict.get("party_code"),
                    "sigla_uf": deputy_dict.get("state_code"),
                    "weighted_degree": deputy_dict.get("weighted_degree", 0.0),
                    "degree_centrality": deputy_dict.get("degree_centrality", 0.0),
                    "betweenness_centrality": deputy_dict.get("betweenness_centrality", 0.0),
                    "closeness_centrality": deputy_dict.get("closeness_centrality", 0.0),
                    "eigenvector_centrality": deputy_dict.get("eigenvector_centrality", 0.0),
                }
            )

        data_frame = pd.DataFrame(records)
        data_frame = data_frame.sort_values(
            by=["degree_centrality", "betweenness_centrality"],
            ascending=False,
        )

        output_file = self.output_dir / f"deputados_metricas_{year}.csv"
        data_frame.to_csv(output_file, index=False, encoding="utf-8-sig")
        return output_file

    def export_coauthorship_metrics(self, coauthorships: Iterable, year: int) -> Path:
        """Export co-authorship edges with their weights.

        Args:
            coauthorships: Iterable of edge-like objects. Each item may be either
                a tuple ``(source_id, target_id, weight)`` or an object exposing
                ``source_id``, ``target_id`` and a weight attribute (``normalized_strength``
                or ``raw_weight``).
            year: Reference year used in the output filename.

        Returns:
            Path to the generated CSV file.
        """
        records = []
        for edge in coauthorships:
            if isinstance(edge, tuple) and len(edge) == 3:
                source, target, weight = edge
            else:
                source = getattr(edge, "source_id")
                target = getattr(edge, "target_id")
                weight = getattr(edge, "normalized_strength", None)
                if not weight:
                    weight = getattr(edge, "raw_weight", 0)

            records.append(
                {
                    "source_id": source,
                    "target_id": target,
                    "weight": float(weight),
                }
            )

        data_frame = pd.DataFrame(records, columns=["source_id", "target_id", "weight"])
        data_frame = data_frame.sort_values(by="weight", ascending=False)

        output_file = self.output_dir / f"coauthorships_{year}.csv"
        data_frame.to_csv(output_file, index=False, encoding="utf-8-sig")
        return output_file

    # --- Backwards-compatible aliases (kept for one release) ---
    def exportar_metricas_deputados(self, deputados: list, ano: int) -> Path:
        """Deprecated alias for :meth:`export_deputy_metrics`."""
        return self.export_deputy_metrics(deputados, ano)

    def exportar_metricas_coautorias(self, coautorias: Iterable, ano: int) -> Path:
        """Deprecated alias for :meth:`export_coauthorship_metrics`."""
        return self.export_coauthorship_metrics(coautorias, ano)
