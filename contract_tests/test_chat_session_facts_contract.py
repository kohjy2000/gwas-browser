"""Contract tests for API_Chat_SessionFacts_v2.

Validates that /api/chat uses session-derived facts when session_id is provided,
and does not return the 'no facts loaded' message when session facts exist.
"""

import os
import sys

import pandas as pd


def _setup():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    gwas_pkg_parent = os.path.join(project_root, "gwas_variant_analyzer")
    if gwas_pkg_parent not in sys.path:
        sys.path.insert(0, gwas_pkg_parent)
    package_root = os.path.join(project_root, "gwas_dashboard_package")
    if package_root not in sys.path:
        sys.path.insert(0, package_root)

    from src.main import app  # noqa: E402
    from src.routes.api import UPLOADS  # noqa: E402

    return app, UPLOADS


def _seed_session(uploads, session_id="test-session-facts"):
    """Seed a fake session with clinvar_matches and pgx_summary stored."""
    uploads[session_id] = {
        "file_path": "/tmp/fake.vcf",
        "variants": pd.DataFrame({"chrom": ["1"], "pos": [100], "ref": ["A"], "alt": ["T"]}),
        "clinvar_matches": [
            {
                "user_chrom": "1",
                "user_pos": 100,
                "user_ref": "A",
                "user_alt": "T",
                "gene": "BRCA1",
                "clinical_significance": "Pathogenic",
                "condition": "Breast cancer",
                "variation_id": "12345",
            }
        ],
        "pgx_summary": {
            "total_rows": 2,
            "genes": ["CYP2D6"],
            "drugs": ["codeine"],
            "by_gene": [
                {
                    "gene": "CYP2D6",
                    "rows": 2,
                    "diplotypes": ["*1/*1", "*4/*4"],
                    "phenotypes": ["Normal metabolizer", "Poor metabolizer"],
                    "drugs": ["codeine"],
                }
            ],
        },
    }
    return session_id


def test_chat_with_session_id_uses_session_facts():
    app, uploads = _setup()
    sid = _seed_session(uploads)
    client = app.test_client()

    resp = client.post("/api/chat", json={"message": "What are my results?", "session_id": sid})
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["success"] is True
    assert "no genetic facts" not in data["answer"].lower()
    assert "no facts loaded" not in data["answer"].lower()
    assert len(data["answer"]) > 0


def test_chat_with_session_id_has_disclaimer_tags():
    app, uploads = _setup()
    sid = _seed_session(uploads)
    client = app.test_client()

    resp = client.post("/api/chat", json={"message": "Tell me about BRCA1", "session_id": sid})
    data = resp.get_json()

    assert "disclaimer_tags" in data
    assert isinstance(data["disclaimer_tags"], list)
    assert len(data["disclaimer_tags"]) >= 1


def test_chat_with_session_id_has_citations():
    app, uploads = _setup()
    sid = _seed_session(uploads)
    client = app.test_client()

    resp = client.post("/api/chat", json={"message": "Explain my CYP2D6", "session_id": sid})
    data = resp.get_json()

    assert "citations" in data
    assert isinstance(data["citations"], list)
    assert len(data["citations"]) >= 1


def test_chat_without_session_id_shows_no_facts_message():
    """Without session_id and without explicit facts, should get 'no facts' message."""
    app, _ = _setup()
    client = app.test_client()

    resp = client.post("/api/chat", json={"message": "Hello"})
    data = resp.get_json()

    assert data["success"] is True
    lower_answer = data["answer"].lower()
    assert "no genetic facts" in lower_answer or "upload" in lower_answer


def test_chat_session_facts_deterministic():
    app, uploads = _setup()
    sid = _seed_session(uploads)
    client = app.test_client()

    resp1 = client.post("/api/chat", json={"message": "results?", "session_id": sid})
    resp2 = client.post("/api/chat", json={"message": "results?", "session_id": sid})

    data1 = resp1.get_json()
    data2 = resp2.get_json()

    assert data1["answer"] == data2["answer"]
    assert data1["citations"] == data2["citations"]
    assert data1["risk_level"] == data2["risk_level"]
