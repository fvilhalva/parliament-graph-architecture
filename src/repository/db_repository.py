"""SQLite persistence for deputy metrics."""
from dataclasses import asdict
from pathlib import Path
import sqlite3


# Columns that must exist on the ``deputados_metricas`` table. Kept ordered so
# both the ``CREATE TABLE`` and the ``ALTER TABLE`` migration produce the same
# logical schema. Each entry is ``(column_name, sqlite_type_with_default)``.
_METRIC_COLUMNS: tuple[tuple[str, str], ...] = (
    ("weighted_degree", "REAL NOT NULL DEFAULT 0"),
    ("degree_centrality", "REAL NOT NULL DEFAULT 0"),
    ("betweenness_centrality", "REAL NOT NULL DEFAULT 0"),
    ("closeness_centrality", "REAL NOT NULL DEFAULT 0"),
    ("eigenvector_centrality", "REAL NOT NULL DEFAULT 0"),
    ("community_louvain", "INTEGER"),
    ("relatorship_count", "INTEGER NOT NULL DEFAULT 0"),
)


class DB_Exporter:
    """Repositorio para persistencia de metricas em SQLite."""

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _garantir_tabela_metricas(self, conn: sqlite3.Connection) -> None:
        """Create the metrics table if missing, then apply idempotent migrations.

        Legacy databases created before the closeness/eigenvector/community/
        relatorship columns existed are migrated in place via ``ALTER TABLE
        ADD COLUMN``. Each ``ALTER`` is guarded by inspecting ``PRAGMA
        table_info`` so repeated calls are safe (SQLite has no
        ``ADD COLUMN IF NOT EXISTS``).
        """
        metrics_ddl = ",\n            ".join(
            f"{name} {ddl}" for name, ddl in _METRIC_COLUMNS
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS deputados_metricas (
                ano INTEGER NOT NULL,
                id_deputado INTEGER NOT NULL,
                nome TEXT NOT NULL,
                sigla_partido TEXT,
                sigla_uf TEXT,
                {metrics_ddl},
                PRIMARY KEY (ano, id_deputado)
            )
            """
        )
        existing = {
            row[1] for row in conn.execute("PRAGMA table_info(deputados_metricas)")
        }
        for column_name, column_ddl in _METRIC_COLUMNS:
            if column_name not in existing:
                conn.execute(
                    f"ALTER TABLE deputados_metricas ADD COLUMN {column_name} {column_ddl}"
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
                    dep.get("closeness_centrality", 0.0),
                    dep.get("eigenvector_centrality", 0.0),
                    dep.get("community_louvain"),
                    dep.get("relatorship_count", 0),
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
                    betweenness_centrality,
                    closeness_centrality,
                    eigenvector_centrality,
                    community_louvain,
                    relatorship_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                registros,
            )
            conn.commit()

        return self.db_path
