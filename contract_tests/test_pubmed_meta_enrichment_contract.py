"""Contract tests for Func_PubMed_Meta_Enrichment_v2.

Validates that parse_gwas_association_data:
1. Prefers non-empty PubMed_ID when multiple records share the same (rsid, alt) key.
2. Normalizes PubMed_ID to a string integer (e.g. 29878757.0 → "29878757").
3. No network calls (monkeypatched Ensembl + study fetch).
"""

import os
import sys

import pytest


def _import_handler():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    gwas_pkg_parent = os.path.join(project_root, "gwas_variant_analyzer")
    if gwas_pkg_parent not in sys.path:
        sys.path.insert(0, gwas_pkg_parent)

    import gwas_variant_analyzer.gwas_catalog_handler as h  # noqa: E402
    return h


_CONFIG = {
    "gwas_api_request_timeout_seconds": 5,
    "gwas_api_max_retries": 1,
    "gwas_api_retry_delay_seconds": 0,
    "study_fetch_rate_limit_per_second": 1000,
}


def _patch_ensembl(monkeypatch, h, locations=None):
    """Monkeypatch Ensembl so no real HTTP calls are made."""
    if locations is None:
        locations = {"rs100": {"chrom": "7", "pos": 5000}}
    monkeypatch.setattr(
        h, "_fetch_snp_locations_from_ensembl",
        lambda rsids, config: locations,
    )


def _patch_study_fetch(monkeypatch, h, pmid="77777777"):
    """Monkeypatch requests.get used for study-link PubMed fill."""
    class _Resp:
        def raise_for_status(self):
            pass

        def json(self_inner):
            return {"publicationInfo": {"pubmedId": pmid}}

    monkeypatch.setattr(h.requests, "get", lambda *a, **kw: _Resp())


# ---------- tests ----------


def test_later_record_fills_empty_pubmed(monkeypatch):
    """If first record for (rsid, alt) lacks PubMed but a later one has it, PubMed_ID must be non-empty."""
    h = _import_handler()
    _patch_ensembl(monkeypatch, h)
    _patch_study_fetch(monkeypatch, h, pmid=None)  # study fetch also returns None

    raw = [
        # Record 1: no PubMed
        {
            "associationId": "A1",
            "publicationInfo": {"pubmedId": None},
            "_links": {"study": {"href": ""}},
            "pvalue": "1e-6",
            "orPerCopyNum": "1.1",
            "loci": [{"strongestRiskAlleles": [{"riskAlleleName": "rs100-G"}]}],
            "ancestries": {},
        },
        # Record 2: has PubMed
        {
            "associationId": "A2",
            "publicationInfo": {"pubmedId": "29878757"},
            "_links": {},
            "pvalue": "2e-8",
            "orPerCopyNum": "1.3",
            "loci": [{"strongestRiskAlleles": [{"riskAlleleName": "rs100-G"}]}],
            "ancestries": {},
        },
    ]

    df = h.parse_gwas_association_data(raw, "TestTrait", _CONFIG)
    assert not df.empty, "Should produce at least one row"

    pmid = str(df["PubMed_ID"].iloc[0])
    assert pmid and pmid not in ("", "None", "nan"), (
        f"PubMed_ID must be non-empty when a later record provides it, got: {pmid!r}"
    )


def test_pubmed_id_normalized_float_to_int_string(monkeypatch):
    """PubMed_ID like 29878757.0 must become '29878757'."""
    h = _import_handler()
    _patch_ensembl(monkeypatch, h)
    _patch_study_fetch(monkeypatch, h, pmid=None)

    raw = [
        {
            "associationId": "A1",
            "publicationInfo": {"pubmedId": 29878757.0},  # float
            "_links": {},
            "pvalue": "3e-9",
            "orPerCopyNum": "1.5",
            "loci": [{"strongestRiskAlleles": [{"riskAlleleName": "rs100-G"}]}],
            "ancestries": {},
        },
    ]

    df = h.parse_gwas_association_data(raw, "TestTrait", _CONFIG)
    assert not df.empty
    assert df["PubMed_ID"].iloc[0] == "29878757", (
        f"Expected '29878757', got {df['PubMed_ID'].iloc[0]!r}"
    )


