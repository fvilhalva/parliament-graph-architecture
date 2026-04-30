"""Pipeline orchestration for parliamentary network analysis."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd  # type: ignore

from config import setup_logger
from core import ParliamentaryGraph
from core.algorithms.community_detection import compare_community_methods, detect_communities
from extraction import ChamberExtractor
from processing import ChamberProcessor
from repository import CsvRepository, DB_Exporter, GraphExporter
from visualization import generate_analysis_plots

logger = setup_logger(__name__)


@dataclass(frozen=True)
class PipelineDependencies:
    """Collaborators required to run the parliamentary analysis pipeline."""

    extractor: ChamberExtractor
    processor: ChamberProcessor
    graph_exporter: GraphExporter
    csv_repository: CsvRepository
    db_repository: DB_Exporter
    generate_plots: Callable[[int], Path] = generate_analysis_plots


def extraction_stage(
    extractor: ChamberExtractor,
    year: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Stage 1: Extract raw data from the Chamber sources."""
    logger.info("Extracting raw data...")
    raw_dataframe = extractor.extract_raw_coauthorship_data(year)
    metadata_dataframe = extractor.extract_propositions_metadata(year)
    return raw_dataframe, metadata_dataframe


def processing_stage(
    processor: ChamberProcessor,
    raw_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    year: int,
) -> tuple[dict, list, list]:
    """Stage 2: Clean raw data and convert it into domain objects."""
    logger.info("Processing data...")

    deputy_map, groups, coauthorships, type_map = processor.process_raw_data(raw_df, metadata_df)
    deputies_dict, propositions_list, coauthorships_list = processor.convert_to_domain_objects(
        deputy_map,
        groups,
        coauthorships,
        type_map,
        year,
    )

    return deputies_dict, propositions_list, coauthorships_list


def core_stage(deputies: dict, propositions: list, coauthorships: list, year: int) -> ParliamentaryGraph:
    """Stage 3: Build the parliamentary graph."""
    logger.info("Building parliamentary graph...")
    graph = ParliamentaryGraph(deputies, propositions, coauthorships, year)
    graph.build()
    return graph


def algorithms_stage(graph: ParliamentaryGraph) -> dict:
    """Stage 4: Run community detection and compare methods."""
    logger.info("Running community detection and modularity comparison...")
    communities_comparison = compare_community_methods(graph.graph)
    logger.info(f"Community comparison: {communities_comparison}")

    louvain_partition = detect_communities(graph.graph, method="louvain")
    if louvain_partition:
        for node_id, community_id in louvain_partition.items():
            if graph.graph.has_node(node_id):
                graph.graph.nodes[node_id]["community_louvain"] = int(community_id)

    return communities_comparison


def repository_stage(
    graph: ParliamentaryGraph,
    deputies: list,
    year: int,
    graph_exporter: GraphExporter,
    csv_repository: CsvRepository,
    db_repository: DB_Exporter,
) -> None:
    """Stage 5: Export graph and metrics to disk."""
    logger.info("Exporting data...")

    gexf_file = graph_exporter.exportar_gexf(graph, ano=year)
    logger.info(f"GEXF exported to: {gexf_file}")

    output_file = csv_repository.exportar_metricas_deputados(deputies, year)
    logger.info(f"CSV metrics exported to: {output_file}")

    db_path = db_repository.exportar_metricas_deputados(deputies, year)
    logger.info(f"SQLite exported to: {db_path}")


def visualization_stage(year: int, generate_plots: Callable[[int], Path]) -> None:
    """Stage 6: Generate plots and summaries."""
    logger.info("Generating visualizations...")
    output_dir = generate_plots(year)
    logger.info(f"Plots exported to: {output_dir}")


def run_pipeline(year: int, dependencies: PipelineDependencies) -> None:
    """Execute the complete parliamentary analysis pipeline."""
    logger.info("=== STARTING PARLIAMENTARY ANALYSIS PIPELINE ===")

    try:
        raw_df, metadata_df = extraction_stage(dependencies.extractor, year)

        deputies, propositions, coauthorships = processing_stage(
            dependencies.processor,
            raw_df,
            metadata_df,
            year,
        )
        print(f"Deputies: {len(deputies)}")
        print(f"Propositions: {len(propositions)}")
        print(f"Co-authorships: {len(coauthorships)}")

        graph = core_stage(deputies, propositions, coauthorships, year)
        deputy_centrality_list = graph.compute_degree_centrality()
        graph.compute_betweenness_centrality()

        communities_info = algorithms_stage(graph)
        logger.info(f"Community summary (year={year}): {communities_info}")

        repository_stage(
            graph,
            deputy_centrality_list,
            year,
            dependencies.graph_exporter,
            dependencies.csv_repository,
            dependencies.db_repository,
        )
        visualization_stage(year, dependencies.generate_plots)

        logger.info("✅ PIPELINE COMPLETED SUCCESSFULLY!")
    except Exception as exc:
        logger.error(f"❌ Pipeline error: {exc}")
        raise