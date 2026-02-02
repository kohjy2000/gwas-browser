import os
import sys


def _import_parser():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    gwas_pkg_parent = os.path.join(project_root, "gwas_variant_analyzer")
    if gwas_pkg_parent not in sys.path:
        sys.path.insert(0, gwas_pkg_parent)

    import gwas_variant_analyzer.gwas_catalog_handler as h  # noqa: E402

    return h


def test_reference_fix_contract_fills_pubmed_and_sets_association_id(monkeypatch):
    h = _import_parser()

    # Avoid hitting Ensembl
    monkeypatch.setattr(
        h,
        "_fetch_snp_locations_from_ensembl",
        lambda rsids, config: {"rs123": {"chrom": "1", "pos": 100}},
    )

    calls = {"count": 0}

    def _fake_get(url, timeout=None):
        calls["count"] += 1

        class _Resp:
            def raise_for_status(self):
                return None

            def json(self):
                return {"publicationInfo": {"pubmedId": "99999999"}}

        return _Resp()

    monkeypatch.setattr(h.requests, "get", _fake_get)

    raw = [
        {
            "associationId": "A1",
            "publicationInfo": {"pubmedId": None},
            "_links": {"study": {"href": "https://example.org/studies/1"}, "self": {"href": "https://example.org/a/A1"}},
            "pvalue": "5e-8",
            "orPerCopyNum": "1.2",
            "loci": [{"strongestRiskAlleles": [{"riskAlleleName": "rs123-A"}]}],
            "ancestries": {},
        }
    ]

    config = {
        "gwas_api_request_timeout_seconds": 5,
        "gwas_api_max_retries": 1,
        "gwas_api_retry_delay_seconds": 0,
        "study_fetch_rate_limit_per_second": 1000,
    }

    df = h.parse_gwas_association_data(raw, "Trait X", config)
    assert not df.empty

    # Must be filled from study fetch for missing pubmedId
    assert df["PubMed_ID"].iloc[0] == "99999999"
    assert calls["count"] >= 1

    # Contract: association id must be carried through the pipeline
    assert "GWAS_Association_ID" in df.columns
    assert df["GWAS_Association_ID"].iloc[0] == "A1"

