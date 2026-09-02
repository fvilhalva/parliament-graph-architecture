"""Visualization utilities for parliamentary network analysis."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd # type: ignore
import seaborn as sns # type: ignore

from config import Config
from core.algorithms.metrics import gini_coefficient

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
METRICS_DIR = DATA_DIR / "metricas"
GEXF_DIR = DATA_DIR / "gexf"
PLOTS_DIR = DATA_DIR / "plots"


def _configure_style() -> None:
    """Configure matplotlib and seaborn style for consistency."""
    sns.set_theme(style="whitegrid", palette="deep")
    plt.rcParams["figure.figsize"] = (12, 7)
    plt.rcParams["axes.titlesize"] = 14
    plt.rcParams["axes.labelsize"] = 11


def _load_metrics(year: int) -> pd.DataFrame:
    """Load deputy metrics CSV for a given year.
    
    Args:
        year: Legislature year
        
    Returns:
        DataFrame with deputy metrics
        
    Raises:
        FileNotFoundError: If CSV does not exist
    """
    csv_path = METRICS_DIR / f"deputados_metricas_{year}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Metrics CSV not found: {csv_path}")
    return pd.read_csv(csv_path)


def _analyze_graph(year: int) -> tuple[nx.Graph | nx.DiGraph | None, dict[str, float | int | str]]:
    """Load and analyze graph statistics from GEXF file.
    
    Args:
        year: Legislature year
        
    Returns:
        Tuple of (graph, statistics_dict)
    """
    gexf_path = GEXF_DIR / f"chamber_graph_{year}.gexf"
    if not gexf_path.exists():
        return None, {"note": f"GEXF not found: {gexf_path}"}

    graph = nx.read_gexf(gexf_path)
    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()
    density = nx.density(graph) if num_nodes > 1 else 0.0

    if num_nodes > 0:
        if graph.is_directed():
            components = list(nx.weakly_connected_components(graph))
        else:
            components = list(nx.connected_components(graph))
        largest_component = max((len(c) for c in components), default=0)
    else:
        components = []
        largest_component = 0

    statistics = {
        "nodes": num_nodes,
        "edges": num_edges,
        "density": density,
        "num_components": len(components),
        "largest_component_size": largest_component,
        "is_directed": str(graph.is_directed()),
    }
    return graph, statistics


def _plot_top_deputies_betweenness(df: pd.DataFrame, output_dir: Path, n: int = 20) -> None:
    """Plot top N deputies by betweenness centrality."""
    top_df = df.nlargest(n, "betweenness_centrality").copy().iloc[::-1]
    top_df["label"] = top_df["name"] + " (" + top_df["party_code"] + ")"

    fig, ax = plt.subplots()
    sns.barplot(data=top_df, x="betweenness_centrality", y="label", hue="party_code", dodge=False, ax=ax)
    ax.set_title(f"Top {n} Deputies by Betweenness Centrality")
    ax.set_xlabel("Betweenness Centrality")
    ax.set_ylabel("Deputy")
    ax.legend(title="Party", loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "top_deputies_betweenness.png", dpi=180)
    plt.close(fig)


def _plot_top_deputies(df: pd.DataFrame, output_dir: Path, n: int = 20) -> None:
    """Plot top N deputies by weighted degree.
    
    Args:
        df: Deputy metrics DataFrame
        output_dir: Output directory for plot
        n: Number of top deputies to display
    """
    top_df = df.nlargest(n, "weighted_degree").copy().iloc[::-1]
    top_df["label"] = top_df["name"] + " (" + top_df["party_code"] + ")"

    fig, ax = plt.subplots()
    sns.barplot(data=top_df, x="weighted_degree", y="label", hue="party_code", dodge=False, ax=ax)
    ax.set_title(f"Top {n} Deputies by Weighted Degree")
    ax.set_xlabel("Weighted Degree")
    ax.set_ylabel("Deputy")
    ax.legend(title="Party", loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "top_deputies_weighted_degree.png", dpi=180)
    plt.close(fig)


def _plot_parties(df: pd.DataFrame, output_dir: Path, n: int = 15) -> None:
    """Plot top N parties by number of deputies and average weighted degree.
    
    Args:
        df: Deputy metrics DataFrame
        output_dir: Output directory for plot
        n: Number of top parties to display
    """
    parties = (
        df.groupby("party_code", as_index=False)
        .agg(num_deputies=("deputy_id", "count"), avg_weighted_degree=("weighted_degree", "mean"))
        .sort_values("num_deputies", ascending=False)
        .head(n)
    )

    fig, ax = plt.subplots()
    sns.barplot(data=parties, x="num_deputies", y="party_code", color="#2b8cbe", ax=ax)
    ax.set_title(f"Top {n} Parties by Number of Deputies")
    ax.set_xlabel("Number of Deputies")
    ax.set_ylabel("Party")
    fig.tight_layout()
    fig.savefig(output_dir / "parties_num_deputies.png", dpi=180)
    plt.close(fig)


def _plot_metrics_correlation(df: pd.DataFrame, output_dir: Path) -> None:
    """Plot correlation between degree centrality and betweenness centrality.
    
    Args:
        df: Deputy metrics DataFrame
        output_dir: Output directory for plot
    """
    fig, ax = plt.subplots()
    sns.scatterplot(
        data=df,
        x="degree_centrality",
        y="betweenness_centrality",
        hue="party_code",
        size="weighted_degree",
        sizes=(20, 220),
        alpha=0.75,
        linewidth=0,
        ax=ax,
        legend=False,
    )
    ax.set_title("Relationship between Degree and Betweenness Centrality")
    ax.set_xlabel("Degree Centrality")
    ax.set_ylabel("Betweenness Centrality")
    fig.tight_layout()
    fig.savefig(output_dir / "centrality_correlation.png", dpi=180)
    plt.close(fig)


def _plot_top_deputies_eigenvector(df: pd.DataFrame, output_dir: Path, n: int = 20) -> None:
    """Plot top N deputies by eigenvector centrality."""
    top_df = df.nlargest(n, "eigenvector_centrality").copy().iloc[::-1]
    top_df["label"] = top_df["name"] + " (" + top_df["party_code"] + ")"

    fig, ax = plt.subplots()
    sns.barplot(data=top_df, x="eigenvector_centrality", y="label", hue="party_code", dodge=False, ax=ax)
    ax.set_title(f"Top {n} Deputies by Eigenvector Centrality")
    ax.set_xlabel("Eigenvector Centrality")
    ax.set_ylabel("Deputy")
    ax.legend(title="Party", loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "top_deputies_eigenvector.png", dpi=180)
    plt.close(fig)


def _plot_top_deputies_closeness(df: pd.DataFrame, output_dir: Path, n: int = 20) -> None:
    """Plot top N deputies by closeness centrality."""
    top_df = df.nlargest(n, "closeness_centrality").copy().iloc[::-1]
    top_df["label"] = top_df["name"] + " (" + top_df["party_code"] + ")"

    fig, ax = plt.subplots()
    sns.barplot(data=top_df, x="closeness_centrality", y="label", hue="party_code", dodge=False, ax=ax)
    ax.set_title(f"Top {n} Deputies by Closeness Centrality")
    ax.set_xlabel("Closeness Centrality")
    ax.set_ylabel("Deputy")
    ax.legend(title="Party", loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "top_deputies_closeness.png", dpi=180)
    plt.close(fig)


def _plot_centrality_correlation_heatmap(df: pd.DataFrame, output_dir: Path) -> None:
    """Plot the Spearman correlation matrix between the four centrality metrics.

    Spearman (rank) correlation is used because centrality distributions are
    highly skewed. Low off-diagonal values are evidence that the four metrics
    capture distinct dimensions of influence (i.e. they are not redundant).
    """
    columns = ["weighted_degree", "betweenness_centrality", "closeness_centrality", "eigenvector_centrality"]
    labels = ["Weighted Degree", "Betweenness", "Closeness", "Eigenvector"]
    corr = df[columns].corr(method="spearman")
    corr.index = labels
    corr.columns = labels

    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(
        corr, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1,
        square=True, linewidths=0.5, cbar_kws={"shrink": 0.8}, ax=ax,
    )
    ax.set_title("Correlation between Centrality Metrics (Spearman)")
    fig.tight_layout()
    fig.savefig(output_dir / "centrality_correlation_heatmap.png", dpi=180)
    plt.close(fig)


def _plot_concentration(df: pd.DataFrame, output_dir: Path) -> None:
    """Lorenz curves of the centrality distributions (visual concentration).

    Each curve plots the cumulative share of centrality (y) against the
    cumulative share of deputies (x), sorted ascending. The dashed diagonal is
    perfect equality; the further a curve bows below it, the more concentrated
    the metric --- the Gini coefficient is the area between the diagonal and the
    curve. Reported in the legend for each metric.
    """
    metrics = {
        "Weighted Degree": ("weighted_degree", "#2b8cbe"),
        "Betweenness": ("betweenness_centrality", "#31a354"),
        "Closeness": ("closeness_centrality", "#e6550d"),
        "Eigenvector": ("eigenvector_centrality", "#756bb1"),
    }

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", linewidth=1.2, label="Perfect equality")

    for label, (column, color) in metrics.items():
        values = np.sort(df[column].to_numpy(dtype=float))
        total = values.sum()
        if total <= 0:
            continue
        cumulative = np.insert(np.cumsum(values) / total, 0, 0.0)
        population = np.linspace(0.0, 1.0, len(cumulative))
        ax.plot(
            population, cumulative, linewidth=2.2, color=color,
            label=f"{label} (Gini = {gini_coefficient(values):.2f})",
        )

    ax.set_title("Lorenz Curves of Centrality Concentration")
    ax.set_xlabel("Cumulative share of deputies")
    ax.set_ylabel("Cumulative share of centrality")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.legend(loc="upper left", fontsize=9, frameon=True)
    fig.tight_layout()
    fig.savefig(output_dir / "concentration_gini.png", dpi=180)
    plt.close(fig)


def _plot_degree_distribution(df: pd.DataFrame, output_dir: Path) -> None:
    """Plot distribution of weighted degree across all deputies.
    
    Args:
        df: Deputy metrics DataFrame
        output_dir: Output directory for plot
    """
    fig, ax = plt.subplots()
    sns.histplot(df["weighted_degree"], bins=35, kde=True, color="#f16913", ax=ax)
    ax.set_title("Distribution of Weighted Degree")
    ax.set_xlabel("Weighted Degree")
    ax.set_ylabel("Frequency")
    fig.tight_layout()
    fig.savefig(output_dir / "degree_distribution.png", dpi=180)
    plt.close(fig)


def _plot_graph_components(graph: nx.Graph | nx.DiGraph, output_dir: Path, top_n: int = 15) -> None:
    """Plot sizes of graph connected components.
    
    Args:
        graph: NetworkX graph
        output_dir: Output directory for plot
        top_n: Number of top components to display
    """
    if graph.is_directed():
        components = [len(c) for c in nx.weakly_connected_components(graph)]
    else:
        components = [len(c) for c in nx.connected_components(graph)]

    if not components:
        return

    sorted_components = sorted(components, reverse=True)[:top_n]
    plot_data = pd.DataFrame(
        {
            "component": [f"C{i + 1}" for i in range(len(sorted_components))],
            "size": sorted_components,
        }
    )

    fig, ax = plt.subplots()
    sns.barplot(data=plot_data, x="component", y="size", color="#7bccc4", ax=ax)
    ax.set_title(f"Top {top_n} Components by Size")
    ax.set_xlabel("Component")
    ax.set_ylabel("Number of Nodes")
    fig.tight_layout()
    fig.savefig(output_dir / "graph_components.png", dpi=180)
    plt.close(fig)


def _save_report(output_dir: Path, stats: dict[str, float | int | str], total_deputies: int, year: int) -> None:
    """Save analysis report to text file.
    
    Args:
        output_dir: Output directory
        stats: Graph statistics dictionary
        total_deputies: Total number of deputies in dataset
        year: Legislature year
    """
    lines = [
        f"Analysis Report - Parliamentary Network {year}",
        "=" * 50,
        f"Total deputies in dataset: {total_deputies}",
        "",
        "Graph statistics:",
    ]
    for key, value in stats.items():
        lines.append(f"- {key}: {value}")
    (output_dir / "analysis_summary.txt").write_text("\n".join(lines), encoding="utf-8")


def generate_analysis_plots(year: int = 2025) -> Path:
    """Generate analysis plots and report for a given legislature year.

    All outputs are written to ``data/plots/<year>/`` so each year keeps its
    own isolated set of figures and the analysis summary — multi-year runs
    no longer overwrite each other.

    Args:
        year: Legislature year (default: 2025)

    Returns:
        Path to the per-year output directory containing generated plots.
    """
    year_dir = PLOTS_DIR / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)
    _configure_style()

    df = _load_metrics(year)
    _plot_top_deputies(df, year_dir)
    _plot_top_deputies_betweenness(df, year_dir)
    _plot_top_deputies_closeness(df, year_dir)
    _plot_top_deputies_eigenvector(df, year_dir)
    _plot_parties(df, year_dir)
    _plot_metrics_correlation(df, year_dir)
    _plot_centrality_correlation_heatmap(df, year_dir)
    _plot_concentration(df, year_dir)
    _plot_degree_distribution(df, year_dir)

    graph, stats = _analyze_graph(year)
    if graph is not None:
        _plot_graph_components(graph, year_dir)

    _save_report(year_dir, stats, total_deputies=len(df), year=year)
    return year_dir


if __name__ == "__main__":
    output = generate_analysis_plots(year=2025)
    print(f"Plots saved to: {output}")