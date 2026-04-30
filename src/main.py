"""Main pipeline for parliamentary network analysis."""
import os
import pandas as pd # type: ignore
from itertools import islice
from dotenv import load_dotenv  # type: ignore

from config import Config, setup_logger
from extraction import ChamberExtractor
from processing import ChamberProcessor
from core import ParliamentaryGraph
from core.algorithms.community_detection import compare_community_methods, detect_communities
from repository import CsvRepository, GraphExporter, DB_Exporter
from visualization import generate_analysis_plots

logger = setup_logger(__name__)
config = Config()
print(Config.DATA_DIR)

# Load environment variables
load_dotenv()
LEGISLATURE_START = config.LEGISLATURE_START
CURRENT_LEGISLATURE = config.CURRENT_LEGISLATURE
LEGISLATURE_ITERATOR = CURRENT_LEGISLATURE
DB_PATH = config.DB_PATH
API_BASE_URL = config.API_BASE_URL

def extraction_stage(year: int) -> tuple:
    """Stage 1: Raw data extraction."""
    logger.info("Extracting raw data...")
    extractor = ChamberExtractor(config)
    raw_dataframe = extractor.extract_raw_coauthorship_data(year)
    metadata_dataframe = extractor.extract_propositions_metadata(year)
    return raw_dataframe, metadata_dataframe, extractor


def processing_stage(raw_df: pd.DataFrame, metadata_df: pd.DataFrame, year: int) -> tuple:
    """Stage 2: Data cleaning and conversion to domain objects."""
    logger.info("Processing data...")
    processor = ChamberProcessor()

    # 1. Clean and extract co-authorships
    deputy_map, groups, coauthorships, type_map = processor.process_raw_data(raw_df, metadata_df)

    # 2. Convert to dataclass objects
    deputies_dict, propositions_list, coauthorships_list = processor.convert_to_domain_objects(
        deputy_map, groups, coauthorships, type_map, year
    )
    
    return deputies_dict, propositions_list, coauthorships_list, processor

def core_stage(deputies: dict, propositions: list, coauthorships: list, year: int) -> ParliamentaryGraph:
    """Stage 3: Graph construction."""
    logger.info("Building parliamentary graph...")
    graph = ParliamentaryGraph(deputies, propositions, coauthorships, year)
    graph.build()
    return graph


def algorithms_stage(graph: ParliamentaryGraph) -> dict:
    """Stage 4: Metrics calculation and community detection."""
    logger.info("Running community detection and modularity comparison...")
    communities_comparison = compare_community_methods(graph.graph)
    logger.info(f"Community comparison: {communities_comparison}")

    # Keep main partition for later export/analysis
    louvain_partition = detect_communities(graph.graph, method="louvain")
    if louvain_partition:
        for node_id, community_id in louvain_partition.items():
            if graph.graph.has_node(node_id):
                graph.graph.nodes[node_id]["community_louvain"] = int(community_id)

    return communities_comparison

def repository_stage(graph: ParliamentaryGraph, deputies: list, year: int) -> None:
    """Stage 5: Export to GEXF, CSV and SQLite."""
    logger.info("Exporting data...")

    graph_exporter = GraphExporter(Config.GEXF_DIR)
    gexf_file = graph_exporter.exportar_gexf(graph, ano=year)
    logger.info(f"GEXF exported to: {gexf_file}")

    csv_repository = CsvRepository(Config.METRICS_DIR)
    output_file = csv_repository.exportar_metricas_deputados(deputies, year)
    logger.info(f"CSV metrics exported to: {output_file}")

    db_repository = DB_Exporter(Config.DB_PATH)
    db_path = db_repository.exportar_metricas_deputados(deputies, year)
    logger.info(f"SQLite exported to: {db_path}")

def visualization_stage(graph: ParliamentaryGraph, deputies: list, year: int) -> None:
    """Stage 6: Generate visualizations."""
    logger.info("Generating visualizations...")
    output_dir = generate_analysis_plots(year)
    logger.info(f"Plots exported to: {output_dir}")

def run_pipeline(year: int) -> None:
    """Execute the complete parliamentary analysis pipeline."""
    logger.info("=== STARTING PARLIAMENTARY ANALYSIS PIPELINE ===")
    
    try:
        # Stage 1: Extraction
        raw_df, metadata_df, extractor = extraction_stage(year)
        
        # Stage 2: Processing
        deputies, propositions, coauthorships, processor = processing_stage(raw_df, metadata_df, year)
        print(f"Deputies: {len(deputies)}")
        print(f"Propositions: {len(propositions)}")
        print(f"Co-authorships: {len(coauthorships)}")

        # Stage 3: Core - Graph Construction
        graph = core_stage(deputies, propositions, coauthorships, year)
        deputy_centrality_list = graph.compute_degree_centrality()
        deputy_betweenness_list = graph.compute_betweenness_centrality()
        
        # Stage 4: Algorithms
        communities_info = algorithms_stage(graph)
        logger.info(f"Community summary (year={year}): {communities_info}")
        
        # Stage 5: Repository
        repository_stage(graph, deputy_centrality_list, year)
        
        # Stage 6: Visualization
        visualization_stage(graph, deputy_centrality_list, year)
        
        logger.info("✅ PIPELINE COMPLETED SUCCESSFULLY!")
    except Exception as e:
        logger.error(f"❌ Pipeline error: {e}")
        raise

if __name__ == "__main__":
    run_pipeline(2025)