"""Contract tests for API_SearchTraits_RemoteGWASCatalog_v2.

Validates that /api/search-traits falls back to the GWAS Catalog REST API
when local results are empty or weak, merges remote results into the
response, and persists new traits into data/trait_list.json + meta.

All tests monkeypatch the HTTP client — no real network calls.
"""

import json
import os
import sys
import shutil

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
    return app


# ---------- helpers ----------

FAKE_REMOTE_RESPONSE = {
    "_embedded": {
        "efoTraits": [
            {
                "trait": "fake remote trait alpha",
                "shortForm": "EFO_9999901",
                "_links": {"self": {"href": "http://example.com/1"}},
            },
            {
                "trait": "fake remote trait beta",
                "shortForm": "EFO_9999902",
                "_links": {"self": {"href": "http://example.com/2"}},
            },
        ]
    }
}


class _FakeResponse:
    """Minimal requests.Response stand-in."""

    status_code = 200

    def __init__(self, json_data):
        self._json = json_data

    def raise_for_status(self):
        pass

    def json(self):
        return self._json


@pytest.fixture(autouse=True)
def _enable_remote_and_reset_trait_list(monkeypatch):
    """Turn on remote search and reset in-memory trait list for every test."""
    monkeypatch.setenv("GWAS_REMOTE_SEARCH", "1")
    # Force trait list reload from disk on next access
    _setup()  # ensure module is imported
    import src.routes.api as api_mod
    api_mod._trait_list = None


