"""Contract tests for C10.B1: Data_Reference_URL_Quality_v3.

Validates:
1. PubMed_ID present → reference = https://pubmed.ncbi.nlm.nih.gov/<ID>/
2. PubMed_ID present → reference MUST NOT contain ?term=
3. PubMed_ID missing + rsid known → stable GWAS Catalog variant URL, not ?term=
4. No scenario produces a PubMed ?term= search URL.
"""

import os
import sys

import pandas as pd
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GWAS_PKG = os.path.join(PROJECT_ROOT, "gwas_variant_analyzer")

if GWAS_PKG not in sys.path:
    sys.path.insert(0, GWAS_PKG)

from gwas_variant_analyzer.customer_friendly_processor import (  # noqa: E402
    format_customer_friendly_results,
    get_confidence_level,
)


# ---------- Direct PubMed URL when PubMed_ID exists ----------


def test_pubmed_id_produces_direct_url():
    """PubMed_ID present → https://pubmed.ncbi.nlm.nih.gov/<ID>/"""
    result = get_confidence_level(1e-9, "29878757")
    assert result["reference"] == "https://pubmed.ncbi.nlm.nih.gov/29878757/"
    assert result["has_reference"] is True


def test_pubmed_id_float_produces_direct_url():
    """PubMed_ID as float (29878757.0) → same direct URL."""
    result = get_confidence_level(1e-9, 29878757.0)
    assert result["reference"] == "https://pubmed.ncbi.nlm.nih.gov/29878757/"


def test_pubmed_id_url_never_contains_term():
    """When PubMed_ID is present, reference MUST NOT contain ?term=."""
    result = get_confidence_level(1e-9, "12345678")
    assert "?term=" not in result["reference"]


# ---------- Fallback: GWAS Catalog stable URLs ----------


def test_missing_pubmed_rsid_uses_gwas_catalog_variant():
    """Missing PubMed_ID + rs* SNP → GWAS Catalog variant page."""
    result = get_confidence_level(1e-9, None, snp_id="rs12345")
    assert "ebi.ac.uk/gwas/variants/rs12345" in result["reference"]
    assert "?term=" not in result["reference"]
    assert result["has_reference"] is True


def test_missing_pubmed_association_id_uses_gwas_catalog_assoc():
    """Missing PubMed_ID + association_id → GWAS Catalog association page."""
    result = get_confidence_level(1e-9, None, association_id="A999")
    assert "ebi.ac.uk/gwas/associations/A999" in result["reference"]
    assert "?term=" not in result["reference"]


def test_missing_pubmed_no_rsid_no_assoc_uses_gwas_catalog():
    """Missing PubMed_ID + no rsid + no assoc_id → GWAS Catalog (not PubMed ?term=)."""
    result = get_confidence_level(1e-9, None, trait="obesity")
    assert "ebi.ac.uk/gwas/" in result["reference"]
    assert "?term=" not in result["reference"] or "pubmed" not in result["reference"].lower()


def test_no_scenario_produces_pubmed_term_search():
    """No input combination should produce pubmed.ncbi.nlm.nih.gov/?term=."""
    combos = [
        {"p_value": 1e-9, "pubmed_id": None},
        {"p_value": 1e-9, "pubmed_id": None, "association_id": None, "trait": "diabetes"},
        {"p_value": 1e-9, "pubmed_id": None, "snp_id": "chr1:12345"},
        {"p_value": 1e-9, "pubmed_id": "", "trait": "cancer", "snp_id": ""},
    ]
    for kwargs in combos:
        result = get_confidence_level(**kwargs)
        assert "pubmed.ncbi.nlm.nih.gov/?term=" not in result["reference"], (
            f"Got forbidden PubMed ?term= URL for kwargs={kwargs}: {result['reference']}"
        )


# ---------- Integration: format_customer_friendly_results ----------


def test_format_results_pubmed_urls_are_direct():
    """Formatted results with PubMed_ID must use direct URLs with trailing slash."""
    df = pd.DataFrame([
        {
            "SNP_ID": "rs123",
            "GWAS_Trait": "obesity",
            "Odds_Ratio": 1.5,
            "P_Value": 1e-9,
            "PubMed_ID": "55555555",
            "GWAS_Association_ID": "A888",
            "GWAS_CHROM": "1",
            "GWAS_POS": 100,
            "GWAS_ALT": "A",
        },
    ])
    result = format_customer_friendly_results(df)
    assert result["success"] is True
    for v in result["variants"]:
        assert v["reference"] == "https://pubmed.ncbi.nlm.nih.gov/55555555/"
        assert "?term=" not in v["reference"]


def test_format_results_missing_pubmed_uses_stable_url():
    """Formatted results without PubMed_ID must use stable GWAS Catalog URL."""
    df = pd.DataFrame([
        {
            "SNP_ID": "rs456",
            "GWAS_Trait": "diabetes",
            "Odds_Ratio": 2.0,
            "P_Value": 1e-10,
            "PubMed_ID": None,
            "GWAS_Association_ID": None,
            "GWAS_CHROM": "2",
            "GWAS_POS": 200,
            "GWAS_ALT": "G",
        },
    ])
    result = format_customer_friendly_results(df)
    assert result["success"] is True
    for v in result["variants"]:
        assert "ebi.ac.uk/gwas/" in v["reference"]
        assert "pubmed.ncbi.nlm.nih.gov/?term=" not in v["reference"]