def test_pubmed_id_normalized_string_int(monkeypatch):
    """PubMed_ID given as plain string '12345678' stays '12345678'."""
    h = _import_handler()
    _patch_ensembl(monkeypatch, h)
    _patch_study_fetch(monkeypatch, h, pmid=None)

    raw = [
        {
            "associationId": "A1",
            "publicationInfo": {"pubmedId": "12345678"},
            "_links": {},
            "pvalue": "1e-5",
            "orPerCopyNum": "0.9",
            "loci": [{"strongestRiskAlleles": [{"riskAlleleName": "rs100-G"}]}],
            "ancestries": {},
        },
    ]

    df = h.parse_gwas_association_data(raw, "TestTrait", _CONFIG)
    assert df["PubMed_ID"].iloc[0] == "12345678"


def test_pubmed_none_yields_empty_string(monkeypatch):
    """When no PubMed is available at all, PubMed_ID should be empty string."""
    h = _import_handler()
    _patch_ensembl(monkeypatch, h)
    _patch_study_fetch(monkeypatch, h, pmid=None)

    raw = [
        {
            "associationId": "A1",
            "publicationInfo": {"pubmedId": None},
            "_links": {"study": {"href": ""}},
            "pvalue": "1e-4",
            "orPerCopyNum": "1.0",
            "loci": [{"strongestRiskAlleles": [{"riskAlleleName": "rs100-G"}]}],
            "ancestries": {},
        },
    ]

    df = h.parse_gwas_association_data(raw, "TestTrait", _CONFIG)
    assert not df.empty
    pmid = str(df["PubMed_ID"].iloc[0])
    assert pmid == "", f"Expected empty string when no PubMed, got {pmid!r}"


def test_multiple_keys_each_gets_best_pubmed(monkeypatch):
    """Two different (rsid, alt) keys; each should carry its best PubMed_ID."""
    h = _import_handler()
    _patch_ensembl(monkeypatch, h, locations={
        "rs100": {"chrom": "7", "pos": 5000},
        "rs200": {"chrom": "12", "pos": 8000},
    })
    _patch_study_fetch(monkeypatch, h, pmid=None)

    raw = [
        # rs100-G: first record has no PubMed
        {
            "associationId": "A1",
            "publicationInfo": {"pubmedId": None},
            "_links": {"study": {"href": ""}},
            "pvalue": "1e-6",
            "orPerCopyNum": "1.1",
            "loci": [{"strongestRiskAlleles": [{"riskAlleleName": "rs100-G"}]}],
            "ancestries": {},
        },
        # rs100-G: second record has PubMed
        {
            "associationId": "A2",
            "publicationInfo": {"pubmedId": "11111111"},
            "_links": {},
            "pvalue": "2e-8",
            "orPerCopyNum": "1.3",
            "loci": [{"strongestRiskAlleles": [{"riskAlleleName": "rs100-G"}]}],
            "ancestries": {},
        },
        # rs200-T: only record, has PubMed
        {
            "associationId": "A3",
            "publicationInfo": {"pubmedId": "22222222"},
            "_links": {},
            "pvalue": "5e-10",
            "orPerCopyNum": "2.0",
            "loci": [{"strongestRiskAlleles": [{"riskAlleleName": "rs200-T"}]}],
            "ancestries": {},
        },
    ]

    df = h.parse_gwas_association_data(raw, "TestTrait", _CONFIG)
    assert len(df) == 2, f"Expected 2 rows, got {len(df)}"

    rs100_row = df[df["SNP_ID"] == "rs100"].iloc[0]
    rs200_row = df[df["SNP_ID"] == "rs200"].iloc[0]

    assert rs100_row["PubMed_ID"] == "11111111", (
        f"rs100 should have PubMed from second record, got {rs100_row['PubMed_ID']!r}"
    )
    assert rs200_row["PubMed_ID"] == "22222222", (
        f"rs200 should have PubMed from its only record, got {rs200_row['PubMed_ID']!r}"
    )
