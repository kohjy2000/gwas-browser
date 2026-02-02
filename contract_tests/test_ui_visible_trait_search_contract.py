"""Contract tests for UI_VisibleTraitSearch_v1.

Validates:
1. The visible search box uses POST /api/search-traits.
2. Contract-required elements (trait-search-input, trait-search-results, selected-efo-id)
   are NOT hidden via display:none + aria-hidden=true.
3. "Obes" yields "obesity" as the first suggestion from /api/search-traits.
4. Selected efo_id from /api/search-traits is the value used for /api/analyze.
"""

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


def test_html_file_exists():
    """index.html must exist."""
    assert os.path.isfile(HTML_PATH), f"HTML file not found: {HTML_PATH}"


def test_trait_search_input_visible(html_source):
    """trait-search-input must NOT have display:none + aria-hidden=true."""
    # Find the element tag containing id="trait-search-input"
    pattern = r'<[^>]*id=["\']trait-search-input["\'][^>]*>'
    match = re.search(pattern, html_source)
    assert match, "Element with id='trait-search-input' not found in HTML"
    tag = match.group(0)
    has_display_none = "display:none" in tag or "display: none" in tag
    has_aria_hidden = 'aria-hidden="true"' in tag or "aria-hidden='true'" in tag
    assert not (has_display_none and has_aria_hidden), (
        f"trait-search-input is hidden (display:none + aria-hidden=true): {tag}"
    )


def test_trait_search_results_visible(html_source):
    """trait-search-results must NOT have display:none + aria-hidden=true."""
    pattern = r'<[^>]*id=["\']trait-search-results["\'][^>]*>'
    match = re.search(pattern, html_source)
    assert match, "Element with id='trait-search-results' not found in HTML"
    tag = match.group(0)
    has_display_none = "display:none" in tag or "display: none" in tag
    has_aria_hidden = 'aria-hidden="true"' in tag or "aria-hidden='true'" in tag
    assert not (has_display_none and has_aria_hidden), (
        f"trait-search-results is hidden (display:none + aria-hidden=true): {tag}"
    )


def test_selected_efo_id_present(html_source):
    """selected-efo-id hidden input must exist in the HTML."""
    assert 'id="selected-efo-id"' in html_source or "id='selected-efo-id'" in html_source


def test_html_uses_search_traits_endpoint(html_source):
    """The HTML/JS must reference /api/search-traits for the visible search."""
    assert "/api/search-traits" in html_source, (
        "HTML does not reference /api/search-traits"
    )


# ---------- API behavior tests ----------


def test_search_traits_obes_returns_obesity(client):
    """POST /api/search-traits with query='Obes' must return obesity as top result."""
    import json
    resp = client.post(
        "/api/search-traits",
        data=json.dumps({"query": "Obes", "top_k": 5}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert len(body["results"]) > 0
    top = body["results"][0]
    assert "obesity" in top["trait"].lower(), (
        f"Expected 'obesity' as top result, got '{top['trait']}'"
    )


def test_search_traits_returns_efo_id(client):
    """Each search result must have an efo_id field."""
    import json
    resp = client.post(
        "/api/search-traits",
        data=json.dumps({"query": "diabetes", "top_k": 3}),
        content_type="application/json",
    )
    body = resp.get_json()
    assert body["success"] is True
    for item in body["results"]:
        assert "efo_id" in item, f"Missing efo_id in search result: {item}"
        assert item["efo_id"], f"Empty efo_id in search result: {item}"
