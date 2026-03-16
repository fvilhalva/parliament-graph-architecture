from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd # type: ignore
import seaborn as sns # type: ignore

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
METRICAS_DIR = DATA_DIR / "metricas"
GEXF_DIR = DATA_DIR / "gexf"
PLOTS_DIR = DATA_DIR / "plots"


def _configurar_estilo() -> None:
    sns.set_theme(style="whitegrid", palette="deep")
    plt.rcParams["figure.figsize"] = (12, 7)
    plt.rcParams["axes.titlesize"] = 14
    plt.rcParams["axes.labelsize"] = 11


def _carregar_metricas(ano: int) -> pd.DataFrame:
    csv_path = METRICAS_DIR / f"deputados_metricas_{ano}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV de metricas nao encontrado: {csv_path}")
    return pd.read_csv(csv_path)


def _analisar_grafo(ano: int) -> tuple[nx.Graph | nx.DiGraph | None, dict[str, float | int | str]]:
    gexf_path = GEXF_DIR / f"grafo_camara_{ano}.gexf"
    if not gexf_path.exists():
        return None, {"observacao": f"GEXF nao encontrado: {gexf_path}"}

    g = nx.read_gexf(gexf_path)
    n_nodes = g.number_of_nodes()
    n_edges = g.number_of_edges()
    densidade = nx.density(g) if n_nodes > 1 else 0.0

    if n_nodes > 0:
        if g.is_directed():
            componentes = list(nx.weakly_connected_components(g))
        else:
            componentes = list(nx.connected_components(g))
        maior_comp = max((len(c) for c in componentes), default=0)
    else:
        componentes = []
        maior_comp = 0

    stats = {
        "nos": n_nodes,
        "arestas": n_edges,
        "densidade": densidade,
        "componentes": len(componentes),
        "maior_componente": maior_comp,
        "direcionado": str(g.is_directed()),
    }
    return g, stats


def _plot_top_deputados(df: pd.DataFrame, output_dir: Path, n: int = 20) -> None:
    top_df = df.nlargest(n, "weighted_degree").copy().iloc[::-1]
    top_df["rotulo"] = top_df["nome"] + " (" + top_df["sigla_partido"] + ")"

    fig, ax = plt.subplots()
    sns.barplot(data=top_df, x="weighted_degree", y="rotulo", hue="sigla_partido", dodge=False, ax=ax)
    ax.set_title(f"Top {n} deputados por grau ponderado")
    ax.set_xlabel("Weighted degree")
    ax.set_ylabel("Deputado")
    ax.legend(title="Partido", loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "top_deputados_weighted_degree.png", dpi=180)
    plt.close(fig)


def _plot_partidos(df: pd.DataFrame, output_dir: Path, n: int = 15) -> None:
    partidos = (
        df.groupby("sigla_partido", as_index=False)
        .agg(qtd_deputados=("id_deputado", "count"), media_weighted_degree=("weighted_degree", "mean"))
        .sort_values("qtd_deputados", ascending=False)
        .head(n)
    )

    fig, ax = plt.subplots()
    sns.barplot(data=partidos, x="qtd_deputados", y="sigla_partido", color="#2b8cbe", ax=ax)
    ax.set_title(f"Top {n} partidos por quantidade de deputados")
    ax.set_xlabel("Quantidade de deputados")
    ax.set_ylabel("Partido")
    fig.tight_layout()
    fig.savefig(output_dir / "partidos_qtd_deputados.png", dpi=180)
    plt.close(fig)


def _plot_correlacao_metricas(df: pd.DataFrame, output_dir: Path) -> None:
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
    ax.set_title("Relacao entre degree centrality e betweenness")
    ax.set_xlabel("Degree centrality")
    ax.set_ylabel("Betweenness centrality")
    fig.tight_layout()
    fig.savefig(output_dir / "correlacao_centralidades.png", dpi=180)
    plt.close(fig)


def _plot_distribuicao_grau(df: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots()
    sns.histplot(df["weighted_degree"], bins=35, kde=True, color="#f16913", ax=ax)
    ax.set_title("Distribuicao de weighted degree")
    ax.set_xlabel("Weighted degree")
    ax.set_ylabel("Frequencia")
    fig.tight_layout()
    fig.savefig(output_dir / "distribuicao_weighted_degree.png", dpi=180)
    plt.close(fig)


def _plot_componentes_grafo(g: nx.Graph | nx.DiGraph, output_dir: Path, top_n: int = 15) -> None:
    if g.is_directed():
        componentes = [len(c) for c in nx.weakly_connected_components(g)]
    else:
        componentes = [len(c) for c in nx.connected_components(g)]

    if not componentes:
        return

    componentes_ordenados = sorted(componentes, reverse=True)[:top_n]
    dados_plot = pd.DataFrame(
        {
            "componente": [f"C{i + 1}" for i in range(len(componentes_ordenados))],
            "tamanho": componentes_ordenados,
        }
    )

    fig, ax = plt.subplots()
    sns.barplot(data=dados_plot, x="componente", y="tamanho", color="#7bccc4", ax=ax)
    ax.set_title(f"Top {top_n} componentes por tamanho")
    ax.set_xlabel("Componente")
    ax.set_ylabel("Numero de nos")
    fig.tight_layout()
    fig.savefig(output_dir / "componentes_grafo.png", dpi=180)
    plt.close(fig)


def _salvar_relatorio(output_dir: Path, stats: dict[str, float | int | str], total_deputados: int, ano: int) -> None:
    linhas = [
        f"Relatorio de analise - Rede Parlamentar {ano}",
        "=" * 48,
        f"Total de deputados no CSV: {total_deputados}",
        "",
        "Estatisticas do grafo:",
    ]
    for chave, valor in stats.items():
        linhas.append(f"- {chave}: {valor}")
    (output_dir / "resumo_analise.txt").write_text("\n".join(linhas), encoding="utf-8")


def gerar_analise_plots(ano: int = 2025) -> Path:
    """Gera graficos e relatorio em data/plots para um ano especifico."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    _configurar_estilo()

    df = _carregar_metricas(ano)
    _plot_top_deputados(df, PLOTS_DIR)
    _plot_partidos(df, PLOTS_DIR)
    _plot_correlacao_metricas(df, PLOTS_DIR)
    _plot_distribuicao_grau(df, PLOTS_DIR)

    grafo, stats = _analisar_grafo(ano)
    if grafo is not None:
        _plot_componentes_grafo(grafo, PLOTS_DIR)

    _salvar_relatorio(PLOTS_DIR, stats, total_deputados=len(df), ano=ano)
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