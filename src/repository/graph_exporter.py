from pathlib import Path
from typing import Any
import networkx as nx


class GraphExporter:
    """Exporta e importa grafos no formato GEXF para uso no Gephi."""

    def __init__(self, output_dir: Path | str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _obter_grafo_nx(self, grafo: Any) -> nx.Graph:
        """Aceita nx.Graph ou objeto da aplicacao com atributo G."""
        if isinstance(grafo, nx.Graph):
            return grafo

        # Backwards-compatible: accept attribute names `G` (legacy) or `graph` (current dataclass)
        if hasattr(grafo, "G") and isinstance(grafo.G, nx.Graph):
            return grafo.G

        if hasattr(grafo, "graph") and isinstance(grafo.graph, nx.Graph):
            return grafo.graph

        raise TypeError("'grafo' deve ser nx.Graph ou objeto com atributo 'G' do tipo nx.Graph")

    def exportar_gexf(
        self,
        grafo: Any,
        ano: int | None = None,
        nome_arquivo: str | None = None,
    ) -> Path:
        """
        Exporta o grafo para GEXF.

        Args:
            grafo: nx.Graph ou objeto com atributo .G
            ano: ano para compor nome padrao do arquivo
            nome_arquivo: nome customizado (com ou sem .gexf)
        """
        grafo_nx = self._obter_grafo_nx(grafo)

        if nome_arquivo:
            nome = nome_arquivo if nome_arquivo.endswith(".gexf") else f"{nome_arquivo}.gexf"
        elif ano is not None:
            nome = f"chamber_graph_{ano}.gexf"
        else:
            nome = "chamber_graph.gexf"

        output_file = self.output_dir / nome
        nx.write_gexf(grafo_nx, output_file)
        return output_file

    def to_gexf(self, grafo: Any, caminho: Path | str) -> Path:
        """Alias util para exportar em um caminho explicito."""
        grafo_nx = self._obter_grafo_nx(grafo)
        output_file = Path(caminho)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        nx.write_gexf(grafo_nx, output_file)
        return output_file

    def from_gexf(self, caminho: Path | str) -> nx.Graph:
        """Importa um grafo a partir de arquivo GEXF."""
        caminho_gexf = Path(caminho)
        if not caminho_gexf.exists():
            raise FileNotFoundError(f"Arquivo GEXF nao encontrado: {caminho_gexf}")
        return nx.read_gexf(caminho_gexf)