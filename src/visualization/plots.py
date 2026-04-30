"""Visualization utilities for parliamentary network analysis."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd # type: ignore
import seaborn as sns # type: ignore

from config import Config

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


def _plot_top_deputies(df: pd.DataFrame, output_dir: Path, n: int = 20) -> None:
    """Plot top N deputies by weighted degree.
    
    Args:
        df: Deputy metrics DataFrame
        output_dir: Output directory for plot
        n: Number of top deputies to display
    """
    top_df = df.nlargest(n, "weighted_degree").copy().iloc[::-1]
    top_df["label"] = top_df["nome"] + " (" + top_df["sigla_partido"] + ")"

    fig, ax = plt.subplots()
    sns.barplot(data=top_df, x="weighted_degree", y="label", hue="sigla_partido", dodge=False, ax=ax)
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
        df.groupby("sigla_partido", as_index=False)
        .agg(num_deputies=("id_deputado", "count"), avg_weighted_degree=("weighted_degree", "mean"))
        .sort_values("num_deputies", ascending=False)
        .head(n)
    )

    fig, ax = plt.subplots()
    sns.barplot(data=parties, x="num_deputies", y="sigla_partido", color="#2b8cbe", ax=ax)
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
        hue="sigla_partido",
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
    
    Creates visualizations of deputy metrics, party statistics, centrality
    correlations, degree distribution, and graph components.
    
    Args:
        year: Legislature year (default: 2025)
        
    Returns:
        Path to output directory containing generated plots
    """
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    _configure_style()

    df = _load_metrics(year)
    _plot_top_deputies(df, PLOTS_DIR)
    _plot_parties(df, PLOTS_DIR)
    _plot_metrics_correlation(df, PLOTS_DIR)
    _plot_degree_distribution(df, PLOTS_DIR)

    graph, stats = _analyze_graph(year)
    if graph is not None:
        _plot_graph_components(graph, PLOTS_DIR)

    _save_report(PLOTS_DIR, stats, total_deputies=len(df), year=year)
    return PLOTS_DIR


def function_1(algo: int = 2025) -> Path:
    """Compat: mantem API antiga e gera a analise completa."""
    return gerar_analise_plots(ano=int(algo))


def function_2(algo: int = 2025) -> Path:
    """Compat: alias de function_1."""
    return gerar_analise_plots(ano=int(algo))


if __name__ == "__main__":
    pasta_saida = gerar_analise_plots(ano=2025)
    print(f"Analise finalizada. Arquivos salvos em: {pasta_saida}")