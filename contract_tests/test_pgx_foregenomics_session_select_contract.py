"""Contract tests for API_PGxSummary_ForeGenomics_SessionSelect_v1.

Validates:
1. With FOREGENOMICS_PGX_ROOT set, source="foregenomics" uses the report
   matching the session's sample_id.
2. Two different sample_ids produce different summaries.
3. Without FOREGENOMICS_PGX_ROOT, falls back to the default report.
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

REPORTS_DIR = os.path.join(PROJECT_ROOT, "data", "pgx", "foregenomics_reports")


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


@pytest.fixture(autouse=True)
def _set_pgx_root(monkeypatch):
    """Point FOREGENOMICS_PGX_ROOT to the fixture reports directory."""
    monkeypatch.setenv("FOREGENOMICS_PGX_ROOT", REPORTS_DIR)


# ---------- find_foregenomics_report unit tests ----------


def test_find_report_returns_path_for_existing_sample():
    """find_foregenomics_report returns a path when the file exists."""
    from gwas_variant_analyzer.pgx_foregenomics import find_foregenomics_report

    path = find_foregenomics_report(REPORTS_DIR, "SAMPLE_A")
    assert path is not None
    assert os.path.isfile(path)
    assert "SAMPLE_A" in path


def test_find_report_returns_none_for_missing_sample():
    """find_foregenomics_report returns None for a non-existent sample."""
    from gwas_variant_analyzer.pgx_foregenomics import find_foregenomics_report

    path = find_foregenomics_report(REPORTS_DIR, "NO_SUCH_SAMPLE")
    assert path is None


# ---------- API: per-session report selection ----------


def test_session_sample_a_returns_success(client):
    """Session with sample_id=SAMPLE_A returns success."""
    UPLOADS["sess_a"] = {"variants": None, "sample_id": "SAMPLE_A"}

    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics", "session_id": "sess_a"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert "summary" in body
    assert body["summary"]["total_rows"] > 0


def test_session_sample_b_returns_success(client):
    """Session with sample_id=SAMPLE_B returns success."""
    UPLOADS["sess_b"] = {"variants": None, "sample_id": "SAMPLE_B"}

    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics", "session_id": "sess_b"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["summary"]["total_rows"] > 0


def test_different_samples_produce_different_summaries(client):
    """Two sessions with different sample_ids produce different summaries."""
    UPLOADS["sess_a"] = {"variants": None, "sample_id": "SAMPLE_A"}
    UPLOADS["sess_b"] = {"variants": None, "sample_id": "SAMPLE_B"}

    resp_a = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics", "session_id": "sess_a"}),
        content_type="application/json",
    )
    resp_b = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics", "session_id": "sess_b"}),
        content_type="application/json",
    )

    summary_a = resp_a.get_json()["summary"]
    summary_b = resp_b.get_json()["summary"]

    # They must differ in at least one of: genes, drugs, or total_rows
    differs = (
        set(summary_a["genes"]) != set(summary_b["genes"])
        or set(summary_a["drugs"]) != set(summary_b["drugs"])
        or summary_a["total_rows"] != summary_b["total_rows"]
    )
    assert differs, (
        f"SAMPLE_A and SAMPLE_B summaries are identical: "
        f"genes_a={summary_a['genes']}, genes_b={summary_b['genes']}"
    )


def test_no_pgx_root_falls_back_to_default(client, monkeypatch):
    """Without FOREGENOMICS_PGX_ROOT, falls back to default report path."""
    monkeypatch.delenv("FOREGENOMICS_PGX_ROOT", raising=False)
    monkeypatch.delenv("FOREGENOMICS_PGX_REPORT_PATH", raising=False)

    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True


def test_session_stores_pgx_summary(client):
    """pgx_summary is stored in UPLOADS[session_id] after call."""
    UPLOADS["sess_store"] = {"variants": None, "sample_id": "SAMPLE_A"}

    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics", "session_id": "sess_store"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert "pgx_summary" in UPLOADS["sess_store"]
    stored = UPLOADS["sess_store"]["pgx_summary"]
    assert "drugs" in stored
    assert len(stored["drugs"]) > 0


def test_disclaimer_tags_present(client):
    """Response includes disclaimer_tags with foregenomics_data."""
    UPLOADS["sess_tag"] = {"variants": None, "sample_id": "SAMPLE_A"}

    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics", "session_id": "sess_tag"}),
        content_type="application/json",
    )
    body = resp.get_json()
    assert "disclaimer_tags" in body
    assert "foregenomics_data" in body["disclaimer_tags"]
