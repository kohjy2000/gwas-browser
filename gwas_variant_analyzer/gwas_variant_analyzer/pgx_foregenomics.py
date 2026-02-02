"""Parser for ForeGenomics PGx report TSV files.

Reads a ForeGenomics PGx report TSV and returns a normalized DataFrame
with columns: gene, drug, genotype, phenotype, recommendation, guideline_ids.
"""

from __future__ import annotations

import pandas as pd


def parse_foregenomics_report_tsv(path: str) -> pd.DataFrame:
    """Parse a ForeGenomics PGx report TSV into a normalized DataFrame.

    Parameters
    ----------
    path : str
        Path to the ForeGenomics ``*.PGx.out.report.tsv`` file.

    Returns
    -------
    pd.DataFrame
        Columns: gene, drug, genotype, phenotype, recommendation, guideline_ids.
        One row per (gene, drug) combination from the source file.
    """
    raw = pd.read_csv(path, sep="\t", dtype=str)

    # Normalize column names to lower-case for resilient lookup
    raw.columns = [c.strip() for c in raw.columns]

    # Build output with only the columns we need
    out_rows = []
    for _, row in raw.iterrows():
        gene = str(row.get("Gene", "") or "").strip()
        drug = str(row.get("Drug", "") or "").strip()
        genotype = str(row.get("Genotype", "") or "").strip()
        phenotype = str(row.get("Phenotype", "") or "").strip()
        recommendation = str(row.get("Recommendation", "") or "").strip()
        guideline_ids = str(row.get("PharmGKB_Guideline_IDs", "") or "").strip()

        # Replace '.' sentinel with empty string
        if gene == ".":
            gene = ""
        if genotype == ".":
            genotype = ""
        if phenotype == ".":
            phenotype = ""
        if recommendation == ".":
            recommendation = ""
        if guideline_ids == ".":
            guideline_ids = ""

        out_rows.append({
            "gene": gene,
            "drug": drug,
            "genotype": genotype,
            "phenotype": phenotype,
            "recommendation": recommendation,
            "guideline_ids": guideline_ids,
        })

    df = pd.DataFrame(out_rows)
    return df
