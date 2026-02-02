"""Contract tests for C9.B2: Chat Suggest Trait Analysis When Missing Facts.

Validates:
1. /api/chat response includes suggested_actions when user asks about a recognizable
   trait and gwas_hits are missing.
2. suggested_actions is an empty list when GWAS facts ARE present.
3. suggested_actions items have required keys (type, label, trait).
4. UI renders a suggested action button (chat-suggested-actions element).
"""

import json
import os
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DASH_SRC = os.path.join(PROJECT_ROOT, "gwas_dashboard_package", "src")
GWAS_PKG = os.path.join(PROJECT_ROOT, "gwas_variant_analyzer")

for p in (DASH_SRC, GWAS_PKG):
    if p not in sys.path:
        sys.path.insert(0, p)

from flask import Flask
from routes.api import api_bp


@pytest.fixture()
def app():
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.register_blueprint(api_bp, url_prefix="/api")
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


# ---------- suggested_actions present when trait detected, no GWAS facts ----------


def test_suggested_actions_present_for_trait_question_without_gwas(client):
    """When user asks about a recognizable trait but no GWAS facts, suggested_actions is non-empty."""
    resp = client.post(
        "/api/chat",
        data=json.dumps({"message": "What is my obesity risk?"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert "suggested_actions" in body
    actions = body["suggested_actions"]
    assert isinstance(actions, list)
    assert len(actions) > 0, "Expected at least one suggested action for 'obesity' query without GWAS facts"


def test_suggested_action_has_required_keys(client):
    """Each suggested_action must have type, label, trait."""
    resp = client.post(
        "/api/chat",
        data=json.dumps({"message": "Tell me about my type 2 diabetes risk"}),
        content_type="application/json",
    )
    body = resp.get_json()
    actions = body.get("suggested_actions", [])
    assert len(actions) > 0
    for action in actions:
        assert "type" in action, "Missing 'type' key in suggested action"
        assert "label" in action, "Missing 'label' key in suggested action"
        assert "trait" in action, "Missing 'trait' key in suggested action"
        assert action["type"] == "analyze_trait"


def test_suggested_actions_empty_when_gwas_facts_present(client):
    """When GWAS facts are provided, suggested_actions should be empty."""
    resp = client.post(
        "/api/chat",
        data=json.dumps({
            "message": "What is my obesity risk?",
            "gwas_associations": [
                {"trait": "Obesity", "variant": "rs1234", "p_value": "1e-9", "pubmed_id": "12345"},
            ],
        }),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert "suggested_actions" in body
    actions = body["suggested_actions"]
    assert isinstance(actions, list)
    assert len(actions) == 0, "suggested_actions should be empty when GWAS facts are present"


def test_suggested_actions_empty_for_generic_message(client):
    """A generic message with no recognizable trait should yield empty suggested_actions."""
    resp = client.post(
        "/api/chat",
        data=json.dumps({"message": "hello"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert "suggested_actions" in body
    actions = body["suggested_actions"]
    assert isinstance(actions, list)
    assert len(actions) == 0, "No trait detected in generic message, suggested_actions should be empty"


def test_suggested_actions_always_present_in_response(client):
    """suggested_actions key must always be present in chat response."""
    resp = client.post(
        "/api/chat",
        data=json.dumps({"message": "anything"}),
        content_type="application/json",
    )
    body = resp.get_json()
    assert "suggested_actions" in body
    assert isinstance(body["suggested_actions"], list)


# ---------- UI contract: index.html renders suggested actions ----------


def test_ui_has_suggested_actions_handler():
    """index.html must contain handleSuggestedAnalyze and chat-suggested-actions rendering."""
    html_path = os.path.join(
        PROJECT_ROOT, "gwas_dashboard_package", "src", "static", "index.html"
    )
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    assert "handleSuggestedAnalyze" in html, "index.html must define handleSuggestedAnalyze function"
    assert "chat-suggested-actions" in html, "index.html must render chat-suggested-actions element"
    assert "suggested_actions" in html, "index.html must reference suggested_actions from API response"
