from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = ("gene", "diplotype", "phenotype", "drug", "recommendation")


def parse_pgx_final_tsv(tsv_path: str | Path) -> pd.DataFrame:
    """
    Parse the toy PGx final TSV into a deterministic DataFrame.

    Contract expectations:
    - TSV has header row with required columns.
    - Parser output is deterministic (sorted, stable types).
    """
    path = Path(tsv_path)
    rows: list[dict] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            if r is None:
                continue
            row = {k: (r.get(k, "") or "").strip() for k in REQUIRED_COLUMNS}
            if any(row.values()):
                rows.append(row)

    df = pd.DataFrame(rows, columns=list(REQUIRED_COLUMNS))

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"PGx TSV missing required columns: {missing}")

    if df.empty:
        return df

    for c in REQUIRED_COLUMNS:
        df[c] = df[c].astype(str)

    df = df.sort_values(
        by=["gene", "drug", "diplotype", "phenotype", "recommendation"],
        kind="mergesort",
    ).reset_index(drop=True)
    return df

