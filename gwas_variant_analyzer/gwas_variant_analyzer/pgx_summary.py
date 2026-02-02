from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = ("gene", "diplotype", "phenotype", "drug", "recommendation")


def summarize_pgx(df: pd.DataFrame) -> dict:
    """
    Create a deterministic summary of parsed PGx recommendations.
    """
    if df is None or df.empty:
        return {
            "total_rows": 0,
            "genes": [],
            "drugs": [],
            "by_gene": [],
        }

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"PGx DataFrame missing required columns: {missing}")

    df2 = df.copy()
    for c in REQUIRED_COLUMNS:
        df2[c] = df2[c].astype(str)

    genes = sorted(set(df2["gene"].tolist()))
    drugs = sorted(set(df2["drug"].tolist()))

    by_gene: list[dict] = []
    for gene in genes:
        sub = df2[df2["gene"] == gene]
        by_gene.append(
            {
                "gene": gene,
                "rows": int(len(sub)),
                "diplotypes": sorted(set(sub["diplotype"].tolist())),
                "phenotypes": sorted(set(sub["phenotype"].tolist())),
                "drugs": sorted(set(sub["drug"].tolist())),
            }
        )

    by_gene = sorted(by_gene, key=lambda x: x["gene"])

    return {
        "total_rows": int(len(df2)),
        "genes": genes,
        "drugs": drugs,
        "by_gene": by_gene,
    }

