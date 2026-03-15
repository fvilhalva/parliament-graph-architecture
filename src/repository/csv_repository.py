from pathlib import Path
from dataclasses import asdict
import pandas as pd  # type: ignore

class CsvRepository:
    def __init__(self, output_dir: Path | str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def exportar_metricas_deputados(self, deputados: list, ano: int) -> Path:
        registros = []

        for deputado in deputados:
            dep_dict = asdict(deputado)
            registros.append(
                {
                    "id_deputado": dep_dict.get("id_deputado"),
                    "nome": dep_dict.get("nome"),
                    "sigla_partido": dep_dict.get("sigla_partido"),
                    "sigla_uf": dep_dict.get("sigla_uf"),
                    "weighted_degree": dep_dict.get("weighted_degree", 0.0),
                    "degree_centrality": dep_dict.get("degree_centrality", 0.0),
                    "betweenness_centrality": dep_dict.get("betweenness_centrality", 0.0),
                }
            )

        df = pd.DataFrame(registros)
        df = df.sort_values(
            by=["degree_centrality", "betweenness_centrality"],
            ascending=False,
        )

        output_file = self.output_dir / f"deputados_metricas_{ano}.csv"
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        return output_file
    
    def exportar_metricas_coautorias(self, coautorias: list):
        pass 