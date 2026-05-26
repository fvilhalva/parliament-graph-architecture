"""Main entrypoint for parliamentary network analysis.

Runs the full pipeline for every year in the configured analysis window
(default: 2022-2025). Each year produces an independent snapshot with its
own GEXF, CSV exports, SQLite row and null-model p-value.
"""

from config import Config, setup_logger
from extraction import ChamberExtractor
from processing import ChamberProcessor
from repository import CsvRepository, DB_Exporter, GraphExporter
from pipeline import PipelineDependencies, run_pipeline
from visualization import generate_analysis_plots

logger = setup_logger(__name__)

# Years analysed for the temporal study. Adjust here if the window changes.
ANALYSIS_YEARS = [2022, 2023, 2024, 2025]


def build_pipeline_dependencies() -> tuple[Config, PipelineDependencies]:
    """Assemble concrete collaborators for the pipeline."""
    config = Config()
    deps = PipelineDependencies(
        extractor=ChamberExtractor(config),
        processor=ChamberProcessor(),
        graph_exporter=GraphExporter(Config.GEXF_DIR),
        csv_repository=CsvRepository(Config.METRICS_DIR),
        db_repository=DB_Exporter(Config.DB_PATH),
        generate_plots=generate_analysis_plots,
    )
    return config, deps


if __name__ == "__main__":
    config, pipeline_dependencies = build_pipeline_dependencies()

    logger.info(f"=== TEMPORAL ANALYSIS — years {ANALYSIS_YEARS} ===")

    failures: list[tuple[int, str]] = []
    for year in ANALYSIS_YEARS:
        logger.info(f"\n{'#' * 60}\n# YEAR {year}\n{'#' * 60}")
        try:
            run_pipeline(
                year,
                pipeline_dependencies,
                max_authors=config.MAX_AUTHORS_PER_PROPOSAL,
            )
        except Exception as exc:
            logger.error(f"Year {year} failed: {exc}")
            failures.append((year, str(exc)))
            # Continue to the next year so partial failures don't kill the run.

    logger.info("\n" + "=" * 60)
    if failures:
        logger.warning(f"Pipeline finished with {len(failures)} failure(s):")
        for year, msg in failures:
            logger.warning(f"  - {year}: {msg}")
    else:
        logger.info("✅ All years completed successfully.")
    logger.info("Run `python scripts/compare_years.py` to generate cross-year analysis.")