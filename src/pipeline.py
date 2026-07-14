"""Pipeline orchestration for parliamentary network analysis."""
from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Callable

import pandas as pd  # type: ignore

from config import setup_logger
from core import ParliamentaryGraph
from core.algorithms.community_detection import compare_community_methods, detect_communities
from core.algorithms.validation import (
    NullModelResult,
    PermutationResult,
    assess_community_significance,
    assess_label_association,
    h2_benchsize_betweenness_statistic,
    h3_degree_betweenness_statistic,
)
from core.algorithms.concentration import ConcentrationResult, assess_graph_concentration
from core.algorithms.community_composition import (
    CommunityCompositionResult,
    assess_graph_community_composition,
)
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
    max_authors: int = 30,
) -> tuple[dict, list, list]:
    """Stage 2: Clean raw data and convert it into domain objects."""
    logger.info("Processing data...")

    deputy_map, groups, coauthorships, type_map = processor.process_raw_data(
        raw_df, metadata_df, max_authors=max_authors
    )
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


def algorithms_stage(
    graph: ParliamentaryGraph,
    n_permutations: int = 200,
    min_party_size: int = 3,
) -> dict:
    """Stage 4: Run community detection, statistical validation, and compare methods."""
    logger.info("Running community detection and modularity comparison...")
    communities_comparison = compare_community_methods(graph.graph)
    logger.info(f"Community comparison: {communities_comparison}")

    louvain_partition = detect_communities(graph.graph, method="louvain")
    if louvain_partition:
        for node_id, community_id in louvain_partition.items():
            if graph.graph.has_node(node_id):
                graph.graph.nodes[node_id]["community_louvain"] = int(community_id)

    # --- Statistical significance via null-model permutation test ---
    logger.info(f"Running null-model permutation test ({n_permutations} permutations)...")
    validation: NullModelResult = assess_community_significance(
        graph.graph, n_permutations=n_permutations, seed=42
    )
    logger.info(str(validation))

    communities_comparison["null_model"] = {
        "q_observed": round(validation.q_observed, 4),
        "q_null_mean": round(validation.q_null_mean, 4),
        "q_null_std": round(validation.q_null_std, 4),
        "p_value": round(validation.p_value, 4),
        "significant": validation.significant,
        "n_permutations": validation.n_permutations,
    }

    # --- Structural hypotheses H2 & H3 via label-permutation tests ---
    # These keep the graph fixed and shuffle party_code labels; topology and
    # per-deputy centralities are never modified (see assess_label_association).
    logger.info("Running label-permutation tests for H2 and H3...")

    # H2: bench size vs. mean betweenness. Expected negative -> one-sided.
    h2: PermutationResult = assess_label_association(
        graph,
        partial(h2_benchsize_betweenness_statistic, min_party_size=min_party_size),
        n_permutations=n_permutations,
        seed=42,
        two_sided=False,
    )
    logger.info("H2 %s", h2)

    # H3: mean weighted degree vs. mean betweenness. Two-sided by default.
    h3: PermutationResult = assess_label_association(
        graph,
        partial(h3_degree_betweenness_statistic, min_party_size=min_party_size),
        n_permutations=n_permutations,
        seed=42,
        two_sided=True,
    )
    logger.info("H3 %s", h3)

    communities_comparison["h2_benchsize_betweenness"] = _permutation_summary(h2)
    communities_comparison["h3_degree_betweenness"] = _permutation_summary(h3)

    # --- PP1: structural concentration of influence (few vs. many) ---
    logger.info("Assessing concentration of influence (PP1)...")
    concentration = {
        metric: assess_graph_concentration(graph, metric=metric)
        for metric in ("weighted_degree", "betweenness_centrality")
    }
    for result in concentration.values():
        logger.info(str(result))
    communities_comparison["concentration"] = {
        metric: {
            "gini": round(result.gini, 4),
            "top_share": {str(frac): round(share, 4) for frac, share in result.top_share.items()},
            "n": result.n,
        }
        for metric, result in concentration.items()
    }

    # --- PP2: are communities parties or coalitions? ---
    logger.info("Assessing community party composition (PP2)...")
    composition: CommunityCompositionResult = assess_graph_community_composition(
        graph, louvain_partition, min_size=min_party_size
    )
    logger.info(str(composition))
    communities_comparison["community_composition"] = {
        "verdict": composition.verdict,
        "mean_purity": round(composition.mean_purity, 4),
        "multiparty_fraction": round(composition.multiparty_fraction, 4),
        "coalition_fraction": round(composition.coalition_fraction, 4),
        "num_communities": composition.num_communities,
    }

    return communities_comparison


def _permutation_summary(result: PermutationResult) -> dict:
    """Serialise a :class:`PermutationResult` for persistence alongside H1."""
    return {
        "statistic_observed": round(result.statistic_observed, 4)
        if result.valid
        else None,
        "statistic_null_mean": round(result.statistic_null_mean, 4)
        if result.valid
        else None,
        "statistic_null_std": round(result.statistic_null_std, 4)
        if result.valid
        else None,
        "p_value": round(result.p_value, 4),
        "significant": result.significant,
        "two_sided": result.two_sided,
        "n_permutations": result.n_permutations,
        "valid": result.valid,
    }


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