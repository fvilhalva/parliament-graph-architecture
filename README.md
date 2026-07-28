<div align="center">

# 🏛️ Parliamentary Network Analysis

### Analysis of Influence Structures Based on Graph Theory

*TCC — Universidade Estadual de Mato Grosso do Sul (UEMS)*

<br/>

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-256%20passing-2ea44f?style=flat-square&logo=pytest&logoColor=white)](./src/tests/)
[![Coverage](https://img.shields.io/badge/Coverage-85%25-2ea44f?style=flat-square)](./src/tests/)
[![Core Coverage](https://img.shields.io/badge/Core%20Coverage-≥93%25-2ea44f?style=flat-square)](./src/tests/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)](./Dockerfile)
[![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)](./LICENSE)

<br/>

*Modular, reproducible architecture for analyzing Brazilian parliamentary co-authorship networks using graph theory.*  
*Transforms raw legislative data into measurable, auditable evidence of political influence structures (2022–2025).*

<br/>

> **Central thesis:** Parliamentary co-authorship is not random — it reflects power structures and political articulation.  
> The co-authorship network is a **valid and measurable proxy** for legislative influence.

</div>

---

## 🔬 Research Questions & Hypotheses

Hypotheses are formulated in **strictly structural (topological)** terms — no ideological party labels.

| Pergunta | Hypothesis | Verdict |
|----------|-----------|---------|
| — | **H1** — Community structure is non-random (Q ≫ null model) | ✅ Confirmed (4/4 years) |
| **PP1** | **H2** — Structural influence is concentrated in few deputies (long-tail) | ✅ Confirmed (Gini ≈ 0.80) |
| **PP2** | **H3** — Communities are multiparty coalitions, not isolated parties | ✅ Confirmed (purity ≈ 0.5) |
| **PP3** | **H4** — Centrality predicts real influence (rapporteurships) — *Fowler effect* | ✅ Confirmed (2023–2025) |

---

## 📊 Key Results (2022–2025)

| Indicator | 2022 | 2023 | 2024 | 2025 |
|-----------|-----:|-----:|-----:|-----:|
| Active nodes | 273 | 360 | 336 | 331 |
| Co-authorship edges | 3,085 | 5,079 | 4,421 | 5,396 |
| Density | 8.31% | 7.86% | 7.86% | 9.88% |
| **H1** — Louvain Q | 0.596 | 0.639 | 0.632 | 0.636 |
| **H1** — Null-model p | <0.005 | <0.005 | <0.005 | <0.005 |
| **H2** — Gini (betweenness) | 0.804 | 0.799 | 0.819 | 0.801 |
| **H3** — Community purity | 0.46 | 0.46 | 0.50 | 0.50 |
| **H4** — ρ (centrality×rapporteur) | 0.115 | **0.299** | **0.242** | **0.221** |
| **H4** — p-value | 0.057 | <0.001 | <0.001 | <0.001 |

> H4 is borderline in 2022 due to the 56th→57th legislature transition (147 off-graph rapporteurs vs. ~21 average) — a limitation of the source data, mechanistically explained, not a model failure.

---

## 🏗️ Architecture

Pipeline with single-responsibility layers, following Clean Architecture + SOLID:

```
extraction → processing → core (Graph + Algorithms) → repository → visualization
```

| Layer | Responsibility |
|-------|----------------|
| **extraction/** | Download and local cache of CSVs from the Chamber portal |
| **processing/** | Cleaning, filters (type + max_authors), rapporteur URI parsing, conversion to domain objects |
| **core/graph.py** | Bipartite projection → weighted co-authorship graph; community & rapporteurship assignment |
| **core/algorithms/** | Centrality, community detection, null-model, concentration (PP1), composition (PP2), relatorship (PP3), stats, aggregate result |
| **models/** | Domain entities (Deputy, Proposition, CoauthorshipEdge) |
| **repository/** | Export to CSV, GEXF (Gephi), SQLite, JSON (AnalysisResult) |
| **visualization/** | Automated per-year plots |
| **scripts/** | Cross-year comparative analysis |
| **tests/** | 256 tests, 85% overall coverage (core ≥ 93%) |

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
│   │   ├── graph.py                     # ParliamentaryGraph — projection, centralities,
│   │   │                                #   assign_communities, assign_relatorship_counts
│   │   └── algorithms/
│   │       ├── metrics.py               # Degree, betweenness, closeness, eigenvector
│   │       ├── community_detection.py   # Louvain, Label Propagation
│   │       ├── validation.py            # Null-model (H1) + party-level permutation tests
│   │       ├── concentration.py         # Gini + top-share (PP1 / H2)
│   │       ├── community_composition.py # Party purity of communities (PP2 / H3)
│   │       ├── relatorship.py           # Centrality × rapporteurship (PP3 / H4)
│   │       ├── stats.py                 # Shared statistical helpers (Spearman)
│   │       └── analysis_result.py       # AnalysisResult aggregate + ARI
│   ├── extraction/
│   │   └── chamber_extractor.py         # ChamberExtractor (CSV download + cache)
│   ├── models/
│   │   ├── deputy.py                    # + community_louvain, relatorship_count
│   │   ├── proposition.py               # + relator_id
│   │   ├── coauthorship_edge.py
│   │   └── parliamentary_network.py
│   ├── processing/
│   │   └── data_cleaning.py             # ChamberProcessor + max_authors + relator parsing
│   ├── repository/
│   │   ├── csv_repository.py
│   │   ├── db_repository.py             # SQLite with idempotent ALTER TABLE migration
│   │   ├── graph_exporter.py
│   │   └── analysis_repository.py       # AnalysisResult ↔ JSON
│   ├── visualization/
│   │   └── plots.py                     # Per-year plots → data/plots/{year}/
│   ├── pipeline.py                      # Orchestrates all stages
│   ├── tests/                           # 256 tests
│   └── main.py                          # Multi-year entry point (2022–2025)
├── scripts/
│   └── compare_years.py                 # Cross-year analysis (reads data/analysis/*.json)
├── data/                                # gitignored — generated at runtime
│   ├── cache/                           # Cached CSVs (downloaded once)
│   ├── gexf/                            # chamber_graph_{year}.gexf
│   ├── metricas/                        # deputados_metricas_{year}.csv, coauthorships_{year}.csv
│   ├── analysis/                        # analysis_{year}.json  (H1, PP1–PP3, ARI, metadata)
│   ├── plots/
│   │   ├── {year}/                      # Per-year plots (isolated per run)
│   │   ├── compare_nodes_edges.png      # Generated by compare_years.py
│   │   ├── compare_modularity.png
│   │   └── compare_top_betweenness.png  # Heatmap across all years
│   └── parliament.db
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

# Run test suite (256 tests)
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
2. **Processing** — Clean data; filter to valid proposition types (PL, PEC, PLP, PDL, EMC); apply `max_authors=30` filter; parse `ultimoStatus_uriRelator` for rapporteurship analysis
3. **Graph construction** — Bipartite projection B=(D∪P, E) → weighted co-authorship graph G=(D, E', w)
4. **Metrics** — Degree, betweenness, closeness, eigenvector centrality for all deputies
5. **Analysis** — Louvain + Label Propagation (ARI); null-model test (H1); concentration (PP1); composition (PP2); relatorship correlation (PP3)
6. **Repository** — Export to CSV, GEXF, SQLite, and `analysis_{year}.json`
7. **Visualization** — Generate plots to `data/plots/{year}/`

The pipeline runs each year independently (2022–2025). A failure in one year does not stop the others.

---

## 🧮 Mathematical Model

**Edge weight** — normalized by group size to penalize mass co-signatures:
```
w(i,j) = Σ  1 / (n_p - 1)    for each shared proposition p
```

**max_authors filter** — proposals with more than 30 deputy co-authors are excluded from edge construction. A PEC with 226 signatories generates ~25,400 pairs, pushing density to ~85% and making community detection invalid.

**Uniform type weights** — all proposition types receive weight = 1. No theoretically justified numeric scale exists for weighting PL vs. PEC; qualitative filtering (by type) already performs the relevant selection.

**Null-model validation (H1)** — 200 random graphs via double-edge-swap (preserving degree sequence). p-value = fraction of null graphs with Q ≥ Q_observed.

**Concentration (PP1)** — Gini coefficient + top-share over centrality distribution.

**Community composition (PP2)** — mean party purity per community (share of the dominant party).

**Relatorship correlation (PP3)** — Spearman ρ between betweenness centrality and rapporteurship count (Fowler effect).

**Partition agreement** — Adjusted Rand Index (ARI) between Louvain and Label Propagation partitions.

---

## 🧪 Test Suite

**256 tests**, **85% overall coverage**, **core ≥ 93%**

| Module | Covers |
|--------|--------|
| `test_aresta_coautoria.py` | CoauthorshipEdge creation, equality, validation |
| `test_deputado.py` | Deputy creation, centrality field updates |
| `test_graph.py` | Graph construction, weights, centrality, community/rapporteur assignment |
| `test_metrics.py` | Centrality helpers |
| `test_community_detection.py` | Louvain, Label Propagation, modularity |
| `test_community_composition.py` | Community purity / coalition verdict (PP2) |
| `test_concentration.py` | Gini + top-share (PP1) |
| `test_relatorship.py` | Centrality × rapporteurship correlation (PP3) |
| `test_validation.py` | Null-model (H1) + party-level permutation tests |
| `test_analysis_result.py` | Adjusted Rand Index |
| `test_analysis_repository.py` | JSON round-trip persistence |
| `test_proposicao.py` | Proposition creation, authorship |
| `test_processing.py` | Data cleaning, max_authors, party/state sanitization |
| `test_repository.py` | CSV/GEXF/SQLite export and integrity |
| `test_dataset_integrity.py` | 64 per-year integrity checks on generated datasets |

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
ANALYSIS_DIR=data/analysis
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

## 📦 Analysis Output (`data/analysis/analysis_{year}.json`)

Each pipeline run persists a single, human-readable, auditable JSON per year — the single source of truth for every number reported in the monograph:

```jsonc
{
  "year": 2025,
  "n_nodes": 331, "n_edges": 5396, "density": 0.0988,
  "max_authors": 30, "n_permutations": 200, "timestamp": "...",
  "louvain": { "modularity": 0.636, "num_communities": 17 },
  "label_propagation": { "modularity": 0.485, "num_communities": 11 },
  "partition_agreement": { "adjusted_rand_index": 0.442 },
  "null_model": { "q_observed": 0.636, "q_null_mean": 0.117, "p_value": 0.0, "significant": true },
  "concentration": { "betweenness_centrality": { "gini": 0.801, "top_share": { ... } } },
  "community_composition": { "verdict": "coalizões", "mean_purity": 0.498 },
  "pp3_relatorship": { "spearman_rho": 0.221, "p_value": 4.8e-05, "significant": true }
}
```

---

## 📚 Main Dependencies

| Package | Purpose |
|---------|---------|
| **networkx** | Graph construction, centrality, community algorithms |
| **pandas** | Data processing and manipulation |
| **python-louvain** | Louvain community detection |
| **scipy** | Spearman correlation and statistical operations |
| **matplotlib / seaborn** | Visualization and plotting |
| **pytest / pytest-cov** | Test framework and coverage |
| **python-dotenv** | Environment variable management |
| **requests** | CSV download from Chamber portal |

---

## 👤 Author

**Felipe Echeverria Vilhalva**  
Orientador: Prof. Dr. Rubens Barbosa Filho  
Universidade Estadual de Mato Grosso do Sul (UEMS)

## 📄 License

MIT License — see `LICENSE` for details.
