# Parliamentary Network Analysis Architecture

## Analysis of Influence Structures Based on Graph Theory

TCC/Final Project that implements a modular architecture for analyzing parliamentary networks, identifying influence structures through centrality metrics and community detection algorithms.

**Period**: 2015-2025 (11 years of historical data from the Brazilian National Congress)

---

## 🏗️ Architecture

The architecture follows a layered pattern with well-defined responsibilities:

```
extraction → processing → core (Graph + Algorithms) → repository → visualization
```

### Layers

| Layer | Responsibility | Status |
|-------|-----------------|--------|
| **extraction/** | Raw data collection from API/CSV | ✅ Complete |
| **processing/** | Data cleaning, transformation, object conversion | ✅ Complete |
| **core/graph.py** | Graph construction and operations | ✅ Complete |
| **core/algorithms/** | Metrics and community detection | ✅ Complete |
| **models/** | Domain entities (dataclasses) | ✅ Complete |
| **repository/** | Persistence (CSV, GEXF, SQLite) | ✅ Complete |
| **visualization/** | Plots and reports | ✅ Complete |
| **tests/** | Automated test suite | ✅ Complete (73 tests, 58% coverage) |

---

## 🧩 Software Engineering Overview

This project is organized as a pipeline where each layer has a single responsibility and passes structured data to the next layer:

1. **extraction/** returns raw tabular data from the Chamber API or local CSV files.
2. **processing/** cleans that data and converts rows into lists of domain objects such as `Proposition` and `Deputy`.
3. **core/** receives those plain objects, creates the coauthorship edges, and builds the parliamentary network. This is the brain of the system.
4. **visualization/** consumes the processed data to generate plots and summaries.
5. **repository/** exports data for third-party tools such as Gephi and for persistence in CSV or SQLite.
6. **config/** centralizes application-wide settings.

### Layer Criticality

| Layer | Relative importance | Notes |
|-------|---------------------|-------|
| **models/** | 100% | Critical for data integrity |
| **processing/** | 80%+ | Data cleaning and normalization |
| **core/** | 80%+ | Main analytical logic |
| **extraction/** | 60% | Depends on external data sources |
| **visualization/** | 40% | Useful, but less critical to the pipeline core |

### Data Persistence

- `data/` stores persistent project outputs.
- `data/gexf/` stores graph exports.
- `data/metricas/` stores CSV metric outputs.
- `data/parliament.db` stores the generated SQLite database.

---

## 📁 Directory Structure

```
parliament-graph-architecture/
├── src/
│   ├── config/                          # Application configuration
│   │   ├── __init__.py
│   │   ├── config.py                    # Config class (environment-loaded)
│   │   ├── constants.py                 # Constants (political parties, states)
│   │   └── logging_config.py            # Logger setup
│   ├── core/                            # Graph analysis core
│   │   ├── __init__.py
│   │   ├── graph.py                     # ParliamentaryGraph class
│   │   └── algorithms/
│   │       ├── __init__.py
│   │       ├── metrics.py               # Centrality metrics (degree, betweenness, etc)
│   │       └── community_detection.py   # Louvain, Label Propagation
│   ├── extraction/                      # Data extraction layer
│   │   ├── __init__.py
│   │   └── chamber_extractor.py         # ChamberExtractor class (API/CSV download)
│   ├── models/                          # Domain entities
│   │   ├── __init__.py
│   │   ├── deputy.py                    # Deputy dataclass
│   │   ├── proposition.py               # Proposition dataclass
│   │   ├── coauthorship_edge.py         # CoauthorshipEdge dataclass
│   │   └── parliamentary_network.py     # ParliamentaryNetwork dataclass
│   ├── processing/                      # Data processing layer
│   │   ├── __init__.py
│   │   ├── data_cleaning.py             # ChamberProcessor class (cleaning, conversion)
│   │   └── processor.py                 # Alternative English processing methods
│   ├── repository/                      # Persistence layer
│   │   ├── __init__.py
│   │   ├── csv_repository.py            # CSV export (CsvRepository)
│   │   ├── db_repository.py             # SQLite persistence (DB_Exporter)
│   │   └── graph_exporter.py            # GEXF export (GraphExporter)
│   ├── visualization/                   # Visualization layer
│   │   ├── __init__.py
│   │   └── plots.py                     # Plots, reports, summaries
│   ├── tests/                           # Test suite
│   │   ├── __init__.py
│   │   ├── conftest.py                  # Shared fixtures
│   │   ├── test_aresta_coautoria.py     # CoauthorshipEdge tests
│   │   ├── test_deputado.py             # Deputy tests
│   │   ├── test_graph.py                # ParliamentaryGraph tests
│   │   ├── test_proposicao.py           # Proposition tests
│   │   ├── test_processing.py           # Processing/conversion tests
│   │   └── test_repository.py           # Repository/export tests
│   └── main.py                          # Pipeline entry point
├── data/                                # Data directory
│   ├── cache/                           # Cached CSVs
│   ├── gexf/                            # Network graphs (chamber_graph_YYYY.gexf)
│   ├── metricas/                        # Metrics CSV exports
│   ├── plots/                           # Generated plots and visualizations
│   └── parliament.db                    # SQLite database (generated)
├── docker-compose.yml                   # Container orchestration
├── Dockerfile                           # Docker image definition
├── requirements.txt                     # Python dependencies
├── LICENSE                              # MIT License
└── README.md                            # This file
```

---

## 🚀 Usage

### Prerequisites

- Docker and Docker Compose (recommended)
- Or: Python 3.11+ with `pip`

### With Docker (Recommended)

```bash
# Build and run everything (pipeline + tests)
docker compose up --build

# Or run in background
docker compose up --build -d

# Run only pipeline
docker compose run --rm pipeline_chamber python src/main.py

# Run only tests
docker compose run --rm tests pytest src/tests/ -v

# Run tests with coverage
docker compose run --rm tests pytest src/tests/ --cov=src --cov-report=term-missing
```

### Without Docker

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# or
venv\Scripts\activate            # Windows

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest src/tests/ -v

# Run pipeline
python src/main.py
```

### Data Files

The pipeline reads proposition author data (coauthorships) and proposition metadata from local CSV files or downloads them from the Chamber's open data portal.

Expected CSV file names by year `YYYY`:
- `proposicoesAutores-YYYY.csv` (coauthorship data)
- `proposicoes-YYYY.csv` (proposition metadata)

Location: `data/cache/` (checked first) or downloaded from:
- `https://dadosabertos.camara.leg.br/arquivos/proposicoesAutores/csv/proposicoesAutores-YYYY.csv`
- `https://dadosabertos.camara.leg.br/arquivos/proposicoes/csv/proposicoes-YYYY.csv`

---

## 📊 Data Models

### Deputy
```python
@dataclass
class Deputy:
    id: int                           # Unique ID from Chamber API
    name: str                         # Full name
    party_code: str                   # Political party abbreviation
    state_code: str                   # Brazilian state code
    weighted_degree: float = 0.0      # Sum of edge weights
    degree_centrality: float = 0.0    # Normalized degree centrality
    betweenness_centrality: float = 0.0  # Betweenness centrality metric
```

### Proposition
```python
@dataclass
class Proposition:
    id: int                      # Proposition ID
    year: int                    # Legislature year
    author_ids: List[int]        # List of deputy IDs who authored it
    proposition_type: str        # Type (PL, PEC, PLP, etc)
```

### CoauthorshipEdge
```python
@dataclass
class CoauthorshipEdge:
    source_id: int                      # Deputy ID 1
    target_id: int                      # Deputy ID 2
    raw_weight: int                     # Number of co-authored propositions
    normalized_strength: float = 0.0    # Normalized weight (0-1)
```

### ParliamentaryNetwork
```python
@dataclass
class ParliamentaryNetwork:
    year: int                           # Analysis year
    graph: nx.Graph                     # NetworkX graph instance
    deputies: Dict[int, Deputy]         # Deputy nodes mapping
```

---

## ✅ Implemented Features

- [x] Modular layered architecture
- [x] Data models (Deputy, Proposition, CoauthorshipEdge, ParliamentaryNetwork)
- [x] Complete `ChamberExtractor` (data collection)
- [x] Complete `ChamberProcessor` (data cleaning and conversion)
- [x] `ParliamentaryGraph` (graph construction and operations)
- [x] Centrality algorithms (degree, betweenness, closeness, eigenvector)
- [x] Community detection (Louvain, Label Propagation)
- [x] CSV export (deputy metrics, coauthorship data)
- [x] GEXF export (Gephi-compatible graph format)
- [x] SQLite persistence (metrics storage and upsert)
- [x] Visualization (plots, network summaries)
- [x] Docker + Docker Compose setup
- [x] Comprehensive test suite (73 tests, 58% coverage)
- [x] All code and identifiers in English

---

## 📚 Main Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| **networkx** | 3.2.1 | Graph analysis and algorithms |
| **pandas** | 2.2.0 | Data processing and manipulation |
| **scikit-learn** | 1.4.1 | Community detection (clustering) |
| **scipy** | 1.12.0 | Scientific computing operations |
| **matplotlib** | 3.8.3 | Visualization and plotting |
| **seaborn** | 0.13.2 | Statistical graphics |
| **pytest** | 7.4.3 | Testing framework |
| **pytest-cov** | 4.1.0 | Code coverage measurement |
| **python-dotenv** | 1.0.1 | Environment variable management |
| **requests** | 2.31.0 | HTTP requests (API/CSV download) | 

---

## 🔄 Pipeline Stages

1. **Extraction**: Download/cache proposition data using `ChamberExtractor`
2. **Processing**: Clean and convert raw data using `ChamberProcessor`
3. **Core**: Build graph, calculate metrics using `ParliamentaryGraph`
4. **Algorithms**: Run community detection (Louvain, Label Propagation)
5. **Repository**: Export to CSV, GEXF, SQLite
6. **Visualization**: Generate plots and reports

---

## 🧪 Test Suite

The test suite contains **73 tests** across 6 modules with **58% code coverage**:

```
test_aresta_coautoria.py    - CoauthorshipEdge creation, validation, equality
test_deputado.py            - Deputy creation, validation, metrics update
test_graph.py               - Graph structure, weights, node attributes
test_proposicao.py          - Proposition creation, authorship, validation
test_processing.py          - Data validation, cleaning, conversion
test_repository.py          - CSV/GEXF/SQLite export and integrity
```

**Status**: ✅ All 73 tests passing

Run tests:
```bash
# Docker (recommended)
docker compose run --rm tests pytest -v

# Or locally
pytest src/tests/ -v
```

---

## � Configuration

Configuration is loaded from environment variables in `.env` file:

```env
# Paths
CACHE_DIR=data/cache
GEXF_DIR=data/gexf
METRICAS_DIR=data/metricas
PLOTS_DIR=data/plots
DB_PATH=data/parliament.db

# Legislature
LEGISLATURA_ATUAL=2026
LEGISLATURA_INICIO=2006

# API
API_BASE_URL=https://dadosabertos.camara.leg.br/api/v2
API_TIMEOUT=30

# Analysis
LOG_LEVEL=INFO
MIN_COAUTORIAS=3
MIN_PESO_ARESTA=1
NUM_COMUNIDADES=5
```

---

## 📅 Project Timeline

| Date | Activity | Status |
|------|----------|--------|
| 2026-03-09 | Initial setup + architecture design | ✅ |
| 2026-03-09 | Test suite implementation (73 tests) | ✅ |
| 2026-03-10 | Graph and algorithm implementation | ✅ |
| 2026-04-30 | English refactor, all naming standardized | ✅ |
| 2026-04-30 | Full Docker integration and testing | ✅ |
| **TBD** | Final analysis and reporting | ⏳ |

---

## 📝 Architecture Patterns

### Pipeline Contract
- **extraction** → Returns DataFrame (raw data)
- **processing** → Returns (deputies_dict, propositions_list, coauthorships_list)
- **core** → Builds graph, computes centrality metrics
- **algorithms** → Performs community detection, returns communities
- **repository** → Exports to CSV/GEXF/SQLite, returns file paths
- **visualization** → Generates plots, returns plot paths

### Dataclass Pattern
All domain entities are immutable Python dataclasses defined in `src/models/`:
- `Deputy`, `Proposition`, `CoauthorshipEdge`, `ParliamentaryNetwork`

### Factory Pattern
Repository classes are instantiated with output directories:
- `CsvRepository(output_dir)`, `GraphExporter(output_dir)`, `DB_Exporter(db_path)`

---

## 🤝 Contributing

This is an academic project. Code follows PEP 8 standards and is fully type-hinted.

---

## 👤 Author

Felipe Echeverria Vilhalva

## 📄 License

MIT License - see `LICENSE` file for details.

---

## ⚠️ Notes

- Data files are cached in `data/cache/` after first download
- Generated outputs (GEXF, CSV, plots) are stored in `data/gexf/`, `data/metricas/`, `data/plots/`
- SQLite database is created automatically on first run
- All timestamps are in local timezone
- Graph is undirected and weighted (edge weight = count of co-authored propositions)