# Arquitetura de Análise de Redes Parlamentares

## Análise de Estruturas de Influência Baseada em Teoria dos Grafos

Projeto de TCC/PFC(Projeto Final de Curso) que implementa uma arquitetura modular para análise de redes parlamentares, identificando estruturas de influência através de métricas de centralidade e detecção de comunidades.

**Período**: 2006-2026 (20 anos de dados históricos do Congresso Nacional Brasileiro)

---

## 🏗️ Arquitetura

A arquitetura segue o padrão de camadas com responsabilidades bem definidas:

```
extraction → processing → core (Graph + Algorithms) → repository → visualization
```

### Camadas

| Camada | Responsabilidade | Status |
|--------|------------------|--------|
| **extraction/** | Coleta de dados brutos da API | ✅ Implementado |
| **processing/** | Limpeza, transformação, conversão em objetos | ✅ Implementado |
| **core/Graph.py** | Construção e operações do grafo | ✅ Implementado |
| **core/algorithms/** | Métricas e detecção de comunidades | ✅ Template pronto |
| **models/** | Entidades do domínio | ✅ Implementado |
| **repository/** | Persistência (CSV, GEXF, SQLite) | ⏳ TODO |
| **visualization/** | Visualizações e plots | ⏳ TODO |
| **tests/** | Suite de testes automatizados | ✅ Estrutura pronta |

---

## 📁 Estrutura de Diretórios

```
parliament-graph-architecture/
├── src/
│   ├── config/              # Configurações gerais
│   │   ├── __init__.py
│   │   └── configs.py
│   ├── core/
│   │   ├── Graph.py         # Classe principal do grafo
│   │   └── algorithms/      # Módulo de análise
│   │       ├── __init__.py
│   │       ├── metrics.py           # Centralidade, closeness, etc
│   │       └── community_detection.py  # Detecção de comunidades
│   ├── extraction/
│   │   ├── __init__.py
│   │   └── extractor.py     # Coleta de dados brutos
│   ├── models/
│   │   ├── deputado.py      # Entidade Deputado
│   │   ├── proposicao.py    # Entidade Proposição
│   │   ├── aresta_coautoria.py  # Aresta entre deputados
│   │   └── rede_parlamentar.py  # Agregação de dados
│   ├── processing/
│   │   ├── __init__.py
│   │   └── processing.py    # Classe GraphNetwork (pipeline)
│   ├── repository/
│   │   ├── csv_repository.py    # Exportação CSV
│   │   ├── graph_exporter.py    # Exportação GEXF/Gephi
│   │   └── db_repository.py     # Persistência SQLite
│   ├── visualization/
│   │   ├── __init__.py
│   │   └── plots.py         # Visualizações
│   ├── tests/               # Suite de testes
│   │   ├── conftest.py      # Fixtures compartilhadas
│   │   ├── test_deputado.py
│   │   ├── test_proposicao.py
│   │   ├── test_aresta_coautoria.py
│   │   ├── test_graph.py
│   │   ├── test_processing.py
│   │   └── test_repository.py
│   ├── main.py              # Entrada principal
│   └── testar.py            # Script de testes
├── data/
│   ├── gexf/                # Grafos em formato GEXF (2006-2026)
│   ├── metricas/            # CSVs com métricas de centralidade
│   ├── plots/               # Gráficos gerados
│   ├── historico_*.csv      # Dados históricos agregados
│   └── parliament.db        # Banco de dados SQLite (gerado)
├── docker-compose.yml       # Orquestração de containers
├── Dockerfile               # Imagem Docker
├── requirements.txt         # Dependências Python
├── LICENSE
└── README.md               # Este arquivo
```

---

## 🚀 Como Usar

### Prerequisitos

- Docker e Docker Compose
- Ou: Python 3.11+ com `pip`

### Com Docker (Recomendado)

```bash
# Build e rodar tudo (pipeline + testes)
docker-compose up --build

# Ou em background
docker-compose up --build -d
```

### Dados Offline (manual)

O pipeline agora le os CSVs localmente (sem download automatico). Baixe os arquivos e coloque em `data/` ou `data/cache/`.

Links diretos (exemplo para 2024):

- `proposicoesAutores-2024.csv`: `https://dadosabertos.camara.leg.br/arquivos/proposicoesAutores/csv/proposicoesAutores-2024.csv`
- `proposicoes-2024.csv`: `https://dadosabertos.camara.leg.br/arquivos/proposicoes/csv/proposicoes-2024.csv`

Nomes esperados por ano `YYYY`:

- `proposicoesAutores-YYYY.csv`
- `proposicoes-YYYY.csv`

**Rodar componentes separados:**

```bash
# Apenas pipeline principal
docker-compose run --build pipeline_camara python src/main.py

# Apenas testes
docker-compose run --build tests

# Testes com cobertura detalhada
docker-compose run --build tests pytest src/tests/ --cov=src --cov-report=term-missing
```

### Sem Docker

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Rodar testes
pytest src/tests/ -v
```

---

## 📊 Modelos de Dados

### Deputado
```python
@dataclass
class Deputado:
    id_deputado: int
    nome: str
    sigla_partido: str
    sigla_uf: str
    degree_centrality: float = 0.0
    betweenness_centrality: float = 0.0
```

### Proposição
```python
@dataclass
class Proposicao:
    id_proposicao: int
    ano: int
    ementa: str
    autores_ids: List[int]  # IDs dos deputados que assinaram
```

### Aresta de Coautoria
```python
@dataclass
class ArestaCoautoria:
    source_id: int           # ID deputado 1
    target_id: int           # ID deputado 2
    peso_bruto: int          # Quantidade de projetos juntos
    forca_normalizada: float = 0.0  # Índice normalizado
```

---

## 📈 Funcionalidades Implementadas

### ✅ Concluído
- [x] Estrutura de arquitetura em camadas
- [x] Modelos de dados (Deputado, Proposição, ArestaCoautoria)
- [x] Template dos algoritmos (métricas + comunidades)
- [x] Template da Suite de testes estruturada (conftest + 6 módulos)
- [x] Docker + Docker Compose
- [x] Implementação completa do `CamaraExtrator` (extraction)
- [x] Implementação completa do `CamaraGraphy` (core)
- [x] Implementação Completa do `CamaraProcessor` (processing)
- [x] Algoritmos de centralidade (degree, betweenness, closeness, eigenvector)

### ⏳ Em Desenvolvimento
- [ ] Dados históricos (20 anos em GEXF)
- [ ] Detecção de comunidades (Louvain, Spectral Clustering)
- [ ] Exportação para GEXF/Gephi
- [ ] Persistência em SQLite
- [ ] Visualizações (matplotlib, seaborn)
- [ ] Análise temporal (evolução das estruturas)

### 🔄 Futuro
- [ ] API REST para consultas
- [ ] Dashboard web
- [ ] Machine Learning (GNN, classificação)
- [ ] Análise de sentimentos
- [ ] Integração contínua (CI/CD)

---

## 📚 Dependências Principais
- **requests** (2.31.0) - processar APIs
- **pandas** (2.2.0) - Processamento de dados
- **networkx** (3.2.1) - Análise de grafos
- **scikit-learn** (1.4.1) - Clustering e ML
- **scipy** (1.12.0) - Operações científicas
- **matplotlib** (3.8.3) - Visualizações
- **seaborn** (0.13.2) - Gráficos estatísticos
- **pytest** (7.4.3) - Framework de testes
- **python-dotenv** (1.0.1) - Variáveis de ambiente
- **pytest-cov** (4.1.0) - ajudar no pytest
- **pyarrow** (15.0.0) - 

---

## 🧪 Testes

A suite de testes está estruturada em 6 módulos com **76 testes** e **65% de cobertura de código**:

```bash
# Rodar via docker (recomendado)
docker-compose up --build

# Ou rodar direto com pytest
pytest src/tests/ -v

# Com cobertura detalhada
pytest src/tests/ --cov=src --cov-report=html
```

**Status:** ✅ 76/76 testes passando

---

## 📝 Documentação

**TODO**: Adicionar documentação detalhada conforme implementação avança.

- [ ] Guia de contribuição
- [ ] Documentação de API
- [ ] Exemplos de uso
- [ ] Relatórios de análise

---

## 📅 Progresso

| Data | Atividade | Status |
|------|-----------|--------|
| 2026-03-09 | Setup inicial + arquitetura | ✅ |
| 2026-03-09 | Suite de testes (76 testes, 65% cobertura) | ✅ |
| 2026-03-10 | Implementação do Graph (implementarei mais funcionalidades) | ✅ |
| **TBD** | Processamento completo | ⏳ |
| **TBD** | Algoritmos + testes | ⏳ |
| **TBD** | Visualizações | ⏳ |
| **TBD** | Análise final | ⏳ |

---

## 👤 Autor

Felipe Echeverria Vilhalva

## 📄 Licença

MIT License - veja arquivo `LICENSE` para detalhes.

---

## 🤝 Contratos da Arquitetura

**extraction** → retorna DataFrame bruto
**processing** → retorna (deputados[], proposições[], arestas[])
**core** → constrói grafo + calcula métricas
**repository** → salva em CSV/GEXF/SQLite
**visualization** → gera plots

---

## ⚠️ Alerta de Conectividade

Se estiver usando notebook com Wi-Fi fraco (ou sem conexão cabeada), baixe antes os arquivos para `data/cache/` usando os links completos:

- `https://dadosabertos.camara.leg.br/arquivos/proposicoesAutores/csv/proposicoesAutores-YYYY.csv`
- `https://dadosabertos.camara.leg.br/arquivos/proposicoes/csv/proposicoes-YYYY.csv`