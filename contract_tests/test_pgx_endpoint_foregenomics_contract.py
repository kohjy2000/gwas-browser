"""Contract tests for API_PGxSummary_ForeGenomics_v2.

Validates:
1. POST /api/pgx-summary with source="foregenomics" returns success with summary and disclaimer_tags.
2. summary.drugs has >= 10 unique drugs from the ForeGenomics snapshot.
3. Session storage: pgx_summary is stored in UPLOADS[session_id]['pgx_summary'].
4. source="toy" still works (backward compatibility).
5. Invalid source returns 400.
"""

import os
import sys
import json

import pytest

# --- Bootstrap: make the Flask app importable ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GWAS_PKG = os.path.join(PROJECT_ROOT, "gwas_variant_analyzer")
DASH_SRC = os.path.join(PROJECT_ROOT, "gwas_dashboard_package", "src")

for p in (GWAS_PKG, DASH_SRC):
    if p not in sys.path:
        sys.path.insert(0, p)

from routes.api import api_bp, UPLOADS  # noqa: E402
from flask import Flask  # noqa: E402


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
    """Clear UPLOADS between tests."""
    UPLOADS.clear()
    yield
    UPLOADS.clear()


# ---------- Acceptance criteria ----------


def test_foregenomics_source_returns_success(client):
    """POST /api/pgx-summary with source='foregenomics' returns success=true."""
    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert "summary" in body
    assert "disclaimer_tags" in body


def test_foregenomics_has_many_drugs(client):
    """summary.drugs must include >= 10 unique drugs for source='foregenomics'."""
    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics"}),
        content_type="application/json",
    )
    body = resp.get_json()
    drugs = body["summary"]["drugs"]
    assert len(drugs) >= 10, f"Expected >= 10 drugs, got {len(drugs)}"


def test_foregenomics_summary_structure(client):
    """Summary must contain total_rows, genes, drugs, by_gene."""
    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics"}),
        content_type="application/json",
    )
    body = resp.get_json()
    summary = body["summary"]
    assert "total_rows" in summary
    assert "genes" in summary
    assert "drugs" in summary
    assert "by_gene" in summary
    assert summary["total_rows"] > 0


def test_foregenomics_disclaimer_tags(client):
    """disclaimer_tags must be a non-empty list for foregenomics source."""
    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics"}),
        content_type="application/json",
    )
    body = resp.get_json()
    tags = body["disclaimer_tags"]
    assert isinstance(tags, list)
    assert len(tags) > 0
    assert "foregenomics_data" in tags


def test_foregenomics_session_storage(client):
    """pgx_summary must be stored in UPLOADS[session_id] when session_id provided."""
    session_id = "test_fg_session"
    UPLOADS[session_id] = {"variants": None}

    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics", "session_id": session_id}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert "pgx_summary" in UPLOADS[session_id]
    stored = UPLOADS[session_id]["pgx_summary"]
    assert "drugs" in stored
    assert len(stored["drugs"]) >= 10


def test_toy_source_still_works(client):
    """source='toy' must still return success (backward compat)."""
    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "toy"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True


def test_invalid_source_returns_400(client):
    """source='invalid' must return 400."""
    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "invalid_source"}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["success"] is False
