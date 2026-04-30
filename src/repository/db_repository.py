from dataclasses import asdict
from pathlib import Path
import sqlite3


class DB_Exporter:
    """Repositorio para persistencia de metricas em SQLite."""

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _garantir_tabela_metricas(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS deputados_metricas (
                ano INTEGER NOT NULL,
                id_deputado INTEGER NOT NULL,
                nome TEXT NOT NULL,
                sigla_partido TEXT,
                sigla_uf TEXT,
                weighted_degree REAL NOT NULL DEFAULT 0,
                degree_centrality REAL NOT NULL DEFAULT 0,
                betweenness_centrality REAL NOT NULL DEFAULT 0,
                PRIMARY KEY (ano, id_deputado)
            )
            """
        )

    def exportar_metricas_deputados(self, deputados: list, ano: int) -> Path:
        """Insere ou atualiza metricas dos deputados para um ano."""
        registros = []
        for deputado in deputados:
            dep = asdict(deputado)
            registros.append(
                (
                    ano,
                    dep.get("id"),
                    dep.get("name"),
                    dep.get("party_code"),
                    dep.get("state_code"),
                    dep.get("weighted_degree", 0.0),
                    dep.get("degree_centrality", 0.0),
                    dep.get("betweenness_centrality", 0.0),
                )
            )

        with self._connect() as conn:
            self._garantir_tabela_metricas(conn)
            conn.executemany(
                """
                INSERT OR REPLACE INTO deputados_metricas (
                    ano,
                    id_deputado,
                    nome,
                    sigla_partido,
                    sigla_uf,
                    weighted_degree,
                    degree_centrality,
                    betweenness_centrality
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                registros,
            )
            conn.commit()

        return self.db_path