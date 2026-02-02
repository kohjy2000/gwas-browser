"""Contract tests for C8.B2: ForeGenomics Report Path Override (Env).

Validates:
1. When FOREGENOMICS_PGX_REPORT_PATH is set, /api/pgx-summary uses that path.
2. When the env var is unset, it falls back to data/pgx/foregenomics_report.tsv.
3. Setting the env var to a non-existent file returns a 500 error.
"""

import json
import os
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GWAS_PKG = os.path.join(PROJECT_ROOT, "gwas_variant_analyzer")
DASH_SRC = os.path.join(PROJECT_ROOT, "gwas_dashboard_package", "src")

for p in (GWAS_PKG, DASH_SRC):
    if p not in sys.path:
        sys.path.insert(0, p)

from routes.api import api_bp  # noqa: E402
from flask import Flask  # noqa: E402

SNAPSHOT_PATH = os.path.join(PROJECT_ROOT, "data", "pgx", "foregenomics_report.tsv")


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
def _clean_env():
    """Ensure FOREGENOMICS_PGX_REPORT_PATH is clean between tests."""
    old = os.environ.pop("FOREGENOMICS_PGX_REPORT_PATH", None)
    yield
    if old is not None:
        os.environ["FOREGENOMICS_PGX_REPORT_PATH"] = old
    else:
        os.environ.pop("FOREGENOMICS_PGX_REPORT_PATH", None)


# ---------- Tests ----------


def test_env_path_override_uses_custom_file(client, tmp_path):
    """When FOREGENOMICS_PGX_REPORT_PATH points to a valid TSV, it is used."""
    # Copy the snapshot to a temp location to prove the env var is respected
    import shutil
    custom_path = str(tmp_path / "custom_fg_report.tsv")
    shutil.copy(SNAPSHOT_PATH, custom_path)
    os.environ["FOREGENOMICS_PGX_REPORT_PATH"] = custom_path

    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert len(body["summary"]["drugs"]) >= 10


def test_fallback_to_snapshot_when_env_unset(client):
    """When FOREGENOMICS_PGX_REPORT_PATH is not set, snapshot is used."""
    os.environ.pop("FOREGENOMICS_PGX_REPORT_PATH", None)

    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert len(body["summary"]["drugs"]) >= 10


def test_env_path_nonexistent_returns_error(client):
    """When FOREGENOMICS_PGX_REPORT_PATH points to a missing file, returns 500."""
    os.environ["FOREGENOMICS_PGX_REPORT_PATH"] = "/tmp/does_not_exist_fg.tsv"

    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics"}),
        content_type="application/json",
    )
    assert resp.status_code == 500
    body = resp.get_json()
    assert body["success"] is False


def test_toy_source_unaffected_by_env(client):
    """source='toy' ignores FOREGENOMICS_PGX_REPORT_PATH."""
    os.environ["FOREGENOMICS_PGX_REPORT_PATH"] = "/tmp/does_not_exist_fg.tsv"

    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "toy"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True


def test_env_path_empty_string_falls_back(client):
    """Empty FOREGENOMICS_PGX_REPORT_PATH falls back to snapshot."""
    os.environ["FOREGENOMICS_PGX_REPORT_PATH"] = ""

    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert len(body["summary"]["drugs"]) >= 10
