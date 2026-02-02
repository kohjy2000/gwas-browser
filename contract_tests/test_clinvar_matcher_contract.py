import os
import sys

import pandas as pd


def _import_matcher():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    gwas_pkg_parent = os.path.join(project_root, "gwas_variant_analyzer")
    if gwas_pkg_parent not in sys.path:
        sys.path.insert(0, gwas_pkg_parent)

    import gwas_variant_analyzer.clinvar_matcher as m  # noqa: E402

    return m, project_root


def test_clinvar_toy_tsv_schema_and_min_rows():
    _, project_root = _import_matcher()
    tsv_path = os.path.join(project_root, "data", "clinvar", "clinvar_toy.tsv")
    assert os.path.exists(tsv_path)

    df = pd.read_csv(tsv_path, sep="\t", dtype=str)
    required = {
        "chrom",
        "pos",
        "ref",
        "alt",
        "clinical_significance",
        "condition",
        "gene",
        "variation_id",
        "rsid",
    }
    assert required.issubset(set(df.columns))
    assert len(df) >= 3


def test_clinvar_matcher_primary_and_rsid_and_default_filter_and_determinism():
    m, project_root = _import_matcher()
    tsv_path = os.path.join(project_root, "data", "clinvar", "clinvar_toy.tsv")

    user_df = pd.DataFrame(
        [
            # No primary match -> rsid fallback expected (pathogenic/likely_pathogenic)
            {"USER_CHROM": "chr7", "USER_POS": 1, "USER_REF": "A", "USER_ALT": "C", "SNP_ID": "rs113993960"},
            # Primary match should win even if SNP_ID points elsewhere
            {"USER_CHROM": "chr1", "USER_POS": 1000, "USER_REF": "a", "USER_ALT": "g", "SNP_ID": "rs113993960"},
            # Benign primary match exists in TSV but should be filtered out by default
            {"USER_CHROM": "17", "USER_POS": 43071077, "USER_REF": "C", "USER_ALT": "T", "SNP_ID": "rs80357065"},
        ]
    )

    out1 = m.match_user_variants_to_clinvar(user_df, tsv_path)
    out2 = m.match_user_variants_to_clinvar(user_df.iloc[::-1].reset_index(drop=True), tsv_path)
    assert out1 == out2

    assert len(out1) == 2

    primary = next(x for x in out1 if x["match_type"] == "primary")
    assert primary["match_key"] == "1-1000-A-G"
    assert primary["user_chrom"] == "1"
    assert primary["user_pos"] == 1000
    assert primary["user_ref"] == "A"
    assert primary["user_alt"] == "G"
    assert primary["chrom"] == "1"
    assert str(primary["pos"]) == "1000"
    assert primary["ref"] == "A"
    assert primary["alt"] == "G"
    assert primary["clinical_significance"].lower() == "pathogenic"

    rsid = next(x for x in out1 if x["match_type"] == "rsid")
    assert rsid["user_chrom"] == "7"
    assert rsid["user_pos"] == 1
    assert rsid["rsid"].lower() == "rs113993960"
    assert rsid["clinical_significance"].lower() == "likely_pathogenic"

    assert all(x["clinical_significance"].lower() in {"pathogenic", "likely_pathogenic"} for x in out1)
