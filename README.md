<div align="center">

# 🏛️ Parliamentary Network Analysis

### Analysis of Influence Structures Based on Graph Theory

*TCC — Universidade Estadual de Mato Grosso do Sul (UEMS)*

<br/>

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-132%20passing-2ea44f?style=flat-square&logo=pytest&logoColor=white)](./src/tests/)
[![Coverage](https://img.shields.io/badge/Coverage-82%25-yellow?style=flat-square)](./src/tests/)
[![Core Coverage](https://img.shields.io/badge/Core%20Coverage-≥93%25-2ea44f?style=flat-square)](./src/tests/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)](./Dockerfile)
[![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)](./LICENSE)

<br/>

*Modular, reproducible architecture for analyzing Brazilian parliamentary co-authorship networks using graph theory.*  
*Transforms raw legislative data into measurable evidence of political alignment (2022–2025).*

<br/>

> **Central thesis:** Parliamentary co-authorship is not random — it reflects power structures, ideology, and political alignment.  
> The co-authorship network is a **valid and measurable proxy** for political alignment.

</div>

---

## 📊 Key Results (2025)

| Metric | Value |
|--------|-------|
| Deputies in dataset | 571 |
| Active nodes (co-authors) | 331 |
| Unique co-authorship edges | 5,396 |
| Graph density | 9.88% |
| Connected components | 7 |
| Largest component | 317 nodes (95.8%) |
| Louvain modularity (Q) | **0.636** |
| Communities detected | 17 |
| Null-model p-value | **< 0.005** (200 permutations) |

**Confirmed hypotheses:**
- **H1** — Community structure is statistically significant (Q_obs = 0.636 ≫ Q_null = 0.117 ± 0.003)
- **H2** — Center/mediation parties (MDB, PSB) produce top betweenness brokers, not the largest parties
- **H3** — Ideologically cohesive parties (PSOL, NOVO) form echo chambers: high weighted degree, low betweenness

---

## 🏗️ Architecture

Pipeline with single-responsibility layers:

```
extraction → processing → core (Graph + Algorithms) → repository → visualization
```

| Layer | Responsibility |
|-------|----------------|
| **extraction/** | Download and local cache of CSVs from the Chamber API |
| **processing/** | Cleaning, filters (type + max_authors), conversion to domain objects |
| **core/graph.py** | Bipartite projection → weighted co-authorship graph |
| **core/algorithms/** | Centrality metrics, community detection, null-model validation |
| **models/** | Domain entities (Deputy, Proposition, CoauthorshipEdge) |
| **repository/** | Export to CSV, GEXF (Gephi), SQLite |
| **visualization/** | Automated per-year plots |
| **scripts/** | Cross-year comparative analysis |
| **tests/** | 132 tests, 82% overall coverage (core ≥ 93%) |

---

## 📁 Directory Structure

```
parliament-graph-architecture/
├── src/
│   ├── config/
│   │   ├── config.py                    # Config class (environment-loaded)
│   │   ├── constants.py                 # Proposition type weights, party lists
│   │   └── logging_config.py
│   ├── core/
│   │   ├── graph.py                     # ParliamentaryGraph — bipartite projection
│   │   └── algorithms/
│   │       ├── metrics.py               # Degree, betweenness, closeness, eigenvector
│   │       ├── community_detection.py   # Louvain, Label Propagation
│   │       └── validation.py            # Null-model permutation test
│   ├── extraction/
│   │   └── chamber_extractor.py         # ChamberExtractor (API/CSV download + cache)
│   ├── models/
│   │   ├── deputy.py
│   │   ├── proposition.py
│   │   ├── coauthorship_edge.py
│   │   └── parliamentary_network.py
│   ├── processing/
│   │   └── data_cleaning.py             # ChamberProcessor + max_authors filter
│   ├── repository/
│   │   ├── csv_repository.py
│   │   ├── db_repository.py
│   │   └── graph_exporter.py
│   ├── visualization/
│   │   └── plots.py                     # Per-year plots → data/plots/{year}/
│   ├── pipeline.py                      # Orchestrates all stages
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_aresta_coautoria.py
│   │   ├── test_deputado.py
│   │   ├── test_graph.py
│   │   ├── test_proposicao.py
│   │   ├── test_processing.py           # Includes max_authors filter tests
│   │   └── test_repository.py
│   └── main.py                          # Multi-year entry point (2022–2025)
├── scripts/
│   └── compare_years.py                 # Cross-year comparative analysis
├── data/                                # gitignored — generated at runtime
│   ├── cache/                           # Cached CSVs (downloaded once)
│   ├── gexf/                            # chamber_graph_{year}.gexf
│   ├── metricas/                        # deputados_metricas_{year}.csv
│   ├── plots/
│   │   ├── {year}/                      # Per-year plots (isolated per run)
│   │   │   ├── top_deputies_weighted_degree.png
│   │   │   ├── top_deputies_betweenness.png
│   │   │   ├── parties_num_deputies.png
│   │   │   ├── centrality_correlation.png
│   │   │   ├── degree_distribution.png
│   │   │   ├── graph_components.png
│   │   │   └── analysis_summary.txt
│   │   ├── compare_nodes_edges.png      # Generated by compare_years.py
│   │   ├── compare_modularity.png
│   │   └── compare_top_betweenness.png  # Heatmap across all years
│   └── parliament.db
├── apresentacao_tcc.tex                 # Beamer presentation (LaTeX)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🚀 Usage

### Prerequisites

- Docker + Docker Compose (recommended)
- Or: Python 3.11+

### Docker (Recommended)

```bash
# Build image
docker compose build

# Run full multi-year pipeline (2022–2025) — ~15-25 min
docker compose up pipeline_chamber

# Run cross-year comparison (after pipeline completes)
docker compose run --rm compare

# Run test suite (132 tests)
docker compose run --rm tests
```

### Local (without Docker)

```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate          # Windows

pip install -r requirements.txt

# Run pipeline
python src/main.py

# Run cross-year comparison
python scripts/compare_years.py

# Run tests with coverage
pytest src/tests/ -v --cov=src
```

---

## 🔄 Pipeline Stages

1. **Extraction** — Download/cache CSVs from `dadosabertos.camara.leg.br`
2. **Processing** — Clean data; filter to valid proposition types (PL, PEC, PLP, PDL, EMC); apply `max_authors=30` filter to exclude mass-signature proposals
3. **Graph construction** — Bipartite projection B=(D∪P, E) → weighted co-authorship graph G=(D, E', w)
4. **Metrics** — Degree, betweenness, closeness, eigenvector centrality for all deputies
5. **Community detection** — Louvain algorithm; null-model permutation test (200 double-edge-swaps, seed=42)
6. **Repository** — Export to CSV, GEXF, SQLite
7. **Visualization** — Generate plots to `data/plots/{year}/`

The pipeline runs each year independently (2022, 2023, 2024, 2025). A failure in one year does not stop the others.

---

## 🧮 Mathematical Model

**Edge weight** — normalized by group size to penalize mass co-signatures:
```
w(i,j) = Σ  1 / (n_p - 1)    for each shared proposition p
```

**max_authors filter** — proposals with more than 30 deputy co-authors are excluded from edge construction. A PEC with 226 signatories generates ~25,400 pairs, pushing graph density to ~85% and making community detection invalid.

**Proposition type weights** — all types receive uniform weight (= 1). No theoretically justified numeric scale exists in the literature for weighting PL vs. PEC; qualitative filtering (by type) already performs the relevant selection.

**Null-model validation** — 200 random graphs generated via double-edge-swap (preserving degree sequence). p-value = fraction of null graphs with Q ≥ Q_observed.

---

## 🧪 Test Suite

**132 tests**, **82% overall coverage**, **core ≥ 93%**

| Module | Covers |
|--------|--------|
| `test_aresta_coautoria.py` | CoauthorshipEdge creation, equality, validation |
| `test_deputado.py` | Deputy creation, centrality field updates |
| `test_graph.py` | Graph construction, edge weights, centrality, party filters |
| `test_metrics.py` | Centrality helpers |
| `test_community_detection.py` | Louvain, Label Propagation, modularity |
| `test_proposicao.py` | Proposition creation, authorship |
| `test_processing.py` | Data cleaning, max_authors filter (boundary tests) |
| `test_repository.py` | CSV/GEXF/SQLite export and integrity |

```bash
docker compose run --rm tests
# or
pytest src/tests/ -v --cov=src --cov-report=term-missing
```

---

## ⚙️ Configuration

All settings are loaded from `.env` (or environment variables):

```env
# Paths
CACHE_DIR=data/cache
GEXF_DIR=data/gexf
METRICS_DIR=data/metricas
PLOTS_DIR=data/plots
DB_PATH=data/parliament.db

# Legislature
CURRENT_LEGISLATURE=2026
PILOT_LEGISLATURE=2025

# API
API_BASE_URL=https://dadosabertos.camara.leg.br/api/v2
API_TIMEOUT=30

# Analysis
LOG_LEVEL=INFO
MIN_COAUTHORSHIPS=3
MIN_EDGE_WEIGHT=1
NUM_COMMUNITIES=5
MAX_AUTHORS_PER_PROPOSAL=30
```

---

## 📚 Main Dependencies

| Package | Purpose |
|---------|---------|
| **networkx** | Graph construction, centrality, community algorithms |
| **pandas** | Data processing and manipulation |
| **python-louvain** | Louvain community detection |
| **matplotlib / seaborn** | Visualization and plotting |
| **scipy** | Statistical operations |
| **pytest / pytest-cov** | Test framework and coverage |
| **python-dotenv** | Environment variable management |
| **requests** | CSV download from Chamber API |

---

## 📅 Timeline

| Date | Activity |
|------|----------|
| 2026-03-09 | Initial setup + architecture design |
| 2026-03-09 | Test suite (73 tests) |
| 2026-03-10 | Graph and algorithm implementation |
| 2026-04-30 | English refactor, Docker integration |
| 2026-05 | Uniform weights, max_authors filter, null-model in pipeline |
| 2026-05 | Multi-year loop (2022–2025), per-year plot isolation |
| 2026-05 | `scripts/compare_years.py`, betweenness plot, docker `compare` service |
| **TBD** | Monograph writing (July) |

---

## 👤 Author

**Felipe Echeverria Vilhalva**  
Orientador: Prof. Dr. Rubens Barbosa Filho  
Universidade Estadual de Mato Grosso do Sul (UEMS)

## 📄 License

MIT License — see `LICENSE` for details.
