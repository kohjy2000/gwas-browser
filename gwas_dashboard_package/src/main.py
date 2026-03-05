"""
Main entry point for the GWAS Variant Analyzer Dashboard Flask application.
"""

from __future__ import annotations

import logging
import os
import sys
import glob

from flask import Flask, jsonify, render_template, send_from_directory
from flask_cors import CORS  # Added

# --- Production environment detection ---
_IS_PRODUCTION = os.environ.get("RENDER") == "true" or os.environ.get("IS_PRODUCTION") == "1"

# Enable remote GWAS trait search by default (moved outside __main__ for gunicorn)
if not os.environ.get("GWAS_REMOTE_SEARCH"):
    os.environ["GWAS_REMOTE_SEARCH"] = "1"

# --- ai_workflow: optional local env auto-load (no manual exports) ---

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

def _load_env_file(path: str) -> None:
    """
    Minimal .env loader.

    - Ignores blank lines and comments (# ...)
    - Supports KEY=VALUE (optionally quoted)
    - Only sets variables that are not already set in os.environ
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        # Never crash app startup due to env file parsing
        return


def _auto_load_ai_workflow_env() -> None:
    """Load ai_workflow env defaults if present (opt-in via file existence)."""
    candidates = [
        os.path.join(_PROJECT_ROOT, "ai_workflow", ".env.local"),
        os.path.join(_PROJECT_ROOT, ".env"),
    ]
    for p in candidates:
        if os.path.exists(p):
            _load_env_file(p)
            break


# Load early so later imports can see env vars if they want to
_auto_load_ai_workflow_env()

# Import blueprints
try:
    from .routes.api import api_bp
except Exception:  # pragma: no cover - script-mode fallback
    # Allows running: `python gwas_dashboard_package/src/main.py`
    _dash_pkg = os.path.dirname(os.path.dirname(__file__))  # gwas_dashboard_package/
    sys.path.insert(0, _dash_pkg)
    # Ensure gwas_variant_analyzer package is importable
    _this_project = os.path.dirname(_dash_pkg)  # ver_260201_.../
    _gwas_pkg_parent = os.path.join(_this_project, "gwas_variant_analyzer")
    if _gwas_pkg_parent not in sys.path:
        sys.path.insert(0, _gwas_pkg_parent)
    from src.routes.api import api_bp  # noqa: E402

# Create Flask app
app = Flask(__name__, static_folder='static', template_folder='static')
CORS(app)  # Added: Enable CORS

# Set file size limit: 50MB in production, 300MB locally
if _IS_PRODUCTION:
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
else:
    app.config['MAX_CONTENT_LENGTH'] = 300 * 1024 * 1024

# Configure logging
if _IS_PRODUCTION:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
    )
else:
    os.makedirs(os.path.join(_PROJECT_ROOT, "logs"), exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(_PROJECT_ROOT, "logs", "app.log")),
            logging.StreamHandler()
        ]
    )

# Register blueprints
app.register_blueprint(api_bp, url_prefix='/api')

# Health check endpoint (for Render)
@app.route('/health')
def health():
    return jsonify({"status": "ok"})

# Serve static files
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return {"error": "Not found", "message": str(e)}, 404

@app.errorhandler(500)
def internal_server_error(e):
    return {"error": "Internal server error", "message": str(e)}, 500

# Run the app
if __name__ == '__main__':
    # Ensure the GWAS Variant Analyzer package is in the path
    gwas_package_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'gwas_variant_analyzer'))
    if os.path.exists(gwas_package_path):
        sys.path.append(os.path.dirname(gwas_package_path))
        app.logger.info(f"Added GWAS Variant Analyzer package to path: {gwas_package_path}")
    
    # Create config directory if it doesn't exist
    config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
    os.makedirs(config_dir, exist_ok=True)
    
    # Copy config files from GWAS Variant Analyzer package if they don't exist
    src_config_dir = os.path.join(gwas_package_path, 'config')
    if os.path.exists(src_config_dir):
        for config_file in os.listdir(src_config_dir):
            src_file = os.path.join(src_config_dir, config_file)
            dst_file = os.path.join(config_dir, config_file)
            if not os.path.exists(dst_file) and os.path.isfile(src_file):
                import shutil
                shutil.copy2(src_file, dst_file)
                app.logger.info(f"Copied config file: {config_file}")
    
    # Auto-detect Ollama for chat LLM mode
    if not os.environ.get("OLLAMA_HOST"):
        try:
            import requests as _req
            _r = _req.get("http://127.0.0.1:11434/api/tags", timeout=2)
            if _r.status_code == 200:
                os.environ["OLLAMA_HOST"] = "http://127.0.0.1:11434"
                models = [m["name"] for m in _r.json().get("models", [])]
                if not os.environ.get("OLLAMA_MODEL_CHAT"):
                    preferred = ["deepseek-r1:32b", "llama3.1:8b-instruct", "qwen2.5:7b-instruct"]
                    chosen = next((p for p in preferred if p in models), models[0] if models else "")
                    if chosen:
                        os.environ["OLLAMA_MODEL_CHAT"] = chosen
                app.logger.info(f"Ollama auto-detected: host=127.0.0.1:11434, model={os.environ.get('OLLAMA_MODEL_CHAT', 'none')}")
        except Exception:
            pass

    # Optional: seed GWAS cache into this project if it's empty (prevents re-fetching everything).
    def _seed_gwas_cache_if_empty() -> None:
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        dst_cache = os.path.join(project_root, "data", "gwas_cache")
        try:
            os.makedirs(dst_cache, exist_ok=True)
            if any(p.endswith(".parquet") for p in os.listdir(dst_cache)):
                return

            # 1) explicit seed dir
            seed_dir = os.environ.get("GWAS_CACHE_SEED_DIR", "").strip()
            if seed_dir and os.path.isdir(seed_dir):
                src_cache = seed_dir
            else:
                # 2) auto-detect best candidate among sibling project versions
                parent = os.path.abspath(os.path.join(project_root, ".."))
                candidates = []
                for p in glob.glob(os.path.join(parent, "ver_*", "data", "gwas_cache")):
                    p_abs = os.path.abspath(p)
                    if p_abs == os.path.abspath(dst_cache):
                        continue
                    n = len(glob.glob(os.path.join(p_abs, "*.parquet")))
                    if n > 0:
                        candidates.append((n, p_abs))
                if not candidates:
                    return
                candidates.sort(reverse=True)
                src_cache = candidates[0][1]

            copied = 0
            for pattern in ("*.parquet", "*.meta.json"):
                for src in glob.glob(os.path.join(src_cache, pattern)):
                    dst = os.path.join(dst_cache, os.path.basename(src))
                    if os.path.exists(dst):
                        continue
                    try:
                        import shutil

                        shutil.copy2(src, dst)
                        copied += 1
                    except Exception:
                        continue

            if copied:
                app.logger.info(f"Seeded GWAS cache: copied {copied} files from {src_cache} -> {dst_cache}")
        except Exception:
            return

    _seed_gwas_cache_if_empty()

    # Optional: auto-detect local ForeGenomics report if user didn't set it.
    if not os.environ.get("FOREGENOMICS_PGX_REPORT_PATH"):
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            trial_dir = os.path.abspath(os.path.join(project_root, "..", "ForeGenomics_PGx", "trial"))
            cands = sorted(glob.glob(os.path.join(trial_dir, "*", "*.PGx.out.report.tsv")))
            if cands:
                os.environ["FOREGENOMICS_PGX_REPORT_PATH"] = cands[0]
        except Exception:
            pass

    # Run the app
    app.run(host='0.0.0.0', port=1111, debug=True)
