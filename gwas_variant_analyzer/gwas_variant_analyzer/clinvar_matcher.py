from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


def _normalize_chrom(chrom: str) -> str:
    c = (chrom or "").strip()
    if c.lower().startswith("chr"):
        c = c[3:]
    return c


def _normalize_allele(allele: str) -> str:
    return (allele or "").strip().upper()


def _primary_key(chrom: str, pos: int, ref: str, alt: str) -> str:
    return f"{_normalize_chrom(chrom)}-{int(pos)}-{_normalize_allele(ref)}-{_normalize_allele(alt)}"


def _chrom_sort_key(chrom: str) -> tuple[int, str]:
    c = _normalize_chrom(chrom)
    try:
        return (0, f"{int(c):09d}")
    except Exception:
        return (1, c.upper())


@dataclass(frozen=True)
class ClinVarMatch:
    match_type: str  # "primary" or "rsid"
    match_key: str
    user_chrom: str
    user_pos: int
    user_ref: str
    user_alt: str
    user_rsid: str | None
    clinvar: dict


def load_clinvar_toy_tsv(tsv_path: str | Path) -> pd.DataFrame:
    path = Path(tsv_path)
    rows: list[dict] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            rows.append(r)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    if "pos" in df.columns:
        df["pos"] = pd.to_numeric(df["pos"], errors="coerce").astype("Int64")
    return df


def match_user_variants_to_clinvar(
    user_variants_df: pd.DataFrame,
    clinvar_tsv_path: str | Path,
    significance_filter: Optional[Iterable[str]] = None,
) -> list[dict]:
    if significance_filter is None:
        significance_filter = ("pathogenic", "likely_pathogenic")
    allowed = {str(s).strip().lower() for s in significance_filter}

    clinvar_df = load_clinvar_toy_tsv(clinvar_tsv_path)
    if clinvar_df is None or clinvar_df.empty:
        return []

    required_cols = {"chrom", "pos", "ref", "alt", "clinical_significance", "rsid"}
    missing = required_cols - set(clinvar_df.columns)
    if missing:
        raise ValueError(f"ClinVar TSV missing columns: {sorted(missing)}")

    filtered = clinvar_df.copy()
    filtered["clinical_significance"] = filtered["clinical_significance"].astype(str)
    filtered = filtered[filtered["clinical_significance"].str.lower().isin(allowed)]

    filtered = filtered.copy()
    filtered["_match_key"] = filtered.apply(
        lambda r: _primary_key(str(r["chrom"]), int(r["pos"]), str(r["ref"]), str(r["alt"])),
        axis=1,
    )
    filtered["_rsid_norm"] = filtered["rsid"].astype(str).str.strip().str.lower()
    filtered = filtered.sort_values(
        by=["_match_key", "_rsid_norm"], kind="mergesort"
    ).reset_index(drop=True)

    key_to_row: dict[str, dict] = {}
    rsid_to_row: dict[str, dict] = {}
    for _, row in filtered.iterrows():
        row_dict = row.drop(labels=["_match_key", "_rsid_norm"]).to_dict()
        mk = str(row["_match_key"])
        rk = str(row["_rsid_norm"])
        if mk not in key_to_row:
            key_to_row[mk] = row_dict
        if rk and rk != "nan" and rk not in rsid_to_row:
            rsid_to_row[rk] = row_dict

    if user_variants_df is None or user_variants_df.empty:
        return []

    matches: list[ClinVarMatch] = []

    for idx, u in user_variants_df.reset_index(drop=True).iterrows():
        chrom = str(u.get("USER_CHROM", ""))
        pos = u.get("USER_POS")
        ref = str(u.get("USER_REF", ""))
        alt = str(u.get("USER_ALT", ""))
        rsid = u.get("SNP_ID")

        if pos is None:
            continue
        try:
            pos_int = int(pos)
        except Exception:
            continue

        mk = _primary_key(chrom, pos_int, ref, alt)
        hit = key_to_row.get(mk)
        if hit is not None:
            matches.append(
                ClinVarMatch(
                    match_type="primary",
                    match_key=mk,
                    user_chrom=_normalize_chrom(chrom),
                    user_pos=pos_int,
                    user_ref=_normalize_allele(ref),
                    user_alt=_normalize_allele(alt),
                    user_rsid=str(rsid) if isinstance(rsid, str) else None,
                    clinvar=hit,
                )
            )
            continue

        if rsid and isinstance(rsid, str) and rsid.lower().startswith("rs"):
            rk = rsid.strip().lower()
            hit = rsid_to_row.get(rk)
            if hit is not None:
                matches.append(
                    ClinVarMatch(
                        match_type="rsid",
                        match_key=mk,
                        user_chrom=_normalize_chrom(chrom),
                        user_pos=pos_int,
                        user_ref=_normalize_allele(ref),
                        user_alt=_normalize_allele(alt),
                        user_rsid=rsid.strip(),
                        clinvar=hit,
                    )
                )

    matches_sorted = sorted(
        matches,
        key=lambda m: (
            _chrom_sort_key(m.user_chrom),
            int(m.user_pos),
            m.match_key,
            0 if m.match_type == "primary" else 1,
        ),
    )

    out: list[dict] = []
    for m in matches_sorted:
        d = {
            "match_type": m.match_type,
            "match_key": m.match_key,
            "user_chrom": m.user_chrom,
            "user_pos": m.user_pos,
            "user_ref": m.user_ref,
            "user_alt": m.user_alt,
            "user_rsid": m.user_rsid,
        }
        d.update(m.clinvar)
        out.append(d)
    return out
