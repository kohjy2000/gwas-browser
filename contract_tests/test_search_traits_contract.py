import os
import sys


def _import_dashboard_app():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    gwas_pkg_parent = os.path.join(project_root, "gwas_variant_analyzer")
    if gwas_pkg_parent not in sys.path:
        sys.path.insert(0, gwas_pkg_parent)

    package_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gwas_dashboard_package"))
    if package_root not in sys.path:
        sys.path.insert(0, package_root)
    from src.main import app  # noqa: E402
    return app


def test_search_traits_query_too_short_returns_400():
    app = _import_dashboard_app()
    client = app.test_client()

    resp = client.post("/api/search-traits", json={"query": "di"})
    assert resp.status_code == 400
    data = resp.get_json()
    assert isinstance(data, dict)
    assert data.get("success") is False
    assert "message" in data


def test_search_traits_contract_schema_and_sorting():
    app = _import_dashboard_app()

    package_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gwas_dashboard_package"))
    if package_root not in sys.path:
        sys.path.insert(0, package_root)
    from src.routes import api as api_module  # noqa: E402

    api_module._trait_list = [
        {"trait": "diabetes mellitus", "shortForm": "EFO_0000400", "uri": ""},
        {"trait": "breast cancer", "shortForm": "EFO_0000305", "uri": ""},
        {"trait": "type 2 diabetes mellitus", "shortForm": "EFO_0001360", "uri": ""},
    ]

    client = app.test_client()
    resp = client.post("/api/search-traits", json={"query": "diab", "top_k": 10})
    assert resp.status_code == 200

    data = resp.get_json()
    assert isinstance(data, dict)
    assert data.get("success") is True

    results = data.get("results")
    assert isinstance(results, list)
    assert len(results) >= 1

    first = results[0]
    assert set(first.keys()) == {"trait", "efo_id", "score"}
    assert isinstance(first["trait"], str)
    assert isinstance(first["efo_id"], str)
    assert isinstance(first["score"], (int, float))

    # "diabetes mellitus" should win (prefix match=1.0) vs "type 2 diabetes..." (contains match=0.8)
    assert results[0]["trait"] == "diabetes mellitus"
    assert results[0]["efo_id"] == "EFO_0000400"
