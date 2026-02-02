"""Contract tests for C9.B1: GWAS Cache Directory Override (Persist Across Versions).

Validates:
1. GWAS_CACHE_DIR set → load/save use that directory.
2. GWAS_CACHE_DIR unset → legacy behavior via config.gwas_cache_directory.
3. GWAS_CACHE_DIR set + empty config → still uses env dir.
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone

import pandas as pd
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GWAS_PKG = os.path.join(PROJECT_ROOT, "gwas_variant_analyzer")

if GWAS_PKG not in sys.path:
    sys.path.insert(0, GWAS_PKG)

from gwas_variant_analyzer.gwas_catalog_handler import (  # noqa: E402
    load_gwas_data_from_cache,
    save_gwas_data_to_cache,
)


@pytest.fixture(autouse=True)
def _clean_env():
    """Ensure GWAS_CACHE_DIR is clean between tests."""
    old = os.environ.pop("GWAS_CACHE_DIR", None)
    yield
    if old is not None:
        os.environ["GWAS_CACHE_DIR"] = old
    else:
        os.environ.pop("GWAS_CACHE_DIR", None)


def _write_cache(cache_abs, efo_id, df):
    """Write parquet + meta to a cache directory."""
    os.makedirs(cache_abs, exist_ok=True)
    df.to_parquet(os.path.join(cache_abs, f"{efo_id}.parquet"), index=False)
    meta = {
        "efo_id": efo_id,
        "trait": "Test",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "association_count": len(df),
    }
    with open(os.path.join(cache_abs, f"{efo_id}.meta.json"), "w") as f:
        json.dump(meta, f)


# ---------- GWAS_CACHE_DIR set → uses env dir ----------


def test_load_uses_env_cache_dir(tmp_path):
    """With GWAS_CACHE_DIR set, load reads from that directory."""
    env_dir = str(tmp_path / "shared_cache")
    os.environ["GWAS_CACHE_DIR"] = env_dir
    efo_id = "EFO_TEST_ENV"
    df = pd.DataFrame([{"SNP_ID": "rs1", "GWAS_Trait": "Obesity"}])
    _write_cache(env_dir, efo_id, df)

    config = {"gwas_cache_directory": "data/gwas_cache", "gwas_cache_expiry_days": 90}
    result = load_gwas_data_from_cache(efo_id, config)
    assert result is not None
    assert not result.empty


def test_save_uses_env_cache_dir(tmp_path):
    """With GWAS_CACHE_DIR set, save writes to that directory."""
    env_dir = str(tmp_path / "shared_cache")
    os.environ["GWAS_CACHE_DIR"] = env_dir
    efo_id = "EFO_TEST_SAVE_ENV"
    df = pd.DataFrame([{"SNP_ID": "rs1", "GWAS_Trait": "Diabetes"}])

    config = {"gwas_cache_directory": "data/gwas_cache", "gwas_cache_expiry_days": 90}
    save_gwas_data_to_cache(df, efo_id, config)

    assert os.path.exists(os.path.join(env_dir, f"{efo_id}.parquet"))
    assert os.path.exists(os.path.join(env_dir, f"{efo_id}.meta.json"))


def test_env_override_ignores_config(tmp_path):
    """GWAS_CACHE_DIR takes precedence even with empty config."""
    env_dir = str(tmp_path / "shared_cache")
    os.environ["GWAS_CACHE_DIR"] = env_dir
    efo_id = "EFO_OVERRIDE"
    df = pd.DataFrame([{"SNP_ID": "rs1", "GWAS_Trait": "Test"}])
    _write_cache(env_dir, efo_id, df)

    config = {"gwas_cache_directory": "", "gwas_cache_expiry_days": 90}
    result = load_gwas_data_from_cache(efo_id, config)
    assert result is not None


# ---------- GWAS_CACHE_DIR unset → legacy behavior ----------


def test_load_legacy_without_env():
    """Without GWAS_CACHE_DIR, load uses config.gwas_cache_directory."""
    os.environ.pop("GWAS_CACHE_DIR", None)
    efo_id = "EFO_LEGACY"
    cache_rel = f"data/_contract_cache_{uuid.uuid4().hex}"
    cache_abs = os.path.join(PROJECT_ROOT, cache_rel)
    df = pd.DataFrame([{"SNP_ID": "rs1", "GWAS_Trait": "Legacy"}])
    _write_cache(cache_abs, efo_id, df)

    config = {"gwas_cache_directory": cache_rel, "gwas_cache_expiry_days": 90}
    result = load_gwas_data_from_cache(efo_id, config)
    assert result is not None
    assert not result.empty


def test_save_legacy_without_env():
    """Without GWAS_CACHE_DIR, save uses config.gwas_cache_directory."""
    os.environ.pop("GWAS_CACHE_DIR", None)
    efo_id = "EFO_SAVE_LEGACY"
    cache_rel = f"data/_contract_cache_{uuid.uuid4().hex}"
    cache_abs = os.path.join(PROJECT_ROOT, cache_rel)

    config = {"gwas_cache_directory": cache_rel, "gwas_cache_expiry_days": 90}
    df = pd.DataFrame([{"SNP_ID": "rs1", "GWAS_Trait": "Legacy Save"}])
    save_gwas_data_to_cache(df, efo_id, config)

    assert os.path.exists(os.path.join(cache_abs, f"{efo_id}.parquet"))
