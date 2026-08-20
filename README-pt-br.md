<div align="center">

# 🏛️ Análise de Redes Parlamentares

### Análise de Estruturas de Influência Baseada em Teoria dos Grafos

*TCC — Universidade Estadual de Mato Grosso do Sul (UEMS)*

<br/>

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-210%20passing-2ea44f?style=flat-square&logo=pytest&logoColor=white)](./src/tests/)
[![Coverage](https://img.shields.io/badge/Coverage-83%25-2ea44f?style=flat-square)](./src/tests/)
[![Core Coverage](https://img.shields.io/badge/Core%20Coverage-≥93%25-2ea44f?style=flat-square)](./src/tests/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)](./Dockerfile)
[![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)](./LICENSE)

<br/>

*Arquitetura modular e reprodutível para análise de redes de coautoria parlamentar brasileira usando teoria dos grafos.*
*Transforma dados legislativos brutos em evidências mensuráveis e auditáveis de estruturas de influência política (2022–2025).*

<br/>

> **Premissa (na esteira de Fowler, 2006):** a coautoria parlamentar é adotada como *proxy* **mensurável** de articulação legislativa.
> A arquitetura é a contribuição — a análise de 2022–2025 **demonstra** que ela funciona, não é uma tese política conclusiva.

> 🌎 **English version:** see [README.md](./README.md).

</div>

---

## 🔬 Hipótese de Pesquisa

O trabalho se centra em uma **única hipótese estrutural (topológica)** — formulada sem rótulos ideológicos de partido — validada estatisticamente contra um modelo nulo.

| Hipótese | Enunciado | Veredito |
|-----------|-----------|---------|
| **H1** | A rede de coautoria tem **estrutura de comunidades não-aleatória**: a modularidade observada *Q* é significativamente maior que a de grafos nulos ponderados que preservam a sequência de graus | ✅ Confirmada (4/4 anos, *p* < 0,005) |

**Como é testada.** Para cada ano, a modularidade Louvain observada *Q*ₒᵦₛ é comparada a uma distribuição nula de 200 grafos aleatórios gerados por `double_edge_swap` (que preserva exatamente a sequência de graus). Como o *swap* descarta os pesos das arestas, o conjunto (*multiset*) de pesos originais é reatribuído às arestas reconfiguradas, mantendo o nulo **ponderado e homogêneo** com *Q*ₒᵦₛ. O *p*-valor usa o estimador "+1", *p* = (*r*+1)/(*m*+1) (North et al., 2002), nunca exatamente zero: com 0 nulos alcançando *Q*ₒᵦₛ em 200, *p* = 1/201 ≈ 0,005.

> **H1 é uma condição de validade, não o achado principal.** Antes de interpretar centralidades e comunidades como estruturas de influência, é preciso mostrar que a organização modular não é artefato do acaso ou da sequência de graus. O *Q* observado supera **todos** os grafos nulos nos quatro anos.

> **Entregáveis descritivos.** Além de H1, a arquitetura produz centralidades por nó (grau, intermediação, proximidade, autovetor) e uma segunda partição via Label Propagation. Estes **não** são hipóteses — são a saída analítica da arquitetura. A concordância entre Louvain e Label Propagation é medida pelo Adjusted Rand Index (ARI), como verificação de robustez de H1.

---

## 📊 Principais Resultados (2022–2025)

| Indicador | 2022 | 2023 | 2024 | 2025 |
|-----------|-----:|-----:|-----:|-----:|
| Nós ativos | 273 | 360 | 337 | 331 |
| Arestas de coautoria | 3.085 | 5.082 | 4.426 | 5.407 |
| Densidade | 8,31% | 7,86% | 7,82% | 9,90% |
| **H1** — Louvain *Q*ₒᵦₛ | 0,596 | 0,640 | 0,634 | 0,634 |
| **H1** — Nulo ponderado *Q̄* | 0,370 | 0,420 | 0,415 | 0,467 |
| **H1** — *p*-valor | 0,005 | 0,005 | 0,005 | 0,005 |
| ARI (Louvain × Label Prop.) | 0,325 | 0,281 | 0,416 | 0,423 |

> A modularidade observada é significativamente maior que o nulo ponderado em todos os anos, e **nenhum grafo nulo (de 200) alcança *Q*ₒᵦₛ** — H1 confirmada em todo o período (*p* < 0,005).
>
> **Legislaturas:** 2022 = fim da 56ª; 2023–2025 = 57ª (iniciada em 1º/fev/2023).

---

## 🏗️ Arquitetura

Pipeline em camadas de responsabilidade única, seguindo Arquitetura Limpa + SOLID. A **Regra de Dependência** é estrita e inegociável — faz parte da defesa:

```
extraction → processing → core (Graph + Algorithms) → repository → visualization
```

- `models/` importa apenas a biblioteca padrão (dataclasses puras — sem lib externa de validação, por decisão de projeto).
- `core/` nunca sabe que JSON, SQLite, CSV ou HTTP existem — toda serialização vive em `repository/`.
- Parsing de formatos externos vive exclusivamente em `extraction/` e `processing/`.

| Camada | Responsabilidade |
|-------|----------------|
| **extraction/** | Download e cache local dos CSVs do Portal de Dados Abertos da Câmara (via `pandas`) |
| **processing/** | Limpeza, filtros (tipo de proposição + `max_authors`), sanitização de partido/UF, conversão em objetos de domínio |
| **core/graph.py** | Projeção bipartida → grafo de coautoria ponderado; centralidades; atribuição de comunidades |
| **core/algorithms/** | Métricas de centralidade, detecção de comunidades (Louvain, Label Propagation), validação por modelo nulo (H1), resultado tipado agregado + ARI |
| **models/** | Entidades de domínio (Deputy, Proposition, CoauthorshipEdge, ParliamentaryNetwork) |
| **repository/** | Exportação para CSV, GEXF (Gephi), SQLite e `AnalysisResult` ↔ JSON |
| **visualization/** | Gráficos automáticos por ano |
| **scripts/** | Análise comparativa entre anos e utilitários de manutenção de dados |
| **tests/** | 210 testes, 83% de cobertura total (core ≥ 93%) |

---

## 🧮 Modelo Matemático

**Projeção bipartida** — a rede de deputados (*D*) e proposições (*P*) é projetada só sobre os deputados, produzindo um grafo ponderado onde uma aresta significa "coassinaram ao menos uma proposição".

**Peso da aresta** — normalizado pelo tamanho do grupo para penalizar assinaturas em massa:
```
w(i,j) = Σ  1 / (n_p − 1)    para cada proposição compartilhada p (n_p = nº de autores de p)
```

**Filtro `max_authors`** — proposições com mais de 30 coautores são excluídas da construção de arestas. Uma PEC com 226 signatários gera ~25.400 pares, elevando a densidade a ~85% e inviabilizando a detecção de comunidades. Esse filtro está **ativo** em toda execução; a análise de sensibilidade do limite fica registrada como trabalho futuro.

**Pesos uniformes por tipo (= 1)** — todos os tipos válidos recebem peso 1. Não há escala numérica teoricamente justificada para ponderar PL vs. PEC; a filtragem qualitativa (por tipo) já faz a seleção relevante.

**Representação das centralidades** — cada métrica usa a representação coerente com sua semântica:
- **Grau (força)** e **autovetor** são calculados no grafo **ponderado** (a intensidade da colaboração acumula de forma aditiva).
- **Intermediação** e **proximidade** são calculadas na **topologia não-ponderada**: o NetworkX trata o peso como *distância*, mas aqui o peso codifica *intensidade* do laço (sentido inverso) — usá-lo diretamente trataria laços fortes como distantes.

**Validação por modelo nulo (H1)** — 200 grafos aleatórios via `double_edge_swap` (preserva a sequência de graus) com o multiset de pesos originais reatribuído (ponderado, *like-for-like*). *p*-valor = (*r*+1)/(*m*+1). Aleatoriedade com semente (`seed=42`) para reprodutibilidade total.

**Concordância de partições** — Adjusted Rand Index (ARI) entre Louvain e Label Propagation, em [−1, 1]; 0 é concordância ao acaso, 1 é partições idênticas.

---

## 🚀 Uso

### Pré-requisitos

- Docker + Docker Compose (recomendado — o ambiente canônico é Python 3.11)
- Ou: Python 3.11+ localmente
- Copie `.env.example` para `.env` antes de rodar: `cp .env.example .env`

### Docker (Recomendado)

```bash
docker compose build                     # Builda a imagem
docker compose up pipeline_chamber       # Pipeline multi-ano completo (2022–2025), ~15–25 min
docker compose run --rm compare          # Comparação entre anos (após o pipeline)
docker compose run --rm tests            # Suíte de testes
```

O utilitário `run.sh` encapsula esses comandos: `./run.sh setup | pipeline | compare | test | all | status`.

### Local (sem Docker)

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac  (venv\Scripts\activate no Windows)
pip install -r requirements.txt
cp .env.example .env

python src/main.py              # Roda o pipeline
python scripts/compare_years.py # Comparação entre anos
pytest src/tests/ -v --cov=src  # Testes com cobertura
```

---

## 🔄 Etapas do Pipeline

1. **Extração** — Download/cache dos CSVs de `dadosabertos.camara.leg.br`
2. **Processamento** — Limpeza; filtro por tipos válidos (PL, PLP, PEC, PDL, EMC); filtro `max_authors=30`; sanitização de partido/UF
3. **Construção do grafo** — Projeção bipartida *B*=(*D*∪*P*, *E*) → grafo de coautoria ponderado *G*=(*D*, *E′*, *w*)
4. **Métricas** — Grau, intermediação, proximidade e autovetor para cada deputado
5. **Análise** — Louvain + Label Propagation (concordância ARI); teste de permutação por modelo nulo (H1)
6. **Repositório** — Exportação para CSV, GEXF, SQLite e `analysis_{ano}.json`
7. **Visualização** — Geração de gráficos em `data/plots/{ano}/`

O pipeline roda cada ano de forma independente (2022–2025). Uma falha em um ano não interrompe os outros.

---

## ⚙️ Configuração

Todas as configurações são carregadas e **validadas** do `.env` (ver `.env.example`) via `pydantic-settings`:

```env
# --- PATHS (relativos à raiz do projeto) ---
DB_PATH=data/parliament.db
CACHE_DIR=data/cache
GEXF_DIR=data/gexf
METRICS_DIR=data/metricas
PLOTS_DIR=data/plots

# --- GRAPH ANALYSIS ---
MAX_AUTHORS_PER_PROPOSAL=30
```

---

## 📦 Saída da Análise (`data/analysis/analysis_{ano}.json`)

Cada execução persiste um único JSON legível e auditável por ano — a fonte única de verdade de todo número reportado na monografia:

```jsonc
{
  "year": 2025,
  "n_nodes": 331,
  "n_edges": 5407,
  "density": 0.099002,
  "max_authors": 30,
  "n_permutations": 200,
  "timestamp": "2026-...T...",
  "louvain": { "modularity": 0.633635, "num_communities": 16 },
  "label_propagation": { "modularity": 0.483206, "num_communities": 10 },
  "partition_agreement": {
    "adjusted_rand_index": 0.422886,
    "louvain_num_communities": 16,
    "label_propagation_num_communities": 10
  },
  "null_model": {
    "q_observed": 0.633635,
    "q_null_mean": 0.467,
    "q_null_std": 0.005,
    "p_value": 0.00498,
    "n_permutations": 200,
    "significant": true,
    "alpha": 0.05
  }
}
```

As métricas por deputado são exportadas em `data/metricas/deputados_metricas_{ano}.csv` com colunas em inglês:
`deputy_id, name, party_code, state_code, weighted_degree, degree_centrality, betweenness_centrality, closeness_centrality, eigenvector_centrality, community_louvain`.

---

## 🧪 Suíte de Testes

**210 testes**, **83% de cobertura total**, **core ≥ 93%** (reportado na monografia).

> Os testes de `test_dataset_integrity` validam os datasets por ano e são **pulados graciosamente** até o pipeline gerá-los. Após rodar o pipeline, os 210 passam.

Categorias: testes unitários (entidades de domínio e algoritmos), testes de integração (pipeline ponta a ponta) e testes de integridade de dataset (esquema, faixas de valores plausíveis, coerência CSV ↔ GEXF).

```bash
docker compose run --rm tests
# ou
pytest src/tests/ -v --cov=src --cov-report=term-missing
```

---

## 📚 Dependências Principais

| Pacote | Finalidade |
|---------|---------|
| **networkx** | Construção do grafo, centralidades, algoritmos de comunidade (Louvain + Label Propagation), modelo nulo |
| **pandas** / **pyarrow** | Processamento de dados, download e manipulação de CSVs |
| **pydantic** / **pydantic-settings** | Configuração tipada e validada, carregada do `.env` |
| **matplotlib / seaborn** | Visualização e geração de gráficos |
| **pysqlite3-binary** | Camada de persistência SQLite |
| **pytest / pytest-cov** | Framework de testes e cobertura |

---

## 👤 Autor

**Felipe Echeverria Vilhalva**
Orientador: Prof. Dr. Rubens Barbosa Filho
Universidade Estadual de Mato Grosso do Sul (UEMS)

## 📄 Licença

Licença MIT — ver `LICENSE` para detalhes.
