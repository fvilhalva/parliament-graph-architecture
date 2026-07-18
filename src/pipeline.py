"""Pipeline orchestration for parliamentary network analysis."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Callable

import networkx as nx  # type: ignore
import pandas as pd  # type: ignore

from config import setup_logger
from core import ParliamentaryGraph
from core.algorithms.analysis_result import (
    AnalysisResult,
    MethodSummary,
    PartitionAgreement,
    compute_adjusted_rand_index,
)
from core.algorithms.community_composition import (
    CommunityCompositionResult,
    assess_graph_community_composition,
)
from core.algorithms.community_detection import CommunityDetector
from core.algorithms.concentration import ConcentrationResult, assess_graph_concentration
from core.algorithms.relatorship import RelatorshipResult, assess_graph_relatorship
from core.algorithms.validation import (
    NullModelResult,
    PermutationResult,
    assess_community_significance,
    assess_label_association,
    party_degree_vs_betweenness_statistic,
    party_size_vs_mean_betweenness_statistic,
)
from extraction import ChamberExtractor
from processing import ChamberProcessor
from repository import AnalysisRepository, CsvRepository, DB_Exporter, GraphExporter
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
    analysis_repository: AnalysisRepository
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
    max_authors: int = 30,
) -> tuple[dict, list, list]:
    """Stage 2: Clean raw data and convert it into domain objects."""
    logger.info("Processing data...")

    deputy_map, groups, coauthorships, type_map, relator_map = processor.process_raw_data(
        raw_df, metadata_df, max_authors=max_authors
    )
    deputies_dict, propositions_list, coauthorships_list = processor.convert_to_domain_objects(
        deputy_map,
        groups,
        coauthorships,
        type_map,
        year,
        relator_map=relator_map,
    )

    return deputies_dict, propositions_list, coauthorships_list


def core_stage(deputies: dict, propositions: list, coauthorships: list, year: int) -> ParliamentaryGraph:
    """Stage 3: Build the parliamentary graph."""
    logger.info("Building parliamentary graph...")
    graph = ParliamentaryGraph(deputies, propositions, coauthorships, year)
    graph.build()
    return graph


def algorithms_stage(
    graph: ParliamentaryGraph,
    propositions: list,
    year: int,
    max_authors: int,
    n_permutations: int = 200,
    min_party_size: int = 3,
) -> AnalysisResult:
    """Stage 4: Community detection, statistical validation, PP1/PP2/PP3.

    Returns the canonical :class:`AnalysisResult` for the year, ready to be
    persisted by :class:`AnalysisRepository`.
    """
    detector = CommunityDetector()

    # --- Community detection (both methods for comparison + ARI) ---
    logger.info("Running community detection...")
    louvain_partition = detector.detect_louvain(graph.graph, seed=42)
    label_prop_partition = detector.detect_label_propagation(graph.graph)

    louvain_summary = MethodSummary(
        modularity=detector.calculate_modularity(graph.graph, louvain_partition),
        num_communities=len(set(louvain_partition.values())) if louvain_partition else 0,
    )
    label_prop_summary = MethodSummary(
        modularity=detector.calculate_modularity(graph.graph, label_prop_partition),
        num_communities=len(set(label_prop_partition.values())) if label_prop_partition else 0,
    )
    logger.info(
        "Louvain Q=%.4f (%d communities); Label Propagation Q=%.4f (%d communities)",
        louvain_summary.modularity,
        louvain_summary.num_communities,
        label_prop_summary.modularity,
        label_prop_summary.num_communities,
    )

    # Propagate Louvain community down to Deputy (for CSV/SQLite export) and to
    # the NetworkX node attributes (for GEXF / Gephi).
    graph.assign_communities(louvain_partition)

    # Adjusted Rand Index between the two partitions — robustness of Louvain.
    ari = compute_adjusted_rand_index(louvain_partition, label_prop_partition)
    partition_agreement = PartitionAgreement(
        adjusted_rand_index=ari,
        louvain_num_communities=louvain_summary.num_communities,
        label_propagation_num_communities=label_prop_summary.num_communities,
    )
    logger.info("Partition agreement (Louvain vs. LP): ARI=%.3f", ari)

    # --- H1: statistical significance of community structure (null model) ---
    logger.info(f"Running null-model permutation test ({n_permutations} permutations)...")
    null_model: NullModelResult = assess_community_significance(
        graph.graph, n_permutations=n_permutations, seed=42
    )
    logger.info(str(null_model))

    # --- Party-level label-permutation tests (historical H2, H3) ---
    logger.info("Running party-level label-permutation tests...")
    party_size_test: PermutationResult = assess_label_association(
        graph,
        partial(party_size_vs_mean_betweenness_statistic, min_party_size=min_party_size),
        n_permutations=n_permutations,
        seed=42,
        two_sided=False,
    )
    logger.info("party_size_vs_mean_betweenness %s", party_size_test)

    party_degree_test: PermutationResult = assess_label_association(
        graph,
        partial(party_degree_vs_betweenness_statistic, min_party_size=min_party_size),
        n_permutations=n_permutations,
        seed=42,
        two_sided=True,
    )
    logger.info("party_degree_vs_betweenness %s", party_degree_test)

    # --- PP1: structural concentration of influence ---
    logger.info("Assessing concentration of influence (PP1)...")
    concentration: dict[str, ConcentrationResult] = {}
    for metric in ("weighted_degree", "betweenness_centrality"):
        result = assess_graph_concentration(graph, metric=metric)
        concentration[metric] = result
        logger.info(str(result))

    # --- PP2: are communities parties or coalitions? ---
    logger.info("Assessing community party composition (PP2)...")
    composition: CommunityCompositionResult = assess_graph_community_composition(
        graph, louvain_partition, min_size=min_party_size
    )
    logger.info(str(composition))

    # --- PP3: centrality vs. relatorship count ---
    logger.info("Assessing centrality vs. relatorship count (PP3)...")
    graph.assign_relatorship_counts(propositions)
    pp3: RelatorshipResult = assess_graph_relatorship(graph)
    logger.info(str(pp3))

    return AnalysisResult(
        year=year,
        n_nodes=graph.graph.number_of_nodes(),
        n_edges=graph.graph.number_of_edges(),
        density=float(nx.density(graph.graph)) if graph.graph.number_of_nodes() > 1 else 0.0,
        max_authors=max_authors,
        n_permutations=n_permutations,
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        louvain=louvain_summary,
        label_propagation=label_prop_summary,
        partition_agreement=partition_agreement,
        null_model=null_model,
        concentration=concentration,
        community_composition=composition,
        party_size_vs_mean_betweenness=party_size_test,
        party_degree_vs_betweenness=party_degree_test,
        pp3_relatorship=pp3,
    )


def repository_stage(
    graph: ParliamentaryGraph,
    deputies: list,
    year: int,
    analysis: AnalysisResult,
    graph_exporter: GraphExporter,
    csv_repository: CsvRepository,
    db_repository: DB_Exporter,
    analysis_repository: AnalysisRepository,
) -> None:
    """Stage 5: Export graph, metrics and analysis result to disk."""
    logger.info("Exporting data...")

    gexf_file = graph_exporter.export_gexf(graph, year=year)
    logger.info(f"GEXF exported to: {gexf_file}")

    output_file = csv_repository.export_deputy_metrics(deputies, year)
    logger.info(f"CSV metrics exported to: {output_file}")

    coauthorship_file = csv_repository.export_coauthorship_metrics(
        list(graph.graph.edges(data="weight")), year
    )
    logger.info(f"CSV coauthorships exported to: {coauthorship_file}")

    db_path = db_repository.exportar_metricas_deputados(deputies, year)
    logger.info(f"SQLite exported to: {db_path}")

    analysis_file = analysis_repository.save(analysis)
    logger.info(f"Analysis result exported to: {analysis_file}")


def visualization_stage(year: int, generate_plots: Callable[[int], Path]) -> None:
    """Stage 6: Generate plots and summaries."""
    logger.info("Generating visualizations...")
    output_dir = generate_plots(year)
    logger.info(f"Plots exported to: {output_dir}")


def run_pipeline(year: int, dependencies: PipelineDependencies, max_authors: int = 30) -> None:
    """Execute the complete parliamentary analysis pipeline."""
    logger.info("=== STARTING PARLIAMENTARY ANALYSIS PIPELINE ===")

    try:
        raw_df, metadata_df = extraction_stage(dependencies.extractor, year)

        deputies, propositions, coauthorships = processing_stage(
            dependencies.processor,
            raw_df,
            metadata_df,
            year,
            max_authors=max_authors,
        )
        print(f"Deputies: {len(deputies)}")
        print(f"Propositions: {len(propositions)}")
        print(f"Co-authorships: {len(coauthorships)}")

        graph = core_stage(deputies, propositions, coauthorships, year)
        deputy_centrality_list = graph.compute_all_centralities()

        analysis = algorithms_stage(
            graph,
            propositions=propositions,
            year=year,
            max_authors=max_authors,
        )

        repository_stage(
            graph,
            deputy_centrality_list,
            year,
            analysis,
            dependencies.graph_exporter,
            dependencies.csv_repository,
            dependencies.db_repository,
            dependencies.analysis_repository,
        )
        visualization_stage(year, dependencies.generate_plots)

        logger.info("✅ PIPELINE COMPLETED SUCCESSFULLY!")
    except Exception as exc:
        logger.error(f"❌ Pipeline error: {exc}")
        raise
