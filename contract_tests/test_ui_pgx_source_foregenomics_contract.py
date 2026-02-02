"""Contract tests for C8.B1: UI PGx Summary Defaults to ForeGenomics Source.

Validates:
1. The pgx-source select element exists in the HTML.
2. The default (first) option value is "foregenomics".
3. The JS references /api/pgx-summary and uses the pgx-source value.
4. POST /api/pgx-summary with source="foregenomics" returns >= 10 drugs.
5. The response summary structure matches what the UI expects (by_gene with genotypes).
"""

import json
import os
import re
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HTML_PATH = os.path.join(
    PROJECT_ROOT, "gwas_dashboard_package", "src", "static", "index.html"
)

GWAS_PKG = os.path.join(PROJECT_ROOT, "gwas_variant_analyzer")
DASH_SRC = os.path.join(PROJECT_ROOT, "gwas_dashboard_package", "src")

for p in (GWAS_PKG, DASH_SRC):
    if p not in sys.path:
        sys.path.insert(0, p)

from routes.api import api_bp  # noqa: E402
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


@pytest.fixture(scope="module")
def html_source():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ---------- HTML structure tests ----------


def test_pgx_source_select_exists(html_source):
    """The pgx-source select element must exist."""
    assert 'id="pgx-source"' in html_source or "id='pgx-source'" in html_source


def test_pgx_source_default_is_foregenomics(html_source):
    """The first <option> inside pgx-source must have value='foregenomics'."""
    pattern = r'<select[^>]*id=["\']pgx-source["\'][^>]*>(.*?)</select>'
    match = re.search(pattern, html_source, re.DOTALL)
    assert match, "pgx-source <select> not found"
    options_html = match.group(1)
    first_option = re.search(r'<option[^>]*value=["\']([^"\']+)["\']', options_html)
    assert first_option, "No <option> found inside pgx-source"
    assert first_option.group(1) == "foregenomics", (
        f"Default pgx-source option is '{first_option.group(1)}', expected 'foregenomics'"
    )


def test_js_uses_pgx_source_value(html_source):
    """The JS must read the pgx-source element value."""
    assert "pgx-source" in html_source
    assert "getElementById('pgx-source')" in html_source or \
        'getElementById("pgx-source")' in html_source


def test_js_calls_pgx_summary_endpoint(html_source):
    """The JS must call /api/pgx-summary."""
    assert "/api/pgx-summary" in html_source


# ---------- API behavior tests ----------


def test_foregenomics_returns_many_drugs(client):
    """POST /api/pgx-summary with source='foregenomics' must return >= 10 drugs."""
    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    drugs = body["summary"]["drugs"]
    assert len(drugs) >= 10, f"Expected >= 10 drugs, got {len(drugs)}"


def test_foregenomics_by_gene_has_genotypes(client):
    """by_gene entries for foregenomics must have 'genotypes' (not 'diplotypes')."""
    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics"}),
        content_type="application/json",
    )
    body = resp.get_json()
    assert body["success"] is True
    by_gene = body["summary"]["by_gene"]
    assert len(by_gene) > 0
    first = by_gene[0]
    assert "genotypes" in first, f"Missing 'genotypes' key in by_gene entry: {first}"


def test_foregenomics_disclaimer_tag(client):
    """disclaimer_tags must include 'foregenomics_data'."""
    resp = client.post(
        "/api/pgx-summary",
        data=json.dumps({"source": "foregenomics"}),
        content_type="application/json",
    )
    body = resp.get_json()
    assert body["success"] is True
    assert "foregenomics_data" in body["disclaimer_tags"]
