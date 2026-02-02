import os


def _read(rel_path: str) -> str:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    full = os.path.join(project_root, rel_path)
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


def test_frontend_contract_required_ids_exist():
    html = _read("gwas_dashboard_package/src/static/index.html")
    assert "trait-search-input" in html
    assert "trait-search-results" in html
    assert "selected-efo-id" in html


def test_frontend_contract_calls_search_endpoint_and_uses_hidden_efo():
    js = _read("gwas_dashboard_package/src/static/js/dashboard.js")
    assert "/api/search-traits" in js or "search-traits" in js
    assert "selected-efo-id" in js

