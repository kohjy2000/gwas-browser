"""Contract tests for UI_Panels_ClinVar_PGx_v1.

Validates that index.html contains the required tab system DOM IDs,
visibility gating, result containers, and run buttons.
"""

import os
import re


def _read_index_html() -> str:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    html_path = os.path.join(
        project_root, "gwas_dashboard_package", "src", "static", "index.html"
    )
    assert os.path.exists(html_path), f"index.html not found: {html_path}"
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


def test_tab_buttons_exist():
    html = _read_index_html()
    for tab_id in ("tab-gwas", "tab-clinvar", "tab-pgx", "tab-chat"):
        assert f'id="{tab_id}"' in html, f"Missing tab button: {tab_id}"


def test_panels_exist():
    html = _read_index_html()
    for panel_id in ("panel-gwas", "panel-clinvar", "panel-pgx", "panel-chat"):
        assert f'id="{panel_id}"' in html, f"Missing panel: {panel_id}"


def test_result_containers_exist():
    html = _read_index_html()
    assert 'id="clinvar-results"' in html, "Missing clinvar-results container"
    assert 'id="pgx-results"' in html, "Missing pgx-results container"


def test_run_buttons_exist():
    html = _read_index_html()
    assert 'id="run-clinvar-btn"' in html, "Missing run-clinvar-btn"
    assert 'id="run-pgx-btn"' in html, "Missing run-pgx-btn"


def test_clinvar_pgx_chat_tabs_disabled_before_upload():
    """Before upload, tab-clinvar/tab-pgx/tab-chat must be disabled."""
    html = _read_index_html()
    for tab_id in ("tab-clinvar", "tab-pgx", "tab-chat"):
        pattern = rf'id="{tab_id}"[^>]*disabled'
        assert re.search(pattern, html), (
            f"{tab_id} must be disabled in initial HTML"
        )


def test_upload_first_message_present():
    """ClinVar/PGx/Chat panels must show an 'upload first' message."""
    html = _read_index_html()
    lower = html.lower()
    assert "upload" in lower and "first" in lower, (
        "Must contain an 'upload first' message for gated tabs"
    )


def test_js_enables_tabs_after_upload():
    """JS must contain logic to enable tabs after upload succeeds."""
    html = _read_index_html()
    assert "enablePostUploadTabs" in html or "disabled = false" in html or "disabled=false" in html, (
        "JS must enable tabs after upload"
    )


def test_js_calls_clinvar_match_endpoint():
    """JS must call /api/clinvar-match."""
    html = _read_index_html()
    assert "/api/clinvar-match" in html, "JS must call /api/clinvar-match"


def test_js_calls_pgx_summary_endpoint():
    """JS must call /api/pgx-summary."""
    html = _read_index_html()
    assert "/api/pgx-summary" in html, "JS must call /api/pgx-summary"


def test_results_rendered_to_page():
    """Results must be rendered into clinvar-results and pgx-results containers."""
    html = _read_index_html()
    assert "clinvar-results" in html, "Must render into clinvar-results"
    assert "pgx-results" in html, "Must render into pgx-results"
    assert "innerHTML" in html, "Must use innerHTML to render results to page"
