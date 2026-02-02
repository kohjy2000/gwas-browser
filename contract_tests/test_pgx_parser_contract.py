import os
import sys

import pandas as pd


def _import_pgx():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    gwas_pkg_parent = os.path.join(project_root, "gwas_variant_analyzer")
    if gwas_pkg_parent not in sys.path:
        sys.path.insert(0, gwas_pkg_parent)

    from gwas_variant_analyzer.pgx_parser import parse_pgx_final_tsv  # noqa: E402
    from gwas_variant_analyzer.pgx_summary import summarize_pgx  # noqa: E402

    return parse_pgx_final_tsv, summarize_pgx, project_root


def test_pgx_final_tsv_schema_and_min_rows():
    _, _, project_root = _import_pgx()
    tsv_path = os.path.join(project_root, "data", "pgx", "final.tsv")
    assert os.path.exists(tsv_path)

    df = pd.read_csv(tsv_path, sep="\t", dtype=str)
    required = {"gene", "diplotype", "phenotype", "drug", "recommendation"}
    assert required.issubset(set(df.columns))
    assert len(df) >= 1


def test_pgx_parser_and_summary_are_deterministic():
    parse_pgx_final_tsv, summarize_pgx, project_root = _import_pgx()
    tsv_path = os.path.join(project_root, "data", "pgx", "final.tsv")

    df1 = parse_pgx_final_tsv(tsv_path)
    df2 = parse_pgx_final_tsv(tsv_path)
    assert df1.to_dict(orient="records") == df2.to_dict(orient="records")

    assert not df1.empty
    assert list(df1.columns) == ["gene", "diplotype", "phenotype", "drug", "recommendation"]

    summary1 = summarize_pgx(df1)
    summary2 = summarize_pgx(df1)
    assert summary1 == summary2

    assert summary1["total_rows"] == len(df1)
    assert summary1["genes"] == sorted(summary1["genes"])
    assert summary1["drugs"] == sorted(summary1["drugs"])
