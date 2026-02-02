"""Contract tests for C8.B3: GWAS Cache Self-Heal for PubMed (Stale If Missing).

Validates:
1. GWAS_CACHE_REQUIRE_PUBMED=1 + missing PubMed_ID column → returns None.
2. GWAS_CACHE_REQUIRE_PUBMED=1 + all-empty PubMed_ID → returns None.
3. GWAS_CACHE_REQUIRE_PUBMED=1 + valid PubMed_ID present → loads normally.
4. Env var unset → legacy behavior (loads even without PubMed_ID).
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

from gwas_variant_analyzer.gwas_catalog_handler import load_gwas_data_from_cache  # noqa: E402


def _make_cache(project_root, df, efo_id="EFO_PUBMED_TEST"):
    """Create a temp cache dir with parquet + valid meta."""
    cache_rel = f"data/_contract_cache_{uuid.uuid4().hex}"
    cache_abs = os.path.join(project_root, cache_rel)
    os.makedirs(cache_abs, exist_ok=True)

    df.to_parquet(os.path.join(cache_abs, f"{efo_id}.parquet"), index=False)

    meta = {
        "efo_id": efo_id,
        "trait": "Test Trait",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "association_count": len(df),
    }
    with open(os.path.join(cache_abs, f"{efo_id}.meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f)

    return cache_rel, efo_id


@pytest.fixture(autouse=True)
def _clean_env():
    """Ensure GWAS_CACHE_REQUIRE_PUBMED is clean between tests."""
    old = os.environ.pop("GWAS_CACHE_REQUIRE_PUBMED", None)
    yield
    if old is not None:
        os.environ["GWAS_CACHE_REQUIRE_PUBMED"] = old
    else:
        os.environ.pop("GWAS_CACHE_REQUIRE_PUBMED", None)


# ---------- Self-heal ON ----------


def test_selfheal_missing_pubmed_column_returns_none():
    """With GWAS_CACHE_REQUIRE_PUBMED=1, no PubMed_ID column → None."""
    os.environ["GWAS_CACHE_REQUIRE_PUBMED"] = "1"
    df = pd.DataFrame([{"SNP_ID": "rs1", "GWAS_Trait": "Obesity"}])
    cache_rel, efo_id = _make_cache(PROJECT_ROOT, df)

    config = {"gwas_cache_directory": cache_rel, "gwas_cache_expiry_days": 90}
    result = load_gwas_data_from_cache(efo_id, config)
    assert result is None


def test_selfheal_all_empty_pubmed_returns_none():
    """With GWAS_CACHE_REQUIRE_PUBMED=1, all PubMed_ID empty → None."""
    os.environ["GWAS_CACHE_REQUIRE_PUBMED"] = "1"
    df = pd.DataFrame([
        {"SNP_ID": "rs1", "PubMed_ID": None},
        {"SNP_ID": "rs2", "PubMed_ID": ""},
        {"SNP_ID": "rs3", "PubMed_ID": "  "},
    ])
    cache_rel, efo_id = _make_cache(PROJECT_ROOT, df)

    config = {"gwas_cache_directory": cache_rel, "gwas_cache_expiry_days": 90}
    result = load_gwas_data_from_cache(efo_id, config)
    assert result is None


def test_selfheal_valid_pubmed_loads():
    """With GWAS_CACHE_REQUIRE_PUBMED=1, at least one valid PubMed_ID → loads."""
    os.environ["GWAS_CACHE_REQUIRE_PUBMED"] = "1"
    df = pd.DataFrame([
        {"SNP_ID": "rs1", "PubMed_ID": "29878757"},
        {"SNP_ID": "rs2", "PubMed_ID": None},
    ])
    cache_rel, efo_id = _make_cache(PROJECT_ROOT, df)

    config = {"gwas_cache_directory": cache_rel, "gwas_cache_expiry_days": 90}
    result = load_gwas_data_from_cache(efo_id, config)
    assert result is not None
    assert not result.empty


# ---------- Self-heal OFF (default) ----------


def test_legacy_no_pubmed_still_loads():
    """Without GWAS_CACHE_REQUIRE_PUBMED, missing PubMed_ID still loads."""
    os.environ.pop("GWAS_CACHE_REQUIRE_PUBMED", None)
    df = pd.DataFrame([{"SNP_ID": "rs1", "GWAS_Trait": "Obesity"}])
    cache_rel, efo_id = _make_cache(PROJECT_ROOT, df)

    config = {"gwas_cache_directory": cache_rel, "gwas_cache_expiry_days": 90}
    result = load_gwas_data_from_cache(efo_id, config)
    assert result is not None
    assert not result.empty


def test_legacy_all_empty_pubmed_still_loads():
    """Without GWAS_CACHE_REQUIRE_PUBMED, all-empty PubMed_ID still loads."""
    os.environ.pop("GWAS_CACHE_REQUIRE_PUBMED", None)
    df = pd.DataFrame([
        {"SNP_ID": "rs1", "PubMed_ID": None},
        {"SNP_ID": "rs2", "PubMed_ID": ""},
    ])
    cache_rel, efo_id = _make_cache(PROJECT_ROOT, df)

    config = {"gwas_cache_directory": cache_rel, "gwas_cache_expiry_days": 90}
    result = load_gwas_data_from_cache(efo_id, config)
    assert result is not None
    assert not result.empty
