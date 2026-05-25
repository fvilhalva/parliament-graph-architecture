"""GEXF graph export/import for downstream tools (e.g., Gephi)."""
from pathlib import Path
from typing import Any

import networkx as nx


class GraphExporter:
    """Exports and imports graphs in the GEXF format used by Gephi."""

    def __init__(self, output_dir: Path | str) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_nx_graph(self, graph: Any) -> nx.Graph:
        """Return an ``nx.Graph`` from either a NetworkX graph or an application wrapper."""
        if isinstance(graph, nx.Graph):
            return graph

        # Backwards-compatible: accept attribute names `G` (legacy) or `graph` (current dataclass).
        if hasattr(graph, "G") and isinstance(graph.G, nx.Graph):
            return graph.G

        if hasattr(graph, "graph") and isinstance(graph.graph, nx.Graph):
            return graph.graph

        raise TypeError("'graph' must be an nx.Graph or expose a `.graph`/`.G` nx.Graph attribute")

    def export_gexf(
        self,
        graph: Any,
        year: int | None = None,
        file_name: str | None = None,
    ) -> Path:
        """Export the graph to GEXF.

        Args:
            graph: ``nx.Graph`` or object with a ``.graph``/``.G`` attribute.
            year: Year used to compose the default file name.
            file_name: Custom file name (with or without the ``.gexf`` suffix).

        Returns:
            Path to the generated GEXF file.
        """
        nx_graph = self._get_nx_graph(graph)

        if file_name:
            name = file_name if file_name.endswith(".gexf") else f"{file_name}.gexf"
        elif year is not None:
            name = f"chamber_graph_{year}.gexf"
        else:
            name = "chamber_graph.gexf"

        output_file = self.output_dir / name
        nx.write_gexf(nx_graph, output_file)
        return output_file

    def to_gexf(self, graph: Any, path: Path | str) -> Path:
        """Export to an explicit destination path."""
        nx_graph = self._get_nx_graph(graph)
        output_file = Path(path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        nx.write_gexf(nx_graph, output_file)
        return output_file

    def from_gexf(self, path: Path | str) -> nx.Graph:
        """Read a graph from a GEXF file."""
        gexf_path = Path(path)
        if not gexf_path.exists():
            raise FileNotFoundError(f"GEXF file not found: {gexf_path}")
        return nx.read_gexf(gexf_path)

    # --- Backwards-compatible alias (kept for one release) ---
    def exportar_gexf(
        self,
        grafo: Any,
        ano: int | None = None,
        nome_arquivo: str | None = None,
    ) -> Path:
        """Deprecated alias for :meth:`export_gexf`."""
        return self.export_gexf(grafo, year=ano, file_name=nome_arquivo)
