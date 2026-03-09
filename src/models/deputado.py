from dataclasses import dataclass

@dataclass
class Deputado:
    id_deputado: int
    nome: str
    sigla_partido: str
    sigla_uf: str
    degree_centrality: float = 0.0
    betweenness_centrality: float = 0.0