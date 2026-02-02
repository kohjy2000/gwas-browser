import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

import pandas as pd


def _import_cache_fns():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    gwas_pkg_parent = os.path.join(project_root, "gwas_variant_analyzer")
    if gwas_pkg_parent not in sys.path:
        sys.path.insert(0, gwas_pkg_parent)

    from gwas_variant_analyzer.gwas_catalog_handler import (  # noqa: E402
        load_gwas_data_from_cache,
        save_gwas_data_to_cache,
    )

    return load_gwas_data_from_cache, save_gwas_data_to_cache, project_root


def _make_rel_cache_dir(project_root: str) -> tuple[str, str]:
    cache_rel = f"data/_contract_cache_{uuid.uuid4().hex}"
    cache_abs = os.path.join(project_root, cache_rel)
    os.makedirs(cache_abs, exist_ok=True)
    return cache_rel, cache_abs


def test_cache_contract_legacy_parquet_without_meta_loads():
    load_gwas_data_from_cache, _, project_root = _import_cache_fns()
    cache_rel, cache_abs = _make_rel_cache_dir(project_root)

    efo_id = "EFO_TEST_LEGACY"
    df = pd.DataFrame([{"SNP_ID": "rs1", "GWAS_Trait": "Trait A"}])
    df.to_parquet(os.path.join(cache_abs, f"{efo_id}.parquet"), index=False)

    config = {"gwas_cache_directory": cache_rel, "gwas_cache_expiry_days": 1}
    loaded = load_gwas_data_from_cache(efo_id, config)
    assert loaded is not None
    assert not loaded.empty


def test_cache_contract_recent_meta_loads():
    load_gwas_data_from_cache, _, project_root = _import_cache_fns()
    cache_rel, cache_abs = _make_rel_cache_dir(project_root)

    efo_id = "EFO_TEST_RECENT"
    df = pd.DataFrame([{"SNP_ID": "rs1", "GWAS_Trait": "Trait A"}])
    df.to_parquet(os.path.join(cache_abs, f"{efo_id}.parquet"), index=False)

    meta = {
        "efo_id": efo_id,
        "trait": "Trait A",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "association_count": len(df),
    }
    with open(os.path.join(cache_abs, f"{efo_id}.meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    config = {"gwas_cache_directory": cache_rel, "gwas_cache_expiry_days": 90}
    loaded = load_gwas_data_from_cache(efo_id, config)
    assert loaded is not None
    assert not loaded.empty


def test_cache_contract_expired_meta_returns_none():
    load_gwas_data_from_cache, _, project_root = _import_cache_fns()
    cache_rel, cache_abs = _make_rel_cache_dir(project_root)

    efo_id = "EFO_TEST_EXPIRED"
    df = pd.DataFrame([{"SNP_ID": "rs1", "GWAS_Trait": "Trait A"}])
    df.to_parquet(os.path.join(cache_abs, f"{efo_id}.parquet"), index=False)

    old = datetime.now(timezone.utc) - timedelta(days=10)
    meta = {
        "efo_id": efo_id,
        "trait": "Trait A",
        "fetched_at": old.isoformat(),
        "association_count": len(df),
    }
    with open(os.path.join(cache_abs, f"{efo_id}.meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    config = {"gwas_cache_directory": cache_rel, "gwas_cache_expiry_days": 1}
    loaded = load_gwas_data_from_cache(efo_id, config)
    assert loaded is None


def test_cache_contract_save_writes_meta_json():
    _, save_gwas_data_to_cache, project_root = _import_cache_fns()
    cache_rel, cache_abs = _make_rel_cache_dir(project_root)

    efo_id = "EFO_TEST_SAVE"
    df = pd.DataFrame(
        [
            {"SNP_ID": "rs1", "GWAS_Trait": "Trait Save"},
            {"SNP_ID": "rs2", "GWAS_Trait": "Trait Save"},
        ]
    )

    config = {"gwas_cache_directory": cache_rel, "gwas_cache_expiry_days": 90}
    save_gwas_data_to_cache(df, efo_id, config)

    meta_path = os.path.join(cache_abs, f"{efo_id}.meta.json")
    assert os.path.exists(meta_path)

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["efo_id"] == efo_id
    assert meta["trait"] == "Trait Save"
    assert isinstance(meta["fetched_at"], str) and meta["fetched_at"]
    assert meta["association_count"] == len(df)

