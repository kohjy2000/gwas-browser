"""Contract tests for Data_PGx_ForeGenomics_Report_v1 and Func_PGx_ForeGenomics_Parser_v1.

Validates:
1. Snapshot TSV exists and has required columns (Sample, Drug, Gene, Genotype, Phenotype, Recommendation).
2. Snapshot has >= 10 unique Drug values.
3. Parser returns normalized DataFrame with gene, drug, genotype, phenotype, recommendation, guideline_ids.
4. Parsed output is deterministic.
"""

import os
import sys

import pandas as pd
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SNAPSHOT_PATH = os.path.join(PROJECT_ROOT, "data", "pgx", "foregenomics_report.tsv")


def _import_parser():
    gwas_pkg_parent = os.path.join(PROJECT_ROOT, "gwas_variant_analyzer")
    if gwas_pkg_parent not in sys.path:
        sys.path.insert(0, gwas_pkg_parent)

    from gwas_variant_analyzer.pgx_foregenomics import parse_foregenomics_report_tsv  # noqa: E402
    return parse_foregenomics_report_tsv


# ---------- Data file contract ----------


def test_snapshot_exists():
    """Snapshot TSV must exist at data/pgx/foregenomics_report.tsv."""
    assert os.path.isfile(SNAPSHOT_PATH), f"Snapshot not found at {SNAPSHOT_PATH}"


def test_snapshot_has_required_columns():
    """Snapshot must include Sample, Drug, Gene, Genotype, Phenotype, Recommendation columns."""
    df = pd.read_csv(SNAPSHOT_PATH, sep="\t", nrows=5)
    required = {"Sample", "Drug", "Gene", "Genotype", "Phenotype", "Recommendation"}
    missing = required - set(df.columns)
    assert not missing, f"Missing columns in snapshot: {missing}"


def test_snapshot_has_at_least_10_unique_drugs():
    """Snapshot must contain >= 10 unique Drug values."""
    df = pd.read_csv(SNAPSHOT_PATH, sep="\t", usecols=["Drug"])
    unique_drugs = df["Drug"].dropna().nunique()
    assert unique_drugs >= 10, f"Expected >= 10 unique drugs, got {unique_drugs}"


# ---------- Parser contract ----------


def test_parser_returns_required_columns():
    """Parser output must have gene, drug, genotype, phenotype, recommendation, guideline_ids."""
    parse = _import_parser()
    df = parse(SNAPSHOT_PATH)
    required = {"gene", "drug", "genotype", "phenotype", "recommendation", "guideline_ids"}
    missing = required - set(df.columns)
    assert not missing, f"Missing columns in parser output: {missing}"


def test_parser_returns_nonempty_dataframe():
    """Parser must return a non-empty DataFrame from the snapshot."""
    parse = _import_parser()
    df = parse(SNAPSHOT_PATH)
    assert not df.empty, "Parser returned empty DataFrame"
    assert len(df) >= 10, f"Expected >= 10 rows, got {len(df)}"


def test_parser_has_many_unique_drugs():
    """Parsed output must expose >= 10 unique drug values."""
    parse = _import_parser()
    df = parse(SNAPSHOT_PATH)
    unique_drugs = df["drug"].dropna().nunique()
    assert unique_drugs >= 10, f"Expected >= 10 unique drugs in parsed output, got {unique_drugs}"


def test_parser_deterministic():
    """Two calls to the parser must produce identical results."""
    parse = _import_parser()
    df1 = parse(SNAPSHOT_PATH)
    df2 = parse(SNAPSHOT_PATH)
    pd.testing.assert_frame_equal(df1, df2)


def test_parser_normalizes_dot_sentinel():
    """Dot sentinels ('.' values) should be normalized to empty strings."""
    parse = _import_parser()
    df = parse(SNAPSHOT_PATH)
    # Some rows in the snapshot have '.' for Gene or Recommendation
    for col in ["gene", "phenotype", "recommendation"]:
        dot_count = (df[col] == ".").sum()
        assert dot_count == 0, (
            f"Column '{col}' still contains {dot_count} dot sentinels; "
            "they should be normalized to empty strings"
        )
