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


def test_pgx_summary_contract_deterministic_and_has_disclaimer_tags():
    app = _import_dashboard_app()
    client = app.test_client()

    resp1 = client.post("/api/pgx-summary", json={"source": "toy"})
    resp2 = client.post("/api/pgx-summary", json={"source": "toy"})

    assert resp1.status_code == 200
    assert resp2.status_code == 200

    data1 = resp1.get_json()
    data2 = resp2.get_json()
    assert isinstance(data1, dict)
    assert isinstance(data2, dict)
    assert data1 == data2

    assert data1.get("success") is True
    assert "summary" in data1 and isinstance(data1["summary"], dict)
    assert "disclaimer_tags" in data1 and isinstance(data1["disclaimer_tags"], list)
    assert len(data1["disclaimer_tags"]) >= 1

