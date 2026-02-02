# B2C Spec (Block-to-Code Specification)

Blocks execute sequentially. Block count is fixed to 11 blocks for Cycle 1 to 4.

## Global Settings

| Setting | Value |
|---------|-------|
| max_attempts_per_block | 3 |
| loop_breaker_N | 3 |
| auto_strategist_on_fail | true |

---

## Block: C1.B1 Search Traits Endpoint Contract

### Description

Ensure POST /api/search-traits meets the contract expected by existing contract tests.

### Dependencies

- Depends on: none

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/main.py

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_search_traits_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_dashboard_package/src/routes/api.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_dashboard_package/src/routes/api.py
git status --porcelain
```

### Acceptance Criteria

1. Query shorter than 3 returns HTTP 400 with success false and a message string.
2. Valid query returns HTTP 200 with success true and a results list.
3. Each result item contains only trait, efo_id, score with correct types.
4. Existing contract test passes: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py

### Allow NOOP

- true

### Notes

If the endpoint already passes contract tests, NOOP is allowed.

---

## Block: C1.B2 Cache Contract Meta and Expiry

### Description

Make cache load and save behavior comply with cache contract tests: support legacy parquet without meta, enforce expiry when meta exists, and write meta on save.

### Dependencies

- Depends on: C1.B1 Search Traits Endpoint Contract

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_cache_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py
git status --porcelain
```

### Acceptance Criteria

1. Legacy cache file with only parquet loads successfully.
2. Cache with meta loads when fetched_at is within expiry days.
3. Cache with meta returns None when fetched_at is older than expiry days.
4. Save writes meta JSON containing efo_id, trait, fetched_at, association_count.
5. Existing contract test passes: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py

### Allow NOOP

- false

### Notes

Contract tests create cache dirs under data with a _contract_cache_ prefix.

---

## Block: C1.B3 Reference Fix PubMed Fill and Association ID

### Description

Update GWAS parsing to fill missing PubMed ID by fetching study JSON via the study link and preserve GWAS association ID as a DataFrame column.

### Dependencies

- Depends on: C1.B2 Cache Contract Meta and Expiry

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_reference_fix_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py
git status --porcelain
```

### Acceptance Criteria

1. When publicationInfo pubmedId is missing, code calls requests.get on the study link and fills PubMed_ID.
2. Output DataFrame includes GWAS_Association_ID and preserves associationId.
3. Existing contract test passes: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py

### Allow NOOP

- false

### Notes

The contract test monkeypatches requests.get and expects it to be called.

---

## Block: C1.B4 Trait List Local File Contract

### Description

Add stable local trait list files under project data and add a contract test that validates the on-disk schema. Align the trait list updater output directory with the dashboard reader.

### Dependencies

- Depends on: C1.B3 Reference Fix PubMed Fill and Association ID

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/trait_list.json
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/trait_list.meta.json
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/scripts/update_trait_list.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_trait_list_file_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/config/efo_mapping.json

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_trait_list_file_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_variant_analyzer/scripts/update_trait_list.py contract_tests/test_trait_list_file_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_variant_analyzer/scripts/update_trait_list.py contract_tests/test_trait_list_file_contract.py
git status --porcelain
```

### Acceptance Criteria

1. data/trait_list.json exists and is valid JSON list with keys trait, shortForm, uri.
2. data/trait_list.meta.json exists and includes updated_at and total_traits.
3. New contract test passes without network.
4. Updater script output directory is the project-root data directory.

### Allow NOOP

- false

### Notes

The updater script may use network, but the contract test must only validate local files.

---

## Block: C1.B5 Frontend Gating Contract

### Description

Ensure the frontend includes required DOM IDs and references the search endpoint and hidden EFO field expected by existing frontend contract tests.

### Dependencies

- Depends on: C1.B4 Trait List Local File Contract

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/js/dashboard.js

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_frontend_contract.py
git status --porcelain
```

### Acceptance Criteria

1. index.html contains trait-search-input, trait-search-results, selected-efo-id.
2. dashboard.js references /api/search-traits or search-traits and uses selected-efo-id.
3. Existing contract test passes: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

### Allow NOOP

- true

### Notes

If the frontend already passes, NOOP is allowed.

---

## Block: C2.B1 ClinVar Toy TSV and Matcher Library

### Description

Add a toy ClinVar TSV database and a matcher library that matches variants using a normalized chrom pos ref alt key, with optional rsID as secondary. Add a contract test for the matcher and TSV schema.

### Dependencies

- Depends on: C1.B5 Frontend Gating Contract

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/clinvar/clinvar_toy.tsv
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/clinvar_matcher.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_clinvar_matcher_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/vcf_parser.py

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_clinvar_matcher_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_variant_analyzer/gwas_variant_analyzer/clinvar_matcher.py contract_tests/test_clinvar_matcher_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_variant_analyzer/gwas_variant_analyzer/clinvar_matcher.py
git status --porcelain
```

### Acceptance Criteria

1. Toy ClinVar TSV exists and has required header columns defined in contracts.
2. Primary match uses a normalized chrom pos ref alt key.
3. Secondary rsID match is optional and does not override primary matches.
4. New contract test passes without network.

### Allow NOOP

- false

### Notes

This is toy data. No real ClinVar downloads.

---

## Block: C2.B2 ClinVar Match API Endpoint Contract

### Description

Add a new endpoint POST /api/clinvar-match that uses uploaded session variants and returns a deterministic pathogenic match report. Add an endpoint contract test.

### Dependencies

