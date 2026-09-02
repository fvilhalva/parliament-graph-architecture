# CLAUDE.md — Contexto do Projeto

> Arquivo lido automaticamente pelo Claude Code. Contém o essencial para não re-aprender o projeto a cada sessão.

## O que é

**PFC/TCC** de Felipe Echeverria Vilhalva — Bacharelado em Ciência da Computação, **UEMS-Dourados**. Orientador: Prof. Dr. Rubens Barbosa Filho. Defesa em 2026.

**Tema:** arquitetura de software modular e reprodutível (paradigma **Design Science Research – DSR**) para análise de **redes de coautoria** da Câmara dos Deputados via **Teoria dos Grafos**, período **2022–2025**.

**Fio condutor de defesa:** a **contribuição é a ARQUITETURA** (o artefato), não uma tese política. A análise 2022–2025 *demonstra* que o artefato funciona — não é conclusão de ciência política. Sempre preferir "o artefato **viabiliza/mede**" a "eu **provo** influência real".

## Hipótese e perguntas (decisão do orientador: só 1 hipótese)

- **H1 (única, falsificável, topológica):** a modularidade $Q$ da rede é significativamente superior à de grafos nulos ponderados de mesma sequência de graus. Refutada se $p \geq \alpha$. Testada por modelo nulo → **confirmada nos 4 anos, $p<0{,}005$**.
- **3 perguntas norteadoras (descritivas, NÃO hipóteses — respondidas por medição, sem teste de significância):**
  1. Há concentração da articulação em poucos? → **Gini** (extremo no autovetor ~0,95; alto na intermediação ~0,74; moderado no grau ~0,57).
  2. Comunidades = partidos/coalizões? → cruzamento comunidade×partido: **ARI ≈ 0,30, pureza ≈ 48% → mais COALIZÕES que partidos puros** (PT é comunidade pura; o bloco PL+UNIÃO+PP+PSD é coalizão). **Descrever partidos é FACTUAL; evitar rótulo ideológico (esquerda/direita).**
  3. Centralidade prediz influência real? → **mede ARTICULAÇÃO, não poder institucional** (relatorias/pauta não aparecem na coautoria).
- **"Estruturas de influência"** = dois níveis: **comunidades** (macro/blocos, validado por H1) + **centralidades** (micro/quem é ponte ou polo).

## Decisões metodológicas (importantes — a banca cutuca)

- **Peso da aresta:** $w(i,j)=\sum 1/(n_p-1)$ (Newman 2001). **Pesos uniformes por tipo (=1)**.
- **Filtro de tipos:** só PL, PLP, PEC, PDL, EMC. **Nenhuma PEC entra** (todas >30 autores → removidas; é intencional: co-assinatura em massa ≠ articulação).
- **Filtro de massa `max_authors=30`:** complementar à normalização — a normalização trata o **peso**, o filtro trata a **topologia** (existência de arestas). Sem o filtro, densidade → 85% e **Q despenca de 0,63 → 0,21** (prova de que não é redundante). Sensibilidade: Q estável (0,60–0,70) para 20/30/40.
- **Centralidades:** grau e autovetor **PONDERADOS**; intermediação e proximidade **TOPOLÓGICAS** (peso = afinidade, não distância — usar como distância inverteria o sentido). As 4 não são redundantes (correlação Spearman máx 0,72).
- **Modelo nulo:** `double_edge_swap` (preserva graus) **com reatribuição dos pesos** (nulo ponderado, like-for-like). $p=(r+1)/(m+1)$ (nunca zero).
- **Algoritmos:** Louvain (primário, `seed=42`) + Label Propagation (contraprova). ARI(Louvain×LP) ≈ 0,28–0,42 (moderado → convergem no essencial, divergem nas fronteiras).
- **Ano de referência das figuras detalhadas = 2025** (mais recente, regime estável da 57ª; tabelas agregadas usam os 4 anos).

## Estado atual (set/2026)

- **Código:** completo, **217 testes**, 83% cobertura (core ≥93%), Docker, determinístico.
- **Monografia (`doc/monografia.tex`):** Caps. 1–4 escritos e revisados; **Caps. 5 e 6 = templates guiados** (`% NORTE` + tabelas com dados reais + `[PREENCHER]`) — **falta escrever o texto interpretativo** (é o principal pendente).
- **Analiticamente ACABOU:** todas as tabelas, plots, sensibilidade, séries temporais, Gephi. Só falta redigir Cap. 5/6.
- **Pendências menores:** 2 PDFs a caçar (Bonacich 1972, Wieringa 2014); Leiden = trabalho futuro; algumas imagens duplicadas em `doc/imagens/`.

## Convenções (SEGUIR)

- **LaTeX ordinais:** usar `\textsuperscript{a}` (ex.: `57\textsuperscript{a} Legislatura`), **nunca** `ª`/`º` unicode (buga no abntex2).
- **Citações ABNT (abntex2cite, estilo alf):** `\citeonline{chave}` quando o autor é sujeito (→ "Sobrenome (ano)"); `\cite{chave}` parentético (→ "(SOBRENOME, ano)"); `\citeyear` só o ano. **Nunca** misturar nome no texto + `\cite` (duplica o autor).
- **Git:** fluxo main → develop → feat/*. **Commitar antes de trocar de branch** (já se perdeu trabalho por merge com working tree sujo).
- **`data/` é gitignored** (regenerado pelo pipeline). PDFs da bibliografia em `doc/imagens/`? não — bibliografia pesada fica em `doc/bibliografia/` (gitignored).

## Como rodar

```bash
./run.sh pipeline   # pipeline completo 2022–2025 (~15–25 min, Docker)
./run.sh compare    # análise comparativa entre anos
./run.sh test       # 217 testes
```
Requer Docker Desktop ativo. Config via `.env` (pydantic-settings).

## Arquitetura (camadas, Regra de Dependência estrita)

```
extraction → processing → core (Graph + Algorithms) → repository → visualization
```
- `models/` = dataclasses puras (só stdlib). `core/` isolado de I/O. `repository/` = CSV, GEXF (Gephi), SQLite, JSON.
- Fonte única de verdade dos números: `data/analysis/analysis_{ano}.json`.

## Dados para o Cap. 5

- **Tabelas** → `data/analysis/*.json` (Q, nulo, p, ARI, densidade, comunidades, **concentração/Gini**).
- **Top deputados + comunidade×partido** → `data/metricas/deputados_metricas_{ano}.csv`.
- **Figuras** → `data/plots/` (por ano + comparativos) e `doc/imagens/resultados/` (Gephi).
- **Rede no Gephi** → `data/gexf/chamber_graph_{ano}.gexf`. NÃO usar: `data/cache/`, `data/parliament.db`.
