"""Patch existing deputy metrics CSVs to replace NaN party/state codes.

Use this as a one-off cleanup after the sanitization fix in
``processing/data_cleaning.py`` — avoids re-running the entire pipeline
just to regenerate the CSVs.

Run from the project root:
    python scripts/fix_null_parties.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd  # type: ignore

BASE_DIR = Path(__file__).resolve().parent.parent
METRICS_DIR = BASE_DIR / "data" / "metricas"

PARTY_SENTINEL = "S/PARTIDO"
STATE_SENTINEL = "S/UF"


def patch_csv(path: Path) -> tuple[int, int]:
    """Replace NaN in sigla_partido and sigla_uf with sentinels.

    Returns:
        (n_party_fixed, n_state_fixed)
    """
    df = pd.read_csv(path)

    n_party = int(df["sigla_partido"].isna().sum()) if "sigla_partido" in df.columns else 0
    n_state = int(df["sigla_uf"].isna().sum()) if "sigla_uf" in df.columns else 0

    if "sigla_partido" in df.columns:
        df["sigla_partido"] = df["sigla_partido"].fillna(PARTY_SENTINEL)
        df["sigla_partido"] = df["sigla_partido"].astype(str).str.strip().replace("", PARTY_SENTINEL)

    if "sigla_uf" in df.columns:
        df["sigla_uf"] = df["sigla_uf"].fillna(STATE_SENTINEL)
        df["sigla_uf"] = df["sigla_uf"].astype(str).str.strip().replace("", STATE_SENTINEL)

    df.to_csv(path, index=False, encoding="utf-8-sig")
    return n_party, n_state


def main() -> None:
    if not METRICS_DIR.exists():
        print(f"Metrics directory not found: {METRICS_DIR}")
        return

    csv_files = sorted(METRICS_DIR.glob("deputados_metricas_*.csv"))
    if not csv_files:
        print(f"No deputy metrics CSVs found in {METRICS_DIR}")
        return

    print(f"Patching {len(csv_files)} CSV file(s)...\n")
    total_party = 0
    total_state = 0
    for path in csv_files:
        n_party, n_state = patch_csv(path)
        total_party += n_party
        total_state += n_state
        print(f"  {path.name}: {n_party} party + {n_state} state nulls patched")

    print(f"\nTotal: {total_party} party + {total_state} state nulls replaced.")
    print("Re-run dataset integrity tests to verify:")
    print("  docker compose run --rm tests pytest src/tests/test_dataset_integrity.py -v")


if __name__ == "__main__":
    main()
