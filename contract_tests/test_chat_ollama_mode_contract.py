"""Contract tests for API_Chat_OllamaMode_v1.

Validates that /api/chat supports an Ollama-backed local LLM mode:
- Ollama is invoked when env vars are set and facts exist.
- Response always includes disclaimer_tags (non-empty) and citations (non-empty).
- Citations reference known fact IDs.
- Tests do NOT require a running Ollama — all calls are monkeypatched.
"""

import os
import sys

import pandas as pd
import pytest


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


def _seed_session(uploads, session_id="test-ollama-session"):
    """Seed a fake session with clinvar + pgx data."""
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


FAKE_OLLAMA_RESPONSE = {
    "response": (
        "Based on your genetic data, I can see the following:\n"
        "- [clinvar-0000-brca1] You have a pathogenic variant in BRCA1.\n"
        "- [pgx-0000-cyp2d6-codeine] CYP2D6 affects codeine metabolism.\n"
        "IMPORTANT: This is not medical advice. Please consult a professional."
    )
}


class _FakeOllamaResponse:
    status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return FAKE_OLLAMA_RESPONSE


@pytest.fixture(autouse=True)
def _disable_ollama(monkeypatch):
    """By default, Ollama is OFF for all tests."""
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL_CHAT", raising=False)


@pytest.fixture()
def _enable_ollama(monkeypatch):
    """Enable Ollama mode via env vars."""
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    monkeypatch.setenv("OLLAMA_MODEL_CHAT", "llama3.1:8b-instruct")


# ---------- tests ----------


def test_ollama_called_when_enabled(_enable_ollama, monkeypatch):
    """When Ollama env vars are set and facts exist, the Ollama HTTP API must be invoked."""
    app, uploads = _setup()
    import src.routes.api as api_mod

    sid = _seed_session(uploads)
    called = {"count": 0}

    def fake_post(*args, **kwargs):
        called["count"] += 1
        return _FakeOllamaResponse()

    monkeypatch.setattr(api_mod.http_requests, "post", fake_post)

    client = app.test_client()
    resp = client.post("/api/chat", json={"message": "Tell me about BRCA1", "session_id": sid})

    assert resp.status_code == 200
    assert called["count"] == 1, "Ollama HTTP API must be called when enabled with facts"


def test_ollama_response_has_disclaimer_tags(_enable_ollama, monkeypatch):
    """Even in Ollama mode, response must include non-empty disclaimer_tags."""
    app, uploads = _setup()
    import src.routes.api as api_mod

    sid = _seed_session(uploads)
    monkeypatch.setattr(api_mod.http_requests, "post", lambda *a, **kw: _FakeOllamaResponse())

    client = app.test_client()
    resp = client.post("/api/chat", json={"message": "What does BRCA1 mean?", "session_id": sid})
    data = resp.get_json()

    assert data["success"] is True
    assert "disclaimer_tags" in data
    assert isinstance(data["disclaimer_tags"], list)
    assert len(data["disclaimer_tags"]) >= 1


def test_ollama_response_has_citations(_enable_ollama, monkeypatch):
    """Even in Ollama mode, response must include non-empty citations referencing known fact IDs."""
    app, uploads = _setup()
    import src.routes.api as api_mod

    sid = _seed_session(uploads)
    monkeypatch.setattr(api_mod.http_requests, "post", lambda *a, **kw: _FakeOllamaResponse())

    client = app.test_client()
    resp = client.post("/api/chat", json={"message": "Explain CYP2D6", "session_id": sid})
    data = resp.get_json()

    assert data["success"] is True
    assert "citations" in data
    assert isinstance(data["citations"], list)
    assert len(data["citations"]) >= 1


def test_ollama_not_called_when_disabled(monkeypatch):
    """When Ollama env vars are NOT set, deterministic mode must be used."""
    app, uploads = _setup()
    import src.routes.api as api_mod

    sid = _seed_session(uploads)
    called = {"count": 0}

    def fake_post(*args, **kwargs):
        called["count"] += 1
        return _FakeOllamaResponse()

    monkeypatch.setattr(api_mod.http_requests, "post", fake_post)

    client = app.test_client()
    resp = client.post("/api/chat", json={"message": "Hello", "session_id": sid})

    assert resp.status_code == 200
    assert called["count"] == 0, "Ollama must NOT be called when env vars are not set"


def test_ollama_failure_falls_back_to_deterministic(_enable_ollama, monkeypatch):
    """If Ollama call fails, the endpoint must fall back to deterministic answer."""
    app, uploads = _setup()
    import src.routes.api as api_mod

    sid = _seed_session(uploads)

    def failing_post(*args, **kwargs):
        raise ConnectionError("Ollama unreachable")

    monkeypatch.setattr(api_mod.http_requests, "post", failing_post)

    client = app.test_client()
    resp = client.post("/api/chat", json={"message": "What are my results?", "session_id": sid})
    data = resp.get_json()

    assert data["success"] is True
    assert len(data["answer"]) > 0
    assert len(data["disclaimer_tags"]) >= 1
    assert len(data["citations"]) >= 1


def test_ollama_answer_validates_fact_ids(_enable_ollama, monkeypatch):
    """The Ollama answer must reference known fact IDs (validated by backend)."""
    app, uploads = _setup()
    import src.routes.api as api_mod

    sid = _seed_session(uploads)

    # Return a response that does NOT mention any fact IDs
    class _NoFactIdResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"response": "Some generic answer without any fact references."}

    monkeypatch.setattr(api_mod.http_requests, "post", lambda *a, **kw: _NoFactIdResponse())

    client = app.test_client()
    resp = client.post("/api/chat", json={"message": "Tell me", "session_id": sid})
    data = resp.get_json()

    assert data["success"] is True
    # The validator should augment the answer with fact references
    assert any(cid in data["answer"] for cid in data["citations"]), (
        f"Answer must reference at least one known fact ID. "
        f"Answer: {data['answer'][:200]}, Citations: {data['citations']}"
    )


def test_deterministic_mode_still_works_without_ollama(monkeypatch):
    """Without Ollama, the existing deterministic mode must still work correctly."""
    app, uploads = _setup()
    sid = _seed_session(uploads)

    client = app.test_client()
    resp = client.post("/api/chat", json={"message": "results?", "session_id": sid})
    data = resp.get_json()

    assert data["success"] is True
    assert len(data["answer"]) > 0
    assert "no genetic facts" not in data["answer"].lower()
    assert len(data["disclaimer_tags"]) >= 1
    assert len(data["citations"]) >= 1
    assert data["risk_level"] in {"low", "medium", "high", "critical"}