- Depends on: C2.B1 ClinVar Toy TSV and Matcher Library

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_clinvar_endpoint_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/clinvar_matcher.py

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_clinvar_endpoint_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_dashboard_package/src/routes/api.py contract_tests/test_clinvar_endpoint_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_dashboard_package/src/routes/api.py
git status --porcelain
```

### Acceptance Criteria

1. POST /api/clinvar-match exists and returns 400 on missing or invalid session_id.
2. Success response includes success, summary, matches and is deterministic.
3. New endpoint contract test passes without network.

### Allow NOOP

- false

### Notes

Endpoint reads variants from the existing upload session store.

---

## Block: C3.B1 PGx Toy final TSV Parser Contract

### Description

Add a toy PGx final TSV data file and deterministic parser and summary logic. Add a parser contract test. This block must follow minimal-context execution.

### Dependencies

- Depends on: C2.B2 ClinVar Match API Endpoint Contract

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/pgx/final.tsv
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/pgx_parser.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/pgx_summary.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_parser_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_pgx_parser_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_variant_analyzer/gwas_variant_analyzer/pgx_parser.py gwas_variant_analyzer/gwas_variant_analyzer/pgx_summary.py contract_tests/test_pgx_parser_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_variant_analyzer/gwas_variant_analyzer/pgx_parser.py gwas_variant_analyzer/gwas_variant_analyzer/pgx_summary.py
git status --porcelain
```

### Acceptance Criteria

1. Toy final TSV exists with required columns described in contracts.
2. Parser produces deterministic structured output from the toy file.
3. New parser contract test passes without network.

### Allow NOOP

- false

### Notes

Minimal-context rule: only provide the necessary files to the Executor for this block.

---

## Block: C3.B2 PGx Summary API Endpoint Contract

### Description

Add a new endpoint POST /api/pgx-summary that returns a deterministic summary and includes disclaimer tags. Add an endpoint contract test.

### Dependencies

- Depends on: C3.B1 PGx Toy final TSV Parser Contract

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_endpoint_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/pgx_parser.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/pgx_summary.py

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_pgx_endpoint_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_dashboard_package/src/routes/api.py contract_tests/test_pgx_endpoint_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_dashboard_package/src/routes/api.py
git status --porcelain
```

### Acceptance Criteria

1. POST /api/pgx-summary exists and returns deterministic output.
2. Response includes disclaimer_tags and disclaimer_tags is non-empty.
3. New endpoint contract test passes without network.

### Allow NOOP

- false

### Notes

If any optional LLM mode exists, contract tests must force deterministic non-LLM mode.

---

## Block: C4.B1 Chat Facts Model Contract

### Description

Add a deterministic facts model that collects GWAS, ClinVar, and PGx facts into a single structure with stable citation IDs. Add a facts contract test.

### Dependencies

- Depends on: C3.B2 PGx Summary API Endpoint Contract

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/chat_facts.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_facts_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_chat_facts_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_variant_analyzer/gwas_variant_analyzer/chat_facts.py contract_tests/test_chat_facts_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_variant_analyzer/gwas_variant_analyzer/chat_facts.py
git status --porcelain
```

### Acceptance Criteria

1. Facts model produces stable citation IDs referencing concrete items from inputs.
2. New facts contract test passes without network.

### Allow NOOP

- false

### Notes

This is pure deterministic logic.

---

## Block: C4.B2 Counseling Chat API Contract

### Description

Add a counseling chat endpoint POST /api/chat that is facts-based and enforces disclaimer_tags and citations on every response. Add an endpoint contract test. Add minimal frontend wiring if needed.

### Dependencies

- Depends on: C4.B1 Chat Facts Model Contract

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_endpoint_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/js/dashboard.js

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/chat_facts.py

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_chat_endpoint_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_dashboard_package/src/routes/api.py contract_tests/test_chat_endpoint_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_dashboard_package/src/routes/api.py
git status --porcelain
```

### Acceptance Criteria

1. POST /api/chat exists and returns success, answer, disclaimer_tags, citations, risk_level.
2. disclaimer_tags is always present and non-empty.
3. citations is always present and references known IDs produced by the facts model.
4. New endpoint contract test passes without network.

### Allow NOOP

- false

### Notes

Cycle 4 is high-risk domain. Disclaimers and citations are mandatory and must be enforced by contract tests.

---

## Execution Order Summary

| Order | Block Name | Depends On |
|-------|-----------|------------|
| 1 | C1.B1 Search Traits Endpoint Contract | none |
| 2 | C1.B2 Cache Contract Meta and Expiry | C1.B1 Search Traits Endpoint Contract |
| 3 | C1.B3 Reference Fix PubMed Fill and Association ID | C1.B2 Cache Contract Meta and Expiry |
| 4 | C1.B4 Trait List Local File Contract | C1.B3 Reference Fix PubMed Fill and Association ID |
| 5 | C1.B5 Frontend Gating Contract | C1.B4 Trait List Local File Contract |
| 6 | C2.B1 ClinVar Toy TSV and Matcher Library | C1.B5 Frontend Gating Contract |
| 7 | C2.B2 ClinVar Match API Endpoint Contract | C2.B1 ClinVar Toy TSV and Matcher Library |
| 8 | C3.B1 PGx Toy final TSV Parser Contract | C2.B2 ClinVar Match API Endpoint Contract |
| 9 | C3.B2 PGx Summary API Endpoint Contract | C3.B1 PGx Toy final TSV Parser Contract |
| 10 | C4.B1 Chat Facts Model Contract | C3.B2 PGx Summary API Endpoint Contract |
| 11 | C4.B2 Counseling Chat API Contract | C4.B1 Chat Facts Model Contract |
