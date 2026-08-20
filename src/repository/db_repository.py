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
)


class DB_Exporter:
    """Repository for persisting deputy metrics into SQLite."""

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_metrics_table(self, conn: sqlite3.Connection) -> None:
        """Create the metrics table if missing, then apply idempotent migrations.

        Legacy databases created before the closeness/eigenvector/community
        columns existed are migrated in place via ``ALTER TABLE ADD COLUMN``.
        Each ``ALTER`` is guarded by inspecting ``PRAGMA table_info`` so repeated
        calls are safe (SQLite has no ``ADD COLUMN IF NOT EXISTS``).
        """
        metrics_ddl = ",\n            ".join(
            f"{name} {ddl}" for name, ddl in _METRIC_COLUMNS
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS deputados_metricas (
                year INTEGER NOT NULL,
                deputy_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                party_code TEXT,
                state_code TEXT,
                {metrics_ddl},
                PRIMARY KEY (year, deputy_id)
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

    def export_deputy_metrics(self, deputies: list, year: int) -> Path:
        """Insert or update deputy metrics for a given year (upsert)."""
        records = []
        for deputy in deputies:
            dep = asdict(deputy)
            records.append(
                (
                    year,
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
                )
            )

        with self._connect() as conn:
            self._ensure_metrics_table(conn)
            conn.executemany(
                """
                INSERT OR REPLACE INTO deputados_metricas (
                    year,
                    deputy_id,
                    name,
                    party_code,
                    state_code,
                    weighted_degree,
                    degree_centrality,
                    betweenness_centrality,
                    closeness_centrality,
                    eigenvector_centrality,
                    community_louvain
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                records,
            )
            conn.commit()

        return self.db_path
