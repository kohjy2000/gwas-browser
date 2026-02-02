"""Contract tests for C10.B3: API_Chat_TraitRisk_Guard_v1.

Validates:
1. When only PGx facts exist and user asks a trait question, risk_level="low".
2. suggested_actions includes analyze_trait for the detected trait.
3. Answer includes guidance to run GWAS analysis first.
4. When GWAS facts ARE present, risk_level may be medium/high (no guard).
"""

import json
import os
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DASH_SRC = os.path.join(PROJECT_ROOT, "gwas_dashboard_package", "src")
GWAS_PKG = os.path.join(PROJECT_ROOT, "gwas_variant_analyzer")

for p in (DASH_SRC, GWAS_PKG):
    if p not in sys.path:
        sys.path.insert(0, p)

from flask import Flask  # noqa: E402
from routes.api import api_bp, UPLOADS  # noqa: E402


@pytest.fixture()
def app():
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.register_blueprint(api_bp, url_prefix="/api")
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def _clean_uploads():
    UPLOADS.clear()
    yield
    UPLOADS.clear()


# ---------- Guard: PGx-only + trait question → risk_level="low" ----------


def test_pgx_only_trait_question_risk_is_low(client):
    """With PGx facts only, asking about obesity → risk_level='low'."""
    resp = client.post(
        "/api/chat",
        data=json.dumps({
            "message": "What is my obesity risk?",
            "pgx_summary": {
                "total_rows": 5,
                "genes": ["CYP2D6"],
                "drugs": ["codeine"],
                "by_gene": [{"gene": "CYP2D6", "rows": 5, "drugs": ["codeine"]}],
            },
        }),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["risk_level"] == "low", (
        f"Expected risk_level='low' with PGx-only facts, got '{body['risk_level']}'"
    )


def test_pgx_only_trait_question_has_suggested_action(client):
    """With PGx facts only, asking about obesity → suggested_actions includes analyze_trait."""
    resp = client.post(
        "/api/chat",
        data=json.dumps({
            "message": "What is my obesity risk?",
            "pgx_summary": {
                "total_rows": 5,
                "genes": ["CYP2D6"],
                "drugs": ["codeine"],
                "by_gene": [],
            },
        }),
        content_type="application/json",
    )
    body = resp.get_json()
    actions = body.get("suggested_actions", [])
    assert len(actions) > 0, "Expected suggested_actions with analyze_trait"
    assert actions[0]["type"] == "analyze_trait"


def test_pgx_only_trait_question_answer_contains_guidance(client):
    """With PGx-only facts, answer should instruct user to run GWAS analysis."""
    resp = client.post(
        "/api/chat",
        data=json.dumps({
            "message": "What is my obesity risk?",
            "pgx_summary": {
                "total_rows": 5,
                "genes": ["CYP2D6"],
                "drugs": ["codeine"],
                "by_gene": [],
            },
        }),
        content_type="application/json",
    )
    body = resp.get_json()
    answer = body.get("answer", "").lower()
    assert "gwas" in answer or "analysis" in answer, (
        f"Answer should mention GWAS or analysis: {body['answer'][:200]}"
    )


def test_pgx_only_no_trait_keeps_original_risk(client):
    """With PGx facts but no trait in message, risk_level follows normal logic."""
    resp = client.post(
        "/api/chat",
        data=json.dumps({
            "message": "hello",
            "pgx_summary": {
                "total_rows": 5,
                "genes": ["CYP2D6"],
                "drugs": ["codeine"],
                "by_gene": [{"gene": "CYP2D6", "rows": 5, "diplotypes": ["*1/*2"], "phenotypes": ["Intermediate Metabolizer"], "drugs": ["codeine"]}],
            },
        }),
        content_type="application/json",
    )
    body = resp.get_json()
    # No trait detected → guard not triggered → normal risk assessment
    assert body["risk_level"] == "medium", (
        f"Expected risk_level='medium' for PGx-only without trait question, got '{body['risk_level']}'"
    )


# ---------- GWAS facts present → no guard ----------


def test_gwas_facts_allow_normal_risk(client):
    """With GWAS facts present, trait question → normal risk_level (not forced low)."""
    resp = client.post(
        "/api/chat",
        data=json.dumps({
            "message": "What is my obesity risk?",
            "gwas_associations": [
                {"trait": "Obesity", "variant": "rs1234", "p_value": "1e-9", "pubmed_id": "12345"},
            ],
            "pgx_summary": {
                "total_rows": 5,
                "genes": ["CYP2D6"],
                "drugs": ["codeine"],
                "by_gene": [],
            },
        }),
        content_type="application/json",
    )
    body = resp.get_json()
    # GWAS + PGx → normal risk assessment applies (medium or higher)
    assert body["risk_level"] != "low" or body["suggested_actions"] == [], (
        "With GWAS facts, guard should not be active"
    )


def test_no_facts_trait_question_is_low(client):
    """With no facts at all and a trait question, risk_level should be 'low'."""
    resp = client.post(
        "/api/chat",
        data=json.dumps({"message": "What is my obesity risk?"}),
        content_type="application/json",
    )
    body = resp.get_json()
    assert body["risk_level"] == "low"
