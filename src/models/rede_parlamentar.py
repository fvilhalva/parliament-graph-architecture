from dataclasses import dataclass
from typing import List, Dict
import networkx as nx

from models.deputado import Deputado

@dataclass
class RedeParlamentar:
    ano: int
    grafo: nx.Graph
    deputados: Dict[int, Deputado]
    
    def total_nos(self) -> int:
        return self.grafo.number_of_nodes()
        
    def total_arestas(self) -> int:
        return self.grafo.number_of_edges()