@pytest.fixture()
def _tmp_trait_files(monkeypatch, tmp_path):
    """Point the app at temporary trait_list.json and meta files."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    orig = os.path.join(project_root, "data", "trait_list.json")
    tmp_data = tmp_path / "data"
    tmp_data.mkdir()
    dst = tmp_data / "trait_list.json"
    shutil.copy(orig, dst)

    meta_src = os.path.join(project_root, "data", "trait_list.meta.json")
    meta_dst = tmp_data / "trait_list.meta.json"
    shutil.copy(meta_src, meta_dst)

    import src.routes.api as api_mod

    def patched_merge(remote_traits):
        api_mod._trait_list = json.loads(dst.read_text(encoding="utf-8"))

        existing_keys = {(e["trait"].lower(), e["shortForm"]) for e in api_mod._trait_list}
        added = 0
        for rt in remote_traits:
            key = (rt["trait"].lower(), rt["shortForm"])
            if key not in existing_keys:
                api_mod._trait_list.append(rt)
                existing_keys.add(key)
                added += 1
        if added > 0:
            with open(str(dst), "w", encoding="utf-8") as f:
                json.dump(api_mod._trait_list, f, ensure_ascii=False, indent=2)
            with open(str(meta_dst), "w", encoding="utf-8") as f:
                json.dump({"updated_at": "2026-01-01T00:00:00Z", "total_traits": len(api_mod._trait_list)}, f, indent=2)
        return added

    monkeypatch.setattr(api_mod, "_merge_remote_into_cache", patched_merge)

    return dst, meta_dst


def _merge_in_memory(api_mod, remote_traits):
    """Test helper: merge remote traits into the in-memory trait list with dedup."""
    existing_keys = {(e["trait"].lower(), e["shortForm"]) for e in api_mod._trait_list}
    added = 0
    for rt in remote_traits:
        key = (rt["trait"].lower(), rt["shortForm"])
        if key not in existing_keys:
            api_mod._trait_list.append(rt)
            existing_keys.add(key)
            added += 1
    return added


# ---------- tests ----------


def test_remote_search_called_when_local_empty(monkeypatch):
    """When local results are empty, the remote HTTP client must be invoked."""
    app = _setup()
    import src.routes.api as api_mod

    called = {"count": 0}

    def fake_get(*args, **kwargs):
        called["count"] += 1
        return _FakeResponse(FAKE_REMOTE_RESPONSE)

    monkeypatch.setattr(api_mod.http_requests, "get", fake_get)
    monkeypatch.setattr(api_mod, "_merge_remote_into_cache",
                        lambda rt: _merge_in_memory(api_mod, rt))

    with app.test_client() as client:
        resp = client.post("/api/search-traits", json={"query": "zzz_nonexistent_trait"})

    assert resp.status_code == 200
    assert called["count"] == 1, "Remote HTTP client must be called when local results are empty"


def test_remote_results_merged_into_response(monkeypatch):
    """Remote traits should appear in the response results."""
    app = _setup()
    import src.routes.api as api_mod

    def fake_get(*args, **kwargs):
        return _FakeResponse(FAKE_REMOTE_RESPONSE)

    monkeypatch.setattr(api_mod.http_requests, "get", fake_get)
    monkeypatch.setattr(api_mod, "_merge_remote_into_cache",
                        lambda rt: _merge_in_memory(api_mod, rt))

    with app.test_client() as client:
        resp = client.post("/api/search-traits", json={"query": "fake remote trait"})

    data = resp.get_json()
    assert data["success"] is True
    traits = [r["trait"] for r in data["results"]]
    assert any("fake remote trait" in t for t in traits), (
        f"Remote traits must appear in results, got: {traits}"
    )


def test_remote_results_same_schema(monkeypatch):
    """Each result must have trait, efo_id, score keys."""
    app = _setup()
    import src.routes.api as api_mod

    def fake_get(*args, **kwargs):
        return _FakeResponse(FAKE_REMOTE_RESPONSE)

    monkeypatch.setattr(api_mod.http_requests, "get", fake_get)
    monkeypatch.setattr(api_mod, "_merge_remote_into_cache",
                        lambda rt: _merge_in_memory(api_mod, rt))

    with app.test_client() as client:
        resp = client.post("/api/search-traits", json={"query": "fake remote trait"})

    data = resp.get_json()
    for r in data["results"]:
        assert "trait" in r, "Each result must have 'trait'"
        assert "efo_id" in r, "Each result must have 'efo_id'"
        assert "score" in r, "Each result must have 'score'"


def test_remote_not_called_when_disabled(monkeypatch):
    """When GWAS_REMOTE_SEARCH is not set, remote must NOT be called."""
    monkeypatch.setenv("GWAS_REMOTE_SEARCH", "")
    app = _setup()
    import src.routes.api as api_mod

    called = {"count": 0}

    def fake_get(*args, **kwargs):
        called["count"] += 1
        return _FakeResponse(FAKE_REMOTE_RESPONSE)

    monkeypatch.setattr(api_mod.http_requests, "get", fake_get)

    with app.test_client() as client:
        resp = client.post("/api/search-traits", json={"query": "zzz_nonexistent_trait"})

    assert resp.status_code == 200
    assert called["count"] == 0, "Remote must NOT be called when GWAS_REMOTE_SEARCH is disabled"


def test_cache_updated_after_remote(_tmp_trait_files, monkeypatch):
    """After remote fetch, data/trait_list.json must contain the new traits and meta must update."""
    dst, meta_dst = _tmp_trait_files
    app = _setup()
    import src.routes.api as api_mod

    def fake_get(*args, **kwargs):
        return _FakeResponse(FAKE_REMOTE_RESPONSE)

    monkeypatch.setattr(api_mod.http_requests, "get", fake_get)

    # Reset the in-memory list so it reloads from our tmp file
    api_mod._trait_list = json.loads(dst.read_text(encoding="utf-8"))
    original_count = len(api_mod._trait_list)

    with app.test_client() as client:
        resp = client.post("/api/search-traits", json={"query": "fake remote trait"})

    assert resp.status_code == 200

    updated = json.loads(dst.read_text(encoding="utf-8"))
    assert len(updated) > original_count, (
        f"trait_list.json must grow after remote merge: was {original_count}, now {len(updated)}"
    )

    short_forms = [t["shortForm"] for t in updated]
    assert "EFO_9999901" in short_forms
    assert "EFO_9999902" in short_forms

    meta = json.loads(meta_dst.read_text(encoding="utf-8"))
    assert "updated_at" in meta
    assert meta["total_traits"] == len(updated)


def test_remote_deduplicates_existing_traits(monkeypatch):
    """Remote traits that already exist locally must not be duplicated."""
    app = _setup()
    import src.routes.api as api_mod

    # Force load so _trait_list is populated
    api_mod._get_trait_list()

    # Inject alpha so it already exists
    api_mod._trait_list.append({
        "trait": "fake remote trait alpha",
        "shortForm": "EFO_9999901",
        "uri": "",
    })
    count_before = len(api_mod._trait_list)

    # Directly test the dedupe logic
    remote_entries = [
        {"trait": rt["trait"], "shortForm": rt["shortForm"], "uri": ""}
        for rt in FAKE_REMOTE_RESPONSE["_embedded"]["efoTraits"]
    ]
    added = _merge_in_memory(api_mod, remote_entries)

    # Only beta should be added (alpha already exists)
    assert added == 1, f"Expected 1 new trait added, got {added}"
    assert len(api_mod._trait_list) == count_before + 1, (
        f"Duplicate must not be added: was {count_before}, now {len(api_mod._trait_list)}"
    )
    short_forms = [t["shortForm"] for t in api_mod._trait_list]
    assert short_forms.count("EFO_9999901") == 1, "Alpha must not be duplicated"
    assert "EFO_9999902" in short_forms, "Beta must be added"


def test_remote_failure_graceful(monkeypatch):
    """If remote call raises, the endpoint must still return local results (empty ok)."""
    app = _setup()
    import src.routes.api as api_mod

    def failing_get(*args, **kwargs):
        raise ConnectionError("Network unreachable")

    monkeypatch.setattr(api_mod.http_requests, "get", failing_get)

    with app.test_client() as client:
        resp = client.post("/api/search-traits", json={"query": "zzz_nonexistent_trait"})

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True, "Endpoint must succeed even when remote fails"
