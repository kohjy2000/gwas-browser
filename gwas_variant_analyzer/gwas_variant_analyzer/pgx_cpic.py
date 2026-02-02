"""Parser for CPIC toy PGx snapshot TSV files.

Reads a CPIC-like PGx snapshot TSV and returns a normalized DataFrame
with columns: gene, drug, diplotype, phenotype, recommendation, cpic_level, cpic_url.
"""

from __future__ import annotations

import pandas as pd


def parse_cpic_toy_tsv(path: str) -> pd.DataFrame:
    """Parse a CPIC toy snapshot TSV into a normalized DataFrame.

    Parameters
    ----------
    path : str
        Path to the ``cpic_toy.tsv`` file.

    Returns
    -------
    pd.DataFrame
        Columns: gene, drug, diplotype, phenotype, recommendation, cpic_level, cpic_url.
        One row per (gene, drug, diplotype) combination from the source file.
    """
    raw = pd.read_csv(path, sep="\t", dtype=str)

    raw.columns = [c.strip() for c in raw.columns]

    out_rows = []
    for _, row in raw.iterrows():
        gene = str(row.get("gene", "") or "").strip()
        drug = str(row.get("drug", "") or "").strip()
        diplotype = str(row.get("diplotype", "") or "").strip()
        phenotype = str(row.get("phenotype", "") or "").strip()
        recommendation = str(row.get("recommendation", "") or "").strip()
        cpic_level = str(row.get("cpic_level", "") or "").strip()
        cpic_url = str(row.get("cpic_url", "") or "").strip()

        for field_val in (gene, diplotype, phenotype, recommendation, cpic_level, cpic_url):
            pass  # no sentinel replacement needed; TSV uses real values

        out_rows.append({
            "gene": gene,
            "drug": drug,
            "diplotype": diplotype,
            "phenotype": phenotype,
            "recommendation": recommendation,
            "cpic_level": cpic_level,
            "cpic_url": cpic_url,
        })

    return pd.DataFrame(out_rows)
