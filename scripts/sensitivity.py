"""Sensitivity analysis of the mass-signature filter (``max_authors``).

Reproduces the numbers behind two tables of Chapter 5:

  - Effect of the mass-signature filter on density (filter on vs. off);
  - Sensitivity of the network to the ``max_authors`` threshold.

For a single reference year (default: 2025) it rebuilds the co-authorship
network under several configurations and reports, for each one, the number of
edges, the density and the Louvain modularity ``Q``:

  - ``max_authors`` in {20, 30, 40}         -> type filter + mass filter
  - "type only (no mass filter)"            -> type filter, mass filter disabled
  - "unfiltered"                            -> no type filter, no mass filter

The first four rows reuse :meth:`ChamberProcessor.process_raw_data`; the last
row reuses :meth:`ChamberProcessor.process_raw_data_unfiltered` (otherwise a
dead-code baseline). Nothing here is recomputed elsewhere: this script is the
reproducible source of the sensitivity/filter tables.

Run from the project root (needs the raw CSVs — cached locally by a previous
pipeline run, or downloaded on demand by the extractor):

    PYTHONPATH=src python3 scripts/sensitivity.py            # 2025
    PYTHONPATH=src python3 scripts/sensitivity.py 2024       # another year
"""
from __future__ import annotations

import sys
from pathlib import Path

import networkx as nx  # type: ignore
import pandas as pd  # type: ignore

# Make src/ importable without installing the package.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Config  # noqa: E402
from core import ParliamentaryGraph  # noqa: E402
from core.algorithms.community_detection import CommunityDetector  # noqa: E402
from extraction import ChamberExtractor  # noqa: E402
from processing import ChamberProcessor  # noqa: E402

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "analysis"

DEFAULT_YEAR = 2025
THRESHOLDS = [20, 30, 40]
NO_MASS_FILTER = 10**9  # effectively disables the mass-signature filter


def _measure(deputies: dict, propositions: list, coauthorships: list, year: int) -> tuple[int, float, float]:
    """Build the graph for one configuration and return (edges, density, Q)."""
    graph = ParliamentaryGraph(deputies, propositions, coauthorships, year)
    graph.build()

    detector = CommunityDetector()
    partition = detector.detect_louvain(graph.graph, seed=42)
    modularity = detector.calculate_modularity(graph.graph, partition) if partition else 0.0

    edges = graph.graph.number_of_edges()
    density = float(nx.density(graph.graph)) if graph.graph.number_of_nodes() > 1 else 0.0
    return edges, density, modularity


def run(year: int) -> pd.DataFrame:
    config = Config()
    extractor = ChamberExtractor(config)
    processor = ChamberProcessor()

    print(f"Extracting raw data for {year}...")
    raw_df = extractor.extract_raw_coauthorship_data(year)
    metadata_df = extractor.extract_propositions_metadata(year)

    rows: list[dict] = []

    def _add(label: str, deputy_map, groups, coauthorships, type_map) -> None:
        deputies, propositions, coauthorships_list = processor.convert_to_domain_objects(
            deputy_map, groups, coauthorships, type_map, year
        )
        edges, density, modularity = _measure(deputies, propositions, coauthorships_list, year)
        rows.append(
            {"config": label, "edges": edges, "density_pct": round(density * 100, 2), "q_louvain": round(modularity, 4)}
        )
        print(f"  {label:<28} edges={edges:>7}  density={density:6.2%}  Q={modularity:.4f}")

    # Type filter + mass filter, for each threshold.
    for threshold in THRESHOLDS:
        label = f"max_authors={threshold}"
        _add(label, *processor.process_raw_data(raw_df, metadata_df, max_authors=threshold))

    # Type filter kept, mass filter effectively disabled.
    _add("type only (no mass filter)", *processor.process_raw_data(raw_df, metadata_df, max_authors=NO_MASS_FILTER))

    # No type filter and no mass filter (the unfiltered baseline).
    _add("unfiltered (no type/mass)", *processor.process_raw_data_unfiltered(raw_df, metadata_df))

    return pd.DataFrame(rows)


def main() -> None:
    year = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_YEAR

    print(f"\n=== Sensitivity of the co-authorship network — {year} ===")
    table = run(year)

    print("\n=== Summary ===")
    print(table.to_string(index=False))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"sensitivity_{year}.csv"
    table.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
