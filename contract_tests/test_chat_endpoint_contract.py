"""Contract tests for POST /api/chat (API_ChatCounseling_v1).

No network calls. All assertions are deterministic.
"""
from __future__ import annotations

import json
import sys
import os

import pytest

# ---------------------------------------------------------------------------
# Fixture: minimal Flask test client
# ---------------------------------------------------------------------------

# Ensure the gwas_dashboard_package/src is on sys.path so Flask app can be imported
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_src_path = os.path.join(_project_root, "gwas_dashboard_package", "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# Also ensure the gwas_variant_analyzer package is importable
_gva_path = os.path.join(_project_root, "gwas_variant_analyzer")
if _gva_path not in sys.path:
    sys.path.insert(0, _gva_path)


from flask import Flask
from routes.api import api_bp


@pytest.fixture()
def client():
    app = Flask(__name__)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

REQUIRED_KEYS = {"success", "answer", "disclaimer_tags", "citations", "risk_level"}

MINIMUM_DISCLAIMER_TAGS = {
    "not_medical_advice",
    "consult_professional",
    "research_only",
    "no_emergency_use",
}

VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}

SAMPLE_GWAS = [
    {"trait": "Type 2 diabetes", "variant": "rs123", "p_value": "1e-8", "pubmed_id": "12345"},
]

SAMPLE_CLINVAR = [
    {
        "user_chrom": "1", "user_pos": 100, "user_ref": "A", "user_alt": "G",
        "gene": "BRCA1", "clinical_significance": "Pathogenic",
        "condition": "Breast cancer", "variation_id": "99999",
    },
]

SAMPLE_PGX = {
    "total_rows": 1,
    "genes": ["CYP2D6"],
    "drugs": ["codeine"],
    "by_gene": [
        {
            "gene": "CYP2D6",
            "diplotypes": ["*1/*2"],
            "phenotypes": ["Normal Metabolizer"],
            "drugs": ["codeine"],
        }
    ],
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestChatEndpointContract:
    """API_ChatCounseling_v1 contract tests."""

    def test_missing_message_returns_400(self, client):
        resp = client.post("/api/chat", json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False

    def test_basic_response_has_required_keys(self, client):
        resp = client.post("/api/chat", json={
            "message": "Tell me about my risk",
            "gwas_associations": SAMPLE_GWAS,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert REQUIRED_KEYS.issubset(data.keys()), f"Missing keys: {REQUIRED_KEYS - data.keys()}"
        assert data["success"] is True

    def test_disclaimer_tags_always_present_and_nonempty(self, client):
        resp = client.post("/api/chat", json={"message": "hello"})
        data = resp.get_json()
        tags = data.get("disclaimer_tags")
        assert isinstance(tags, list)
        assert len(tags) > 0, "disclaimer_tags must be non-empty"

    def test_disclaimer_tags_contain_minimum_set(self, client):
        resp = client.post("/api/chat", json={"message": "hello"})
        data = resp.get_json()
        tags_set = set(data["disclaimer_tags"])
        assert MINIMUM_DISCLAIMER_TAGS.issubset(tags_set), (
            f"Missing minimum tags: {MINIMUM_DISCLAIMER_TAGS - tags_set}"
        )

    def test_risk_level_valid(self, client):
        resp = client.post("/api/chat", json={
            "message": "risk?",
            "gwas_associations": SAMPLE_GWAS,
        })
        data = resp.get_json()
        assert data["risk_level"] in VALID_RISK_LEVELS, (
            f"Invalid risk_level: {data['risk_level']}"
        )

    def test_citations_reference_known_fact_ids(self, client):
        """Citations must reference IDs that the facts model actually produces."""
        from gwas_variant_analyzer.chat_facts import collect_facts, get_fact_ids

        facts = collect_facts(
            gwas_associations=SAMPLE_GWAS,
            clinvar_matches=SAMPLE_CLINVAR,
            pgx_summary=SAMPLE_PGX,
        )
        known_ids = set(get_fact_ids(facts))

        resp = client.post("/api/chat", json={
            "message": "What are my results?",
            "gwas_associations": SAMPLE_GWAS,
            "clinvar_matches": SAMPLE_CLINVAR,
            "pgx_summary": SAMPLE_PGX,
        })
        data = resp.get_json()
        citations = data.get("citations", [])
        assert isinstance(citations, list)
        for cid in citations:
            assert cid in known_ids, f"Citation '{cid}' not in known fact IDs"

    def test_deterministic_output(self, client):
        """Two identical requests must produce identical responses."""
        payload = {
            "message": "determinism check",
            "gwas_associations": SAMPLE_GWAS,
            "clinvar_matches": SAMPLE_CLINVAR,
            "pgx_summary": SAMPLE_PGX,
        }
        resp1 = client.post("/api/chat", json=payload)
        resp2 = client.post("/api/chat", json=payload)
        assert resp1.get_json() == resp2.get_json()

    def test_no_facts_still_returns_valid_contract(self, client):
        """Even with no context data, the contract shape must hold."""
        resp = client.post("/api/chat", json={"message": "hello with no data"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert REQUIRED_KEYS.issubset(data.keys())
        assert data["success"] is True
        assert isinstance(data["disclaimer_tags"], list)
        assert len(data["disclaimer_tags"]) > 0
        assert data["risk_level"] in VALID_RISK_LEVELS
        assert isinstance(data["citations"], list)

    def test_risk_level_escalates_with_clinvar_and_pgx(self, client):
        """When both clinvar and pgx facts are present, risk should be high."""
        resp = client.post("/api/chat", json={
            "message": "full context",
            "clinvar_matches": SAMPLE_CLINVAR,
            "pgx_summary": SAMPLE_PGX,
        })
        data = resp.get_json()
        assert data["risk_level"] == "high"
