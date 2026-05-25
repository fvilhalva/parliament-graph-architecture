"""Main entrypoint for parliamentary network analysis."""

from config import Config
from extraction import ChamberExtractor
from processing import ChamberProcessor
from repository import CsvRepository, DB_Exporter, GraphExporter
from pipeline import PipelineDependencies, run_pipeline
from visualization import generate_analysis_plots


def build_pipeline_dependencies() -> PipelineDependencies:
    """Assemble concrete collaborators for the pipeline."""
    config = Config()
    return config, PipelineDependencies(
        extractor=ChamberExtractor(config),
        processor=ChamberProcessor(),
        graph_exporter=GraphExporter(Config.GEXF_DIR),
        csv_repository=CsvRepository(Config.METRICS_DIR),
        db_repository=DB_Exporter(Config.DB_PATH),
        generate_plots=generate_analysis_plots,
    )

if __name__ == "__main__":
    config, pipeline_dependecies = build_pipeline_dependencies()
    run_pipeline(config.CURRENT_PILOTO, pipeline_dependecies, max_authors=config.MAX_AUTHORS_PER_PROPOSAL)