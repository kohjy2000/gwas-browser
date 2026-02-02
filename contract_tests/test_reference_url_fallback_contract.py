"""Contract tests for Data_Reference_URL_Fallback_v2.

Validates that customer-friendly variant outputs use URL references
and never emit the literal 'No publication reference available' string.
"""

import os
import sys

import pandas as pd


def _import_processor():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    gwas_pkg_parent = os.path.join(project_root, "gwas_variant_analyzer")
    if gwas_pkg_parent not in sys.path:
        sys.path.insert(0, gwas_pkg_parent)

    from gwas_variant_analyzer.customer_friendly_processor import (  # noqa: E402
        format_customer_friendly_results,
        get_confidence_level,
    )
    return format_customer_friendly_results, get_confidence_level


def test_pubmed_id_produces_pubmed_url():
    _, get_confidence_level = _import_processor()
    result = get_confidence_level(1e-9, "12345678")
    assert result["reference"].startswith("https://pubmed.ncbi.nlm.nih.gov/")
    assert "12345678" in result["reference"]
    assert result["has_reference"] is True


def test_missing_pubmed_with_association_id_produces_gwas_url():
    _, get_confidence_level = _import_processor()
    result = get_confidence_level(1e-9, None, association_id="A123")
    assert "https://www.ebi.ac.uk/gwas/" in result["reference"]
    assert "A123" in result["reference"]
    assert result["has_reference"] is True


def test_missing_pubmed_and_association_id_still_produces_url():
    _, get_confidence_level = _import_processor()
    result = get_confidence_level(1e-9, None, association_id=None)
    assert result["reference"].startswith("https://")
    assert result["has_reference"] is True


def test_no_publication_reference_available_never_appears():
    """The literal 'No publication reference available' must never appear."""
    _, get_confidence_level = _import_processor()
    # All possible missing-pubmed scenarios
    for pubmed in [None, "", float("nan")]:
        for assoc in [None, "", "A1"]:
            result = get_confidence_level(0.01, pubmed, association_id=assoc)
            assert "No publication reference available" not in result["reference"], (
                f"Got forbidden string for pubmed={pubmed!r}, assoc={assoc!r}"
            )


def test_format_results_references_are_urls():
    format_customer_friendly_results, _ = _import_processor()
    df = pd.DataFrame([
        {
            "SNP_ID": "rs123",
            "GWAS_Trait": "test trait",
            "Odds_Ratio": 1.5,
            "P_Value": 1e-9,
            "PubMed_ID": None,
            "GWAS_Association_ID": "A999",
            "GWAS_CHROM": "1",
            "GWAS_POS": 100,
            "GWAS_ALT": "A",
        },
        {
            "SNP_ID": "rs456",
            "GWAS_Trait": "test trait",
            "Odds_Ratio": 2.0,
            "P_Value": 1e-10,
            "PubMed_ID": "55555555",
            "GWAS_Association_ID": "A888",
            "GWAS_CHROM": "2",
            "GWAS_POS": 200,
            "GWAS_ALT": "G",
        },
    ])
    result = format_customer_friendly_results(df)
    assert result["success"] is True
    for v in result["variants"]:
        assert v["reference"].startswith("https://"), (
            f"Reference must be a URL, got: {v['reference']}"
        )
        assert "No publication reference available" not in v["reference"]
