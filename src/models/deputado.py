from dataclasses import dataclass

@dataclass
class Deputado:
    id_deputado: int
    nome: str
    sigla_partido: str
    sigla_uf: str
    weighted_degree: float = 0.0
    degree_centrality: float = 0.0
    betweenness_centrality: float = 0.0