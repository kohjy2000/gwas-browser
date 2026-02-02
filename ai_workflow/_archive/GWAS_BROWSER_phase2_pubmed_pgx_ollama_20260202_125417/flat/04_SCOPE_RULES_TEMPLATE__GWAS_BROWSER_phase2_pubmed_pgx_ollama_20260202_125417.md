# Scope Rules

This document defines file-level access control for every block.
Violation of these rules is an immediate FAIL and halt condition.

---

## Definitions

target_files are files the Executor may create or modify.

read_files are files the Executor may read for context but must not modify.

do_not_touch are files and directories that must never be modified.

---

## Enforcement Rules

| Rule | Description | Consequence |
|------|-------------|-------------|
| R1 | Only files in target_files may be modified. | FAIL and rollback |
| R2 | Files in do_not_touch must not appear in any diff. | FAIL and rollback |
| R3 | Files in read_files must not appear in any diff. | FAIL and rollback |
| R4 | Unlisted files must not be modified. | FAIL and rollback |
| R5 | New file creation is only allowed when allow_missing_targets is true and the new path is listed in target_files. | FAIL and rollback |

---

## Per-Block Scope Definitions

### Block: C1.B1 Search Traits Endpoint Contract

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/main.py

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

allow_missing_targets: false

---

### Block: C1.B2 Cache Contract Meta and Expiry

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

allow_missing_targets: false

---

### Block: C1.B3 Reference Fix PubMed Fill and Association ID

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

allow_missing_targets: false

---

### Block: C1.B4 Trait List Local File Contract

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/trait_list.json
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/trait_list.meta.json
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/scripts/update_trait_list.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_trait_list_file_contract.py

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/config/efo_mapping.json

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

allow_missing_targets: true

---

### Block: C1.B5 Frontend Gating Contract

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/js/dashboard.js

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py

allow_missing_targets: false

---

### Block: C2.B1 ClinVar Toy TSV and Matcher Library

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/clinvar/clinvar_toy.tsv
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/clinvar_matcher.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_clinvar_matcher_contract.py

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/vcf_parser.py

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py

allow_missing_targets: true

---

### Block: C2.B2 ClinVar Match API Endpoint Contract

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_clinvar_endpoint_contract.py

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/clinvar_matcher.py

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

allow_missing_targets: true

---

### Block: C3.B1 PGx Toy final TSV Parser Contract

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/pgx/final.tsv
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/pgx_parser.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/pgx_summary.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_parser_contract.py

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py

allow_missing_targets: true

---

### Block: C3.B2 PGx Summary API Endpoint Contract

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_endpoint_contract.py

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/pgx_parser.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/pgx_summary.py

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

allow_missing_targets: true

---

### Block: C4.B1 Chat Facts Model Contract

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/chat_facts.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_facts_contract.py

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py

allow_missing_targets: true

---

### Block: C4.B2 Counseling Chat API Contract

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_endpoint_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/js/dashboard.js

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/chat_facts.py

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

allow_missing_targets: true

---

### Block: C5.B1 Visible Trait Search Uses /api/search-traits

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_ui_visible_trait_search_contract.py

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

allow_missing_targets: true

---

### Block: C5.B2 ClinVar and PGx Panels Visible and Wired

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_ui_panels_clinvar_pgx_contract.py

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

allow_missing_targets: true

---

### Block: C5.B3 Chat Must Use Session Facts (No Manual Facts Paste)

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_session_facts_contract.py

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/chat_facts.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

allow_missing_targets: true

---

### Block: C5.B4 References Must Be URLs (PubMed or Study URL)

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/customer_friendly_processor.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_url_fallback_contract.py

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

allow_missing_targets: true

---

### Block: C6.B1 Remote Trait Search (GWAS Catalog) + Local Cache Update

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/trait_list.json
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/trait_list.meta.json
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_remote_cache_contract.py

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

allow_missing_targets: true

---

### Block: C6.B2 Counseling Chat (Ollama Local LLM Mode)

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_ollama_mode_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/05_RUNBOOK_TEMPLATE.md

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/chat_facts.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

allow_missing_targets: true

---

### Block: C6.B3 PubMed Meta Enrichment (Prefer PubMed When Available)

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pubmed_meta_enrichment_contract.py

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

allow_missing_targets: true

---

### Block: C7.B1 ForeGenomics PGx Report Snapshot + Parser

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/pgx/foregenomics_report.tsv
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/pgx_foregenomics.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_foregenomics_parser_contract.py

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

allow_missing_targets: true

---

### Block: C7.B2 PGx Summary API Supports ForeGenomics Source

target_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_endpoint_foregenomics_contract.py

read_files:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/pgx_foregenomics.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

do_not_touch:
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

allow_missing_targets: true

---

## Global Do-Not-Touch List

- /Users/june-young/Research_Local/08_GWAS_browser/venv
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/.git
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/app.log
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_cache_builder.log
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/app.log
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/app.log

---

## Scope Validation Checklist

- Every modified file is listed in target_files for the current block.
- No file in do_not_touch was modified.
- No file in read_files was modified.
- No unlisted file was modified.
- If new files were created, allow_missing_targets is true and the path is listed in target_files.
