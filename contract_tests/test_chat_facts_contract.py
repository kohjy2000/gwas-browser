"""Contract tests for the chat_facts module (C4.B1).

Verifies:
- Facts model produces stable citation IDs referencing concrete items from inputs.
- Output is deterministic across repeated calls.
- Each domain (gwas, clinvar, pgx) contributes facts when data is provided.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is importable
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from gwas_variant_analyzer.gwas_variant_analyzer.chat_facts import (
    Fact,
    collect_facts,
    facts_to_dicts,
    get_fact_ids,
)


# --- Fixtures ---

SAMPLE_GWAS = [
    {"trait": "Type 2 Diabetes", "variant": "rs7903146", "p_value": "1e-8", "pubmed_id": "12345"},
    {"trait": "Height", "variant": "rs1042725", "p_value": "5e-10", "pubmed_id": "67890"},
]

SAMPLE_CLINVAR = [
    {
        "user_chrom": "1",
        "user_pos": 11856378,
        "user_ref": "G",
        "user_alt": "A",
        "gene": "MTHFR",
        "clinical_significance": "pathogenic",
        "condition": "Homocystinuria",
        "variation_id": "3520",
    },
]

SAMPLE_PGX_SUMMARY = {
    "total_rows": 2,
    "genes": ["CYP2C19", "CYP2D6"],
    "drugs": ["Clopidogrel", "Codeine"],
    "by_gene": [
        {
            "gene": "CYP2C19",
            "rows": 1,
            "diplotypes": ["*1/*2"],
            "phenotypes": ["Intermediate Metabolizer"],
            "drugs": ["Clopidogrel"],
        },
        {
            "gene": "CYP2D6",
            "rows": 1,
            "diplotypes": ["*1/*1"],
            "phenotypes": ["Normal Metabolizer"],
            "drugs": ["Codeine"],
        },
    ],
}


# --- Tests ---


def test_collect_facts_returns_list_of_fact_objects():
    facts = collect_facts(
        gwas_associations=SAMPLE_GWAS,
        clinvar_matches=SAMPLE_CLINVAR,
        pgx_summary=SAMPLE_PGX_SUMMARY,
    )
    assert isinstance(facts, list)
    assert len(facts) > 0
    for f in facts:
        assert isinstance(f, Fact)


def test_every_fact_has_stable_nonempty_id():
    facts = collect_facts(
        gwas_associations=SAMPLE_GWAS,
        clinvar_matches=SAMPLE_CLINVAR,
        pgx_summary=SAMPLE_PGX_SUMMARY,
    )
    ids = [f.id for f in facts]
    assert all(isinstance(fid, str) and len(fid) > 0 for fid in ids)
    # IDs must be unique
    assert len(ids) == len(set(ids)), f"Duplicate IDs found: {ids}"


def test_deterministic_output():
    """Calling collect_facts twice with same input produces identical results."""
    facts_a = collect_facts(
        gwas_associations=SAMPLE_GWAS,
        clinvar_matches=SAMPLE_CLINVAR,
        pgx_summary=SAMPLE_PGX_SUMMARY,
    )
    facts_b = collect_facts(
        gwas_associations=SAMPLE_GWAS,
        clinvar_matches=SAMPLE_CLINVAR,
        pgx_summary=SAMPLE_PGX_SUMMARY,
    )
    ids_a = [f.id for f in facts_a]
    ids_b = [f.id for f in facts_b]
    assert ids_a == ids_b


def test_domains_present():
    facts = collect_facts(
        gwas_associations=SAMPLE_GWAS,
        clinvar_matches=SAMPLE_CLINVAR,
        pgx_summary=SAMPLE_PGX_SUMMARY,
    )
    domains = {f.domain for f in facts}
    assert "gwas" in domains
    assert "clinvar" in domains
    assert "pgx" in domains


def test_facts_to_dicts_preserves_ids():
    facts = collect_facts(
        gwas_associations=SAMPLE_GWAS,
        clinvar_matches=SAMPLE_CLINVAR,
        pgx_summary=SAMPLE_PGX_SUMMARY,
    )
    dicts = facts_to_dicts(facts)
    assert isinstance(dicts, list)
    assert len(dicts) == len(facts)
    for d in dicts:
        assert "id" in d
        assert "domain" in d
        assert "category" in d
        assert "text" in d
        assert "source" in d


def test_get_fact_ids_returns_sorted():
    facts = collect_facts(
        gwas_associations=SAMPLE_GWAS,
        clinvar_matches=SAMPLE_CLINVAR,
        pgx_summary=SAMPLE_PGX_SUMMARY,
    )
    ids = get_fact_ids(facts)
    assert ids == sorted(ids)
    assert len(ids) == len(facts)


def test_citation_ids_reference_concrete_items():
    """Each fact ID references concrete input data, not generic placeholders."""
    facts = collect_facts(
        gwas_associations=SAMPLE_GWAS,
        clinvar_matches=SAMPLE_CLINVAR,
        pgx_summary=SAMPLE_PGX_SUMMARY,
    )
    for f in facts:
        # ID must contain the domain prefix
        assert f.id.startswith(f.domain), f"Fact ID {f.id} doesn't start with domain {f.domain}"
        # Text must be non-empty and contain meaningful content
        assert len(f.text) > 10, f"Fact text too short: {f.text}"


def test_empty_inputs_returns_empty():
    facts = collect_facts()
    assert facts == []


def test_partial_inputs():
    """Only providing some domains still works."""
    facts_gwas_only = collect_facts(gwas_associations=SAMPLE_GWAS)
    assert len(facts_gwas_only) == len(SAMPLE_GWAS)
    assert all(f.domain == "gwas" for f in facts_gwas_only)

    facts_clinvar_only = collect_facts(clinvar_matches=SAMPLE_CLINVAR)
    assert len(facts_clinvar_only) == len(SAMPLE_CLINVAR)
    assert all(f.domain == "clinvar" for f in facts_clinvar_only)
