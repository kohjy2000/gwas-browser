"""Contract tests for C8.B4: Chat Transparency — Report Ollama Model Used.

Validates:
1. /api/chat response always includes an 'llm' object.
2. In deterministic mode, llm.enabled=false, llm.provider='deterministic', llm.model=''.
3. In ollama mode (mocked), llm.enabled=true, llm.provider='ollama', llm.model=<tag>.
"""

import json
import os
import sys
from unittest.mock import patch

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
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


@pytest.fixture(autouse=True)
def _clean_ollama_env():
    """Ensure Ollama env vars are clean between tests."""
    old_host = os.environ.pop("OLLAMA_HOST", None)
    old_model = os.environ.pop("OLLAMA_MODEL_CHAT", None)
    yield
    if old_host is not None:
        os.environ["OLLAMA_HOST"] = old_host
    else:
        os.environ.pop("OLLAMA_HOST", None)
    if old_model is not None:
        os.environ["OLLAMA_MODEL_CHAT"] = old_model
    else:
        os.environ.pop("OLLAMA_MODEL_CHAT", None)


# ---------- Deterministic mode ----------


def test_deterministic_mode_llm_info(client):
    """Without Ollama env vars, llm reports deterministic mode."""
    os.environ.pop("OLLAMA_HOST", None)
    os.environ.pop("OLLAMA_MODEL_CHAT", None)

    resp = client.post(
        "/api/chat",
        data=json.dumps({"message": "What is my risk?"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert "llm" in body
    llm = body["llm"]
    assert llm["enabled"] is False
    assert llm["provider"] == "deterministic"
    assert llm["model"] == ""


def test_llm_field_always_present(client):
    """The llm field must always be present in the response."""
    resp = client.post(
        "/api/chat",
        data=json.dumps({"message": "hello"}),
        content_type="application/json",
    )
    body = resp.get_json()
    assert "llm" in body
    assert "enabled" in body["llm"]
    assert "provider" in body["llm"]
    assert "model" in body["llm"]


# ---------- Ollama mode (mocked) ----------


def test_ollama_mode_llm_info(client):
    """With Ollama enabled and successful call, llm reports ollama mode + model tag."""
    os.environ["OLLAMA_HOST"] = "http://127.0.0.1:11434"
    os.environ["OLLAMA_MODEL_CHAT"] = "deepseek-r1:32b"

    fake_response = "[FACT_gwas_0] Based on the genetic data, your results indicate..."

    with patch("routes.api._call_ollama", return_value=fake_response):
        resp = client.post(
            "/api/chat",
            data=json.dumps({
                "message": "What is my risk?",
                "gwas_associations": [
                    {"trait": "Obesity", "snp_id": "rs1234", "p_value": 1e-9, "odds_ratio": 1.5}
                ],
            }),
            content_type="application/json",
        )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    llm = body["llm"]
    assert llm["enabled"] is True
    assert llm["provider"] == "ollama"
    assert llm["model"] == "deepseek-r1:32b"


def test_ollama_fallback_reports_deterministic(client):
    """When Ollama is enabled but call fails, llm reports deterministic fallback."""
    os.environ["OLLAMA_HOST"] = "http://127.0.0.1:11434"
    os.environ["OLLAMA_MODEL_CHAT"] = "deepseek-r1:32b"

    with patch("routes.api._call_ollama", side_effect=Exception("Connection refused")):
        resp = client.post(
            "/api/chat",
            data=json.dumps({
                "message": "What is my risk?",
                "gwas_associations": [
                    {"trait": "Obesity", "snp_id": "rs1234", "p_value": 1e-9, "odds_ratio": 1.5}
                ],
            }),
            content_type="application/json",
        )

    assert resp.status_code == 200
    body = resp.get_json()
    llm = body["llm"]
    assert llm["enabled"] is False
    assert llm["provider"] == "deterministic"
