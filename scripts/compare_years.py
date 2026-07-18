"""Multi-year comparative analysis of parliamentary co-authorship networks.

Loads the persisted :class:`AnalysisResult` JSONs for each year plus the
per-deputy metrics CSV, and produces:

  - Summary table printed to stdout
  - data/plots/compare_nodes_edges.png
  - data/plots/compare_modularity.png
  - data/plots/compare_top_betweenness.png

Run from the project root:
    python scripts/compare_years.py

Nothing is recomputed here: modularities, Q values and community counts come
straight from ``data/analysis/analysis_{year}.json``, which is the single
source of truth for those numbers.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd  # type: ignore
import seaborn as sns  # type: ignore

# Make src/ importable without installing the package.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from repository import AnalysisRepository  # noqa: E402

BASE_DIR = Path(__file__).parent.parent
METRICS_DIR = BASE_DIR / "data" / "metricas"
ANALYSIS_DIR = BASE_DIR / "data" / "analysis"
PLOTS_DIR = BASE_DIR / "data" / "plots"

YEARS = [2022, 2023, 2024, 2025]
TOP_N = 10  # deputies shown in the betweenness heatmap


# ── helpers ────────────────────────────────────────────────────────────────

def _load_year(year: int, analysis_repository: AnalysisRepository) -> dict:
    """Return stats dict for one year. Skips year if files are missing."""
    csv_path = METRICS_DIR / f"deputados_metricas_{year}.csv"
    analysis_path = ANALYSIS_DIR / f"analysis_{year}.json"

    if not csv_path.exists():
        print(f"  [skip] {year}: CSV not found ({csv_path})")
        return {}
    if not analysis_path.exists():
        print(f"  [skip] {year}: analysis JSON not found ({analysis_path}). Run the pipeline first.")
        return {}

    df = pd.read_csv(csv_path)
    result = analysis_repository.load(year)

    return {
        "year": year,
        "nodes": result.n_nodes,
        "edges": result.n_edges,
        "density": round(result.density * 100, 2),  # percent
        "q_louvain": round(result.louvain.modularity, 4),
        "n_communities": result.louvain.num_communities,
        "df": df,
        "result": result,
    }


# ── plots ───────────────────────────────────────────────────────────────────

def _plot_nodes_edges(rows: list[dict]) -> None:
    summary = pd.DataFrame([{k: r[k] for k in ("year", "nodes", "edges")} for r in rows])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    sns.barplot(data=summary, x="year", y="nodes", hue="year", palette="Blues_d", ax=ax1, legend=False)
    ax1.set_title("Active Deputies per Year (nodes)")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Nodes")

    sns.barplot(data=summary, x="year", y="edges", hue="year", palette="Oranges_d", ax=ax2, legend=False)
    ax2.set_title("Co-authorship Edges per Year")
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Edges")

    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "compare_nodes_edges.png", dpi=180)
    plt.close(fig)
    print("  Saved: compare_nodes_edges.png")


def _plot_modularity(rows: list[dict]) -> None:
    summary = pd.DataFrame([{k: r[k] for k in ("year", "q_louvain", "n_communities")} for r in rows])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    sns.lineplot(data=summary, x="year", y="q_louvain", marker="o", color="#2b8cbe", ax=ax1)
    ax1.set_title("Louvain Modularity (Q) per Year")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Q")
    ax1.set_ylim(0, 1)
    ax1.set_xticks(summary["year"].tolist())
    ax1.axhline(0.3, linestyle="--", color="gray", linewidth=0.8, label="Q=0.3 threshold")
    ax1.legend(fontsize=8)

    sns.barplot(
        data=summary, x="year", y="n_communities", hue="year", palette="Greens_d", ax=ax2, legend=False
    )
    ax2.set_title("Number of Communities per Year (Louvain)")
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Communities")

    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "compare_modularity.png", dpi=180)
    plt.close(fig)
    print("  Saved: compare_modularity.png")


def _plot_betweenness_heatmap(rows: list[dict]) -> None:
    """Heatmap: top deputies by betweenness across all years."""
    all_names: set[str] = set()
    year_dfs: dict[int, pd.Series] = {}

    for r in rows:
        df = r["df"].copy()
        df["label"] = df["nome"] + " (" + df["sigla_partido"] + ")"
        top = df.nlargest(TOP_N, "betweenness_centrality").set_index("label")["betweenness_centrality"]
        year_dfs[r["year"]] = top
        all_names.update(top.index)

    matrix = pd.DataFrame(index=sorted(all_names), columns=[r["year"] for r in rows], dtype=float)
    for year, series in year_dfs.items():
        matrix[year] = series

    matrix = matrix.fillna(0)
    matrix = matrix.loc[matrix.max(axis=1) > 0]
    matrix = matrix.loc[matrix.mean(axis=1).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(10, max(6, len(matrix) * 0.4)))
    sns.heatmap(
        matrix,
        annot=True,
        fmt=".3f",
        cmap="YlOrRd",
        linewidths=0.4,
        ax=ax,
        cbar_kws={"label": "Betweenness Centrality"},
    )
    ax.set_title(f"Top {TOP_N} Deputies by Betweenness Centrality (2022–2025)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Deputy")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "compare_top_betweenness.png", dpi=180)
    plt.close(fig)
    print("  Saved: compare_top_betweenness.png")


# ── main ────────────────────────────────────────────────────────────────────

def main() -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", palette="deep")

    analysis_repository = AnalysisRepository(ANALYSIS_DIR)

    print("Loading data for each year...")
    rows = [r for year in YEARS if (r := _load_year(year, analysis_repository))]

    if not rows:
        print("No data found. Run the pipeline first for each year.")
        return

    # ── Summary table ──
    cols = ["year", "nodes", "edges", "density", "q_louvain", "n_communities"]
    summary = pd.DataFrame([{c: r[c] for c in cols} for r in rows])
    summary.columns = ["Year", "Nodes", "Edges", "Density (%)", "Q Louvain", "Communities"]
    print("\n=== Multi-year Summary ===")
    print(summary.to_string(index=False))

    # ── PP-level highlights (from persisted analysis results) ──
    print("\n=== Concentration (Gini) per year ===")
    for r in rows:
        result = r["result"]
        for metric, conc in result.concentration.items():
            print(
                f"  {r['year']} {metric}: Gini={conc.gini:.3f} "
                f"(top 5% = {conc.top_share.get(0.05, 0.0):.1%})"
            )

    print("\n=== Community composition per year ===")
    for r in rows:
        result = r["result"]
        composition = result.community_composition
        if composition is None:
            continue
        print(
            f"  {r['year']}: verdict={composition.verdict}, "
            f"pureza={composition.mean_purity:.2f}, "
            f"multipartidárias={composition.multiparty_fraction:.0%}, "
            f"coalizões={composition.coalition_fraction:.0%}"
        )

    print("\n=== PP3 (centrality × relatorship) per year ===")
    for r in rows:
        result = r["result"]
        pp3 = result.pp3_relatorship
        if pp3 is None:
            print(f"  {r['year']}: no PP3 result")
            continue
        print(f"  {r['year']}: {pp3}")

    # ── Top deputies per year ──
    print("\n=== Top 5 by Betweenness Centrality per Year ===")
    for r in rows:
        df = r["df"]
        top = df.nlargest(5, "betweenness_centrality")[["nome", "sigla_partido", "betweenness_centrality"]]
        print(f"\n{r['year']}:")
        print(top.to_string(index=False))

    # ── Plots ──
    print("\nGenerating plots...")
    _plot_nodes_edges(rows)
    _plot_modularity(rows)
    if len(rows) > 1:
        _plot_betweenness_heatmap(rows)
    else:
        print("  [skip] heatmap requires data for 2+ years")

    print(f"\nDone. Plots saved to: {PLOTS_DIR}")


if __name__ == "__main__":
    main()
