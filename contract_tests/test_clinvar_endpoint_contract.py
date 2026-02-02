import os
import sys

import pandas as pd


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


def test_clinvar_match_missing_session_id_returns_400():
    app = _import_dashboard_app()
    client = app.test_client()

    resp = client.post("/api/clinvar-match", json={})
    assert resp.status_code == 400
    data = resp.get_json()
    assert isinstance(data, dict)
    assert data.get("success") is False


def test_clinvar_match_success_schema_and_determinism():
    app = _import_dashboard_app()

    package_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gwas_dashboard_package"))
    if package_root not in sys.path:
        sys.path.insert(0, package_root)
    from src.routes import api as api_module  # noqa: E402

    session_id = "SESSION_CONTRACT"
    api_module.UPLOADS[session_id] = {
        "file_path": "dummy",
        "variants": pd.DataFrame(
            [
                # rsid-only fallback match
                {"USER_CHROM": "chr7", "USER_POS": 1, "USER_REF": "A", "USER_ALT": "C", "SNP_ID": "rs113993960"},
                # primary match
                {"USER_CHROM": "chr1", "USER_POS": 1000, "USER_REF": "A", "USER_ALT": "G", "SNP_ID": "rs000000001"},
                # benign in TSV should be excluded by default matcher filter
                {"USER_CHROM": "17", "USER_POS": 43071077, "USER_REF": "C", "USER_ALT": "T", "SNP_ID": "rs80357065"},
            ]
        ),
    }

    client = app.test_client()
    resp1 = client.post("/api/clinvar-match", json={"session_id": session_id})
    resp2 = client.post("/api/clinvar-match", json={"session_id": session_id})

    assert resp1.status_code == 200
    assert resp2.status_code == 200

    data1 = resp1.get_json()
    data2 = resp2.get_json()
    assert isinstance(data1, dict)
    assert isinstance(data2, dict)
    assert data1 == data2

    assert data1.get("success") is True
    assert "summary" in data1 and isinstance(data1["summary"], dict)
    assert "matches" in data1 and isinstance(data1["matches"], list)

    matches = data1["matches"]
    assert len(matches) == 2
    assert all(isinstance(m, dict) for m in matches)
    assert all("match_type" in m and "match_key" in m for m in matches)

    # Deterministic ordering: primary (chr1:1000) should come before rsid-only (chr7)
    assert matches[0]["match_key"] == "1-1000-A-G"
    assert matches[0]["match_type"] == "primary"
    assert matches[1]["match_type"] in {"rsid", "primary"}

