from dataclasses import dataclass

@dataclass
class ArestaCoautoria:
    source_id: int
    target_id: int
    peso_bruto: int  # Número total de projetos assinados juntos
    forca_normalizada: float = 0.0 # O teu índice que penaliza partidos grandes