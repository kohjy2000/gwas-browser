"""Contract tests for C9.B3: PGx Dataset Expansion — CPIC Snapshot Ingest.

Validates:
1. cpic_toy.tsv exists and has required columns.
2. parse_cpic_toy_tsv returns a DataFrame with expected columns and >= 30 unique drugs.
3. /api/pgx-summary with source="cpic" returns success with >= 30 unique drugs.
4. Disclaimer tags include cpic_data for source="cpic".
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

from gwas_variant_analyzer.pgx_cpic import parse_cpic_toy_tsv  # noqa: E402
from flask import Flask  # noqa: E402
from routes.api import api_bp  # noqa: E402

CPIC_TSV_PATH = os.path.join(PROJECT_ROOT, "data", "pgx", "cpic_toy.tsv")


@pytest.fixture()
def app():
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.register_blueprint(api_bp, url_prefix="/api")
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


# ---------- Data file contract ----------


def test_cpic_toy_tsv_exists():
    """cpic_toy.tsv must exist at the expected path."""
    assert os.path.exists(CPIC_TSV_PATH), f"cpic_toy.tsv not found at {CPIC_TSV_PATH}"


def test_cpic_toy_tsv_has_required_columns():
    """cpic_toy.tsv must have required columns."""
    df = parse_cpic_toy_tsv(CPIC_TSV_PATH)
    required = {"gene", "drug", "diplotype", "phenotype", "recommendation"}
    assert required.issubset(set(df.columns)), f"Missing columns: {required - set(df.columns)}"


def test_cpic_toy_tsv_has_enough_drugs():
    """cpic_toy.tsv must have >= 30 unique drugs."""
    df = parse_cpic_toy_tsv(CPIC_TSV_PATH)
    unique_drugs = df["drug"].dropna().loc[df["drug"] != ""].unique()
    assert len(unique_drugs) >= 30, f"Expected >= 30 unique drugs, got {len(unique_drugs)}"


# ---------- Parser contract ----------


def test_parse_cpic_returns_dataframe():
    """parse_cpic_toy_tsv returns a non-empty DataFrame."""
    df = parse_cpic_toy_tsv(CPIC_TSV_PATH)
    assert not df.empty
    assert len(df) > 0


# ---------- API endpoint contract ----------


def test_pgx_summary_cpic_source_returns_success(client):
    """/api/pgx-summary with source=cpic returns success."""
    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "cpic"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert "summary" in body
    assert "disclaimer_tags" in body


def test_pgx_summary_cpic_has_enough_drugs(client):
    """/api/pgx-summary with source=cpic returns >= 30 unique drugs."""
    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "cpic"}),
        content_type="application/json",
    )
    body = resp.get_json()
    drugs = body["summary"].get("drugs", [])
    assert len(drugs) >= 30, f"Expected >= 30 unique drugs, got {len(drugs)}"


def test_pgx_summary_cpic_disclaimer_tags(client):
    """Disclaimer tags must include cpic_data for source=cpic."""
    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "cpic"}),
        content_type="application/json",
    )
    body = resp.get_json()
    tags = body.get("disclaimer_tags", [])
    assert "cpic_data" in tags, f"Expected 'cpic_data' in disclaimer_tags, got {tags}"
    assert "not_medical_advice" in tags
    assert "consult_professional" in tags


def test_pgx_summary_cpic_has_by_gene(client):
    """CPIC summary must include by_gene breakdown."""
    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "cpic"}),
        content_type="application/json",
    )
    body = resp.get_json()
    by_gene = body["summary"].get("by_gene", [])
    assert len(by_gene) > 0, "by_gene must be non-empty"
    for entry in by_gene:
        assert "gene" in entry
        assert "drugs" in entry
        assert "diplotypes" in entry
