from dataclasses import dataclass
from typing import List

@dataclass
class Proposicao:
    id_proposicao: int
    ano: int
    # ementa: str
    autores_ids: List[int] # Lista de IDs dos deputados que assinaram