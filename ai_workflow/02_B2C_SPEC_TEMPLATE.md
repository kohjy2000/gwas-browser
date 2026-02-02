# B2C Spec (Block-to-Code Specification)

Blocks execute sequentially. Block count is fixed to 11 blocks for Cycle 1 to 4.
Cycle 5 (Phase 2) is allowed to add additional blocks when Gate2 passes but the real UI/UX is still unacceptable.

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

---

## Cycle 9 (Phase 6): Persistency + Auto-Analyze + Dataset Expansion

These blocks exist because users still report:
- “GWAS cache was deleted” (actually: versioned folders don’t share cache; self-heal can also refetch once)
- Chat answers using only PGx facts even when the question is clearly GWAS/trait-driven
- PGx drug lists are still too small without additional datasets

## Block: C9.B1 GWAS Cache Directory Override (Persist Across Versions)

### Description

Stop the “cache disappeared / refetching again” pain.
Introduce a single shared cache directory controlled by env:

- If `GWAS_CACHE_DIR` is set: read/write GWAS cache parquet/meta only under that directory.
- Else: keep legacy behavior (`/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache`).

This should work across versioned project folders so you don’t lose cache when you clone/copy a new `ver_*` folder.

### Dependencies

- Depends on: C8.B3 GWAS Cache Self-Heal for PubMed (Stale If Missing)

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_gwas_cache_dir_override_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/utils.py

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_gwas_cache_dir_override_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py contract_tests/test_gwas_cache_dir_override_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py
git status --porcelain
```

### Acceptance Criteria

1. With `GWAS_CACHE_DIR` set to a directory, cache read/write paths are under that directory only.
2. With env var unset, legacy behavior remains unchanged.
3. New contract test passes:
   - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_gwas_cache_dir_override_contract.py

### Allow NOOP

- false

---

## Block: C9.B2 Chat: Suggest Trait Analysis When Missing Facts

### Description

When the user asks a trait-driven question (e.g., “obesity risk”) but the session has no GWAS facts loaded,
the chat should not answer using only PGx facts.

Instead, return a `next_actions` / `suggested_actions` field that the UI can render as a one-click action:
- Suggest selecting the extracted trait (via `/api/search-traits`) and running `/api/analyze`.

This is “auto-analyze 유도/트리거” without silently running expensive network calls.

### Dependencies

- Depends on: C8.B4 Chat Transparency: Report Ollama Model Used

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_suggest_analyze_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_endpoint_contract.py

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_chat_suggest_analyze_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_dashboard_package/src/routes/api.py contract_tests/test_chat_suggest_analyze_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_dashboard_package/src/routes/api.py
git status --porcelain
```

### Acceptance Criteria

1. `/api/chat` response includes `suggested_actions` when user asks about a recognizable trait and `gwas_hits` are missing.
2. UI renders this as a visible button (e.g., “Analyze obesity”) that triggers the normal flow (search-traits → analyze).
3. New contract test passes:
   - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_suggest_analyze_contract.py

### Allow NOOP

- false

---

## Block: C9.B3 PGx Dataset Expansion: CPIC Snapshot Ingest

### Description

Expand the PGx drug list beyond the current ForeGenomics snapshot by adding a **CPIC toy snapshot**.

Requirements:
- Store a small CPIC-like mapping snapshot inside the project (no external download during tests).
- Parse it into normalized recommendations (drug, gene, phenotype/diplotype, recommendation summary, evidence link).
- Extend `/api/pgx-summary` to optionally include these recommendations (either as a new `source="cpic"` or a merge mode).

### Dependencies

- Depends on: C7.B2 PGx Summary API Supports ForeGenomics Source

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/pgx/cpic_toy.tsv
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/pgx_cpic.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_cpic_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/pgx_foregenomics.py

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_pgx_cpic_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_dashboard_package/src/routes/api.py gwas_variant_analyzer/gwas_variant_analyzer/pgx_cpic.py contract_tests/test_pgx_cpic_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_variant_analyzer/gwas_variant_analyzer/pgx_cpic.py
git status --porcelain
```

### Acceptance Criteria

1. The CPIC snapshot exists at:
   - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/pgx/cpic_toy.tsv
2. `/api/pgx-summary` can return a `summary.drugs` list that is meaningfully larger (e.g., >= 30 unique drugs) when CPIC is enabled.
3. New contract test passes:
   - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_cpic_contract.py

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
| 12 | C5.B1 Visible Trait Search Uses /api/search-traits | C4.B2 Counseling Chat API Contract |
| 13 | C5.B2 ClinVar and PGx Panels Visible and Wired | C5.B1 Visible Trait Search Uses /api/search-traits |
| 14 | C5.B3 Chat Must Use Session Facts (No Manual Facts Paste) | C5.B2 ClinVar and PGx Panels Visible and Wired |
| 15 | C5.B4 References Must Be URLs (PubMed or Study URL) | C5.B3 Chat Must Use Session Facts (No Manual Facts Paste) |
| 16 | C6.B1 Remote Trait Search (GWAS Catalog) + Local Cache Update | C5.B4 References Must Be URLs (PubMed or Study URL) |
| 17 | C6.B2 Chat Ollama Local LLM Mode | C6.B1 Remote Trait Search (GWAS Catalog) + Local Cache Update |
| 18 | C6.B3 PubMed Meta Enrichment (Prefer PubMed When Available) | C6.B2 Chat Ollama Local LLM Mode |
| 19 | C7.B1 ForeGenomics PGx Report Snapshot + Parser | C6.B3 PubMed Meta Enrichment (Prefer PubMed When Available) |
| 20 | C7.B2 PGx Summary API Supports ForeGenomics Source | C7.B1 ForeGenomics PGx Report Snapshot + Parser |
| 21 | C8.B1 UI PGx Summary Defaults to ForeGenomics Source | C7.B2 PGx Summary API Supports ForeGenomics Source |
| 22 | C8.B2 ForeGenomics Report Path Override (Env) | C8.B1 UI PGx Summary Defaults to ForeGenomics Source |
| 23 | C8.B3 GWAS Cache Self-Heal for PubMed (Stale If Missing) | C6.B3 PubMed Meta Enrichment (Prefer PubMed When Available) |
| 24 | C8.B4 Chat Transparency: Report Ollama Model Used | C6.B2 Chat Ollama Local LLM Mode |
| 25 | C9.B1 GWAS Cache Directory Override (Persist Across Versions) | C8.B3 GWAS Cache Self-Heal for PubMed (Stale If Missing) |
| 26 | C9.B2 Chat: Suggest Trait Analysis When Missing Facts | C8.B4 Chat Transparency: Report Ollama Model Used |
| 27 | C9.B3 PGx Dataset Expansion: CPIC Snapshot Ingest | C7.B2 PGx Summary API Supports ForeGenomics Source |
| 28 | C10.B1 References: PubMed Direct URL + Robust PubMed ID Extraction | C6.B3 PubMed Meta Enrichment (Prefer PubMed When Available) |
| 29 | C10.B2 ForeGenomics PGx: Per-Session Report Selection (Different Individuals ≠ Same Output) | C7.B2 PGx Summary API Supports ForeGenomics Source |
| 30 | C10.B3 Chat: Trait-Risk Guard (Do Not Answer Disease Risk From PGx-Only Facts) | C9.B2 Chat: Suggest Trait Analysis When Missing Facts |

---

## Cycle 5 (Phase 2): Product UX Activation (UI + Session Facts)

These blocks exist because Gate2 passing is not enough: the user-facing UI must actually expose and wire the features.

## Block: C5.B1 Visible Trait Search Uses /api/search-traits

### Description

Make the *visible* search box use POST /api/search-traits (not /api/search-phenotypes) so partial inputs behave as expected (e.g., "Obes" → obesity at the top). Remove or demote the NLP phenotype search in the default UI flow (it may remain as optional fallback).

### Dependencies

- Depends on: C4.B2 Counseling Chat API Contract

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_ui_visible_trait_search_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_ui_visible_trait_search_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check contract_tests/test_ui_visible_trait_search_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile contract_tests/test_ui_visible_trait_search_contract.py
git status --porcelain
```

### Acceptance Criteria

1. The visible UI search input uses POST /api/search-traits on typing (or debounced typing).
2. For query "Obes" / "obes", the suggestion list includes "obesity" as the top suggestion (UI-level behavior, not hidden inputs).
3. Selected phenotype/efo_id used for /api/analyze is the chosen /api/search-traits result (no mismatch).
4. New contract test passes: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_ui_visible_trait_search_contract.py

### Allow NOOP

- false

---

## Cycle 10 (Phase 7): PubMed + ForeGenomics Personalization + Chat Relevance

Gate2 PASS is not the end: **user-visible quality** must match the original intent:
- References should link to **real PubMed papers** (not `?term=EFO_...+rs...` searches).
- PGx should not show the *same* result for different individuals unless the inputs are truly identical.
- Chat must not answer “obesity risk” using only PGx facts (it should require GWAS facts or trigger analysis).

## Block: C10.B1 References: PubMed Direct URL + Robust PubMed ID Extraction

### Description

Make reference URLs human-meaningful:
- If PubMed_ID exists, reference must be a **direct PubMed article URL** (`/12345678/`), not a `?term=` search URL.
- If PubMed_ID is missing, reference should fall back to a GWAS Catalog stable URL (variant/study), not a vague placeholder.

Important (real GWAS Catalog API behavior, verified):
- Association objects from `/efoTraits/<EFO>/associations` and `/associations/<id>` typically **do NOT** include `publicationInfo`.
- PubMed lives on the **study** resource:
  - `/associations/<association_id>/study` → returns a study JSON with `publicationInfo.pubmedId`
  - `/studies/<GCST...>` → also has `publicationInfo.pubmedId`
- Many association objects also omit `associationId`; you must parse it from `_links.self.href`
  (example: `.../associations/13733` → association_id=`13733`).

This block is allowed to touch both:
- PubMed_ID extraction (parsing / study JSON keys)
- Reference URL formatting (customer-friendly layer)

### Dependencies

- Depends on: C6.B3 PubMed Meta Enrichment (Prefer PubMed When Available)

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/customer_friendly_processor.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_url_quality_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_url_fallback_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_reference_url_quality_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py gwas_variant_analyzer/gwas_variant_analyzer/customer_friendly_processor.py contract_tests/test_reference_url_quality_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py gwas_variant_analyzer/gwas_variant_analyzer/customer_friendly_processor.py
git status --porcelain
```

### Acceptance Criteria

1. When PubMed_ID is known, variants[].reference equals `https://pubmed.ncbi.nlm.nih.gov/<PubMed_ID>/` (no `?term=`).
2. When PubMed_ID is missing but rsid is known, variants[].reference is a stable GWAS Catalog URL (variant/study), not “No publication…” and not a PubMed `?term=` search.
3. New contract test passes:
   - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_url_quality_contract.py

### Allow NOOP

- false

---

## Block: C10.B2 ForeGenomics PGx: Per-Session Report Selection (Different Individuals ≠ Same Output)

### Description

Fix “PGx looks identical for different individuals” by making ForeGenomics ingestion session-aware:
- Derive a `sample_id` from the uploaded VCF (or explicitly supplied sample_id).
- Select the matching ForeGenomics report file for that sample_id (from a root directory).
- Store the summary into the session so chat can cite it.

### Dependencies

- Depends on: C7.B2 PGx Summary API Supports ForeGenomics Source

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/pgx_foregenomics.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/pgx/foregenomics_reports/SAMPLE_A.PGx.out.report.tsv
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/pgx/foregenomics_reports/SAMPLE_B.PGx.out.report.tsv
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_foregenomics_session_select_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_endpoint_foregenomics_contract.py

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_pgx_foregenomics_session_select_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_dashboard_package/src/routes/api.py gwas_variant_analyzer/gwas_variant_analyzer/pgx_foregenomics.py contract_tests/test_pgx_foregenomics_session_select_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_dashboard_package/src/routes/api.py gwas_variant_analyzer/gwas_variant_analyzer/pgx_foregenomics.py
git status --porcelain
```

### Acceptance Criteria

1. With `FOREGENOMICS_PGX_ROOT` set, `/api/pgx-summary` source="foregenomics" uses the report that matches the session’s sample_id.
2. Two different uploaded fixture VCFs (different sample_id) produce **different** ForeGenomics summaries.
3. New contract test passes:
   - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_foregenomics_session_select_contract.py

### Allow NOOP

- false

---

## Block: C10.B3 Chat: Trait-Risk Guard (Do Not Answer Disease Risk From PGx-Only Facts)

### Description

Prevent misleading answers like “obesity risk: medium” when only PGx facts exist.

Rules:
- If user’s message mentions a trait (e.g., obesity) and session has **no GWAS facts**, chat must:
  - avoid disease-risk scoring from PGx-only facts
  - return risk_level="low"
  - include suggested_actions to run trait analysis (C9.B2 behavior), and a clear instruction to run GWAS analysis first
- If GWAS facts exist, chat may answer trait-risk questions and cite GWAS fact IDs.

### Dependencies

- Depends on: C9.B2 Chat: Suggest Trait Analysis When Missing Facts

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_trait_risk_guard_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_suggest_analyze_contract.py

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_chat_trait_risk_guard_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_dashboard_package/src/routes/api.py contract_tests/test_chat_trait_risk_guard_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_dashboard_package/src/routes/api.py
git status --porcelain
```

### Acceptance Criteria

1. When only PGx facts exist and user asks a trait-risk question, chat does NOT produce a “medium/high” trait risk; returns risk_level="low" and guides to run analysis.
2. suggested_actions includes analyze_trait for the detected trait.
3. New contract test passes:
   - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_trait_risk_guard_contract.py

### Allow NOOP

- false

---

## Block: C5.B2 ClinVar and PGx Panels Visible and Wired

### Description

Expose ClinVar(rare variant) and PGx as **UI tabs** and wire them to the existing API endpoints using the current session_id from upload.

Tab names (fixed):
- GWAS
- ClinVar (rare variant)
- PGx
- Chat

Visibility rule (fixed):
- Tabs for ClinVar/PGx/Chat are hidden (or disabled) until VCF upload succeeds (session_id exists).
- After upload succeeds, those tabs become visible/clickable and can call their endpoints.

### Dependencies

- Depends on: C5.B1 Visible Trait Search Uses /api/search-traits

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_ui_panels_clinvar_pgx_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_ui_panels_clinvar_pgx_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check contract_tests/test_ui_panels_clinvar_pgx_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile contract_tests/test_ui_panels_clinvar_pgx_contract.py
git status --porcelain
```

### Acceptance Criteria

1. UI contains a tab system (buttons + panels) with stable DOM IDs defined in contracts (tabs, panels, and result containers).
2. Before upload (no session_id), ClinVar/PGx/Chat tabs are not shown or are disabled and show a clear “upload first” message.
3. After upload (session_id exists), UI can trigger:
   - POST /api/clinvar-match with session_id
   - POST /api/pgx-summary with session_id
4. UI renders returned results to the page inside the relevant tab panel (not only console logs).
5. New contract test passes: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_ui_panels_clinvar_pgx_contract.py

### Allow NOOP

- false

---

## Block: C5.B3 Chat Must Use Session Facts (No Manual Facts Paste)

### Description

Make chat usable from the UI by ensuring the UI sends session_id and the backend can derive facts from that session (GWAS/ClinVar/PGx results stored or computed). "No genetic facts are currently loaded..." must not happen after the user has uploaded a VCF and run at least one analysis step.

### Dependencies

- Depends on: C5.B2 ClinVar and PGx Panels Visible and Wired

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_session_facts_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/chat_facts.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_chat_session_facts_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_dashboard_package/src/routes/api.py contract_tests/test_chat_session_facts_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_dashboard_package/src/routes/api.py
git status --porcelain
```

### Acceptance Criteria

1. UI chat request includes session_id when available.
2. Backend /api/chat accepts session_id and uses session-derived facts when facts are not explicitly provided.
3. Response always includes disclaimer_tags and citations, and is not the "no facts loaded" message when session facts exist.
4. New contract test passes: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_session_facts_contract.py

### Allow NOOP

- false

---

## Block: C5.B4 References Must Be URLs (PubMed or Study URL)

### Description

Stop emitting "No publication reference available" as the default reference string. If PubMed_ID is missing, use a deterministic study URL (GWAS Catalog link) when available, so the UI can always render a clickable reference.

### Dependencies

- Depends on: C5.B3 Chat Must Use Session Facts (No Manual Facts Paste)

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/customer_friendly_processor.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_url_fallback_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_reference_url_fallback_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py gwas_variant_analyzer/gwas_variant_analyzer/customer_friendly_processor.py contract_tests/test_reference_url_fallback_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py gwas_variant_analyzer/gwas_variant_analyzer/customer_friendly_processor.py
git status --porcelain
```

### Acceptance Criteria

1. Customer-facing variant items have reference as a URL string when any study link is available.
2. The literal string "No publication reference available" must not appear in end-user variant outputs.
3. New contract test passes: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_url_fallback_contract.py

### Allow NOOP

- false

---

## Cycle 6 (Phase 3): Online Traits + Local LLM (Ollama)

Cycle 6 adds two capabilities you explicitly asked for:
- If a trait is not in local cache, trait search must query a remote API (GWAS Catalog REST) and then cache it locally.
- Chat must support a local LLM via Ollama (configurable model), while still enforcing disclaimer_tags + citations and keeping tests network-free (mock remote calls).

## Block: C6.B1 Remote Trait Search (GWAS Catalog) + Local Cache Update

### Description

Extend POST /api/search-traits so that when local results are empty or too weak, it queries the GWAS Catalog REST API trait search endpoint, merges the results into the response, and updates the local trait cache file (data/trait_list.json + meta).

### Dependencies

- Depends on: C5.B4 References Must Be URLs (PubMed or Study URL)

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/trait_list.json
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/trait_list.meta.json
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_remote_cache_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_search_traits_remote_cache_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_dashboard_package/src/routes/api.py contract_tests/test_search_traits_remote_cache_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_dashboard_package/src/routes/api.py
git status --porcelain
```

### Acceptance Criteria

1. When local trait cache produces no results for a query, /api/search-traits calls the configured GWAS Catalog trait search endpoint.
2. Remote calls are OPTIONAL and must be disabled by default in tests; contract tests must monkeypatch the HTTP client and prove it is called.
3. Remote results are merged into the response with the same schema (trait, efo_id, score).
4. New traits from remote are appended/merged into data/trait_list.json (dedupe by shortForm or trait+shortForm), and meta updated_at/total_traits is updated.
5. New contract test passes: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_remote_cache_contract.py

### Allow NOOP

- false

---

## Block: C6.B2 Counseling Chat (Ollama Local LLM Mode)

### Description

Add an Ollama-backed mode to /api/chat so that after facts exist (session_id or explicit facts), the backend can call a local LLM to produce a better answer — while still enforcing disclaimer_tags + citations and keeping contract tests network-free by mocking the Ollama call.

### Dependencies

- Depends on: C6.B1 Remote Trait Search (GWAS Catalog) + Local Cache Update

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_ollama_mode_contract.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/05_RUNBOOK_TEMPLATE.md

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/chat_facts.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_chat_ollama_mode_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_dashboard_package/src/routes/api.py contract_tests/test_chat_ollama_mode_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_dashboard_package/src/routes/api.py
git status --porcelain
```

### Acceptance Criteria

1. /api/chat supports a configuration flag to use local LLM via Ollama (host + model via env vars).
2. Contract tests must not require a running Ollama; instead they monkeypatch the Ollama call and assert it was invoked and the response is validated.
3. Regardless of LLM mode, response MUST include disclaimer_tags (non-empty) + citations (non-empty) and must reference known fact IDs.
4. New contract test passes: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_ollama_mode_contract.py

### Allow NOOP

- false

---

## Block: C6.B3 PubMed Meta Enrichment (Prefer PubMed When Available)

### Description

Fix GWAS meta parsing so that PubMed IDs are recovered whenever the GWAS Catalog metadata provides them.

Observed failure mode:
- For the same rsID/alt key, the first association record may lack PubMed metadata but a later one has it.
- Current parsing can “lock in” an empty PubMed_ID and never update it.

This block makes PubMed_ID prefer non-empty values and ensures we do not drop PubMed metadata in downstream processing.

### Dependencies

- Depends on: C6.B2 Counseling Chat (Ollama Local LLM Mode)

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pubmed_meta_enrichment_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_pubmed_meta_enrichment_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py contract_tests/test_pubmed_meta_enrichment_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py
git status --porcelain
```

### Acceptance Criteria

1. If multiple association records map to the same (rsid, alt) key and at least one has a PubMed ID, the final parsed DataFrame must carry a non-empty PubMed_ID for that key.
2. PubMed_ID must be normalized to a string integer when possible (e.g., 29878757.0 → "29878757").
3. New contract test passes without network:
   - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pubmed_meta_enrichment_contract.py

### Allow NOOP

- false

---

## Cycle 7 (Phase 4): ForeGenomics_PGx Ingest (Richer PGx)

Cycle 3 PGx was toy-only. Cycle 7 ingests a real local PGx report TSV (ForeGenomics_PGx output)
into our PGx summary schema so the drug list is much richer.

Important rule:
- Contract tests must not depend on reading external folders.
- Therefore, the Executor must copy a small “snapshot” TSV into this project under data/pgx/.

## Block: C7.B1 ForeGenomics PGx Report Snapshot + Parser

### Description

Add a parser for the ForeGenomics PGx report TSV format and a small snapshot file under data/pgx/.

Input source (read-only, outside project):
- /Users/june-young/Research_Local/08_GWAS_browser/ForeGenomics_PGx/trial/GINS-AAM4-0007-10AD/GINS-AAM4-0007-10AD.PGx.out.report.tsv

Snapshot destination (inside project, used by tests):
- data/pgx/foregenomics_report.tsv

### Dependencies

- Depends on: C6.B3 PubMed Meta Enrichment (Prefer PubMed When Available)

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/pgx/foregenomics_report.tsv
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/pgx_foregenomics.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_foregenomics_parser_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_pgx_foregenomics_parser_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_variant_analyzer/gwas_variant_analyzer/pgx_foregenomics.py contract_tests/test_pgx_foregenomics_parser_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_variant_analyzer/gwas_variant_analyzer/pgx_foregenomics.py
git status --porcelain
```

### Acceptance Criteria

1. Snapshot TSV exists at data/pgx/foregenomics_report.tsv and is a faithful copy of the source report (header preserved).
2. Parser returns a normalized DataFrame with at minimum these logical fields:
   - gene, drug, genotype, phenotype, recommendation, guideline_ids
3. New contract test passes and demonstrates that the parsed snapshot yields “many drugs” (e.g., >= 10 unique drugs).

### Allow NOOP

- false

---

## Block: C7.B2 PGx Summary API Supports ForeGenomics Source

### Description

Extend POST /api/pgx-summary so that it can return a richer summary from the ForeGenomics snapshot (source="foregenomics"),
store it in session, and make it available to chat facts.

### Dependencies

- Depends on: C7.B1 ForeGenomics PGx Report Snapshot + Parser

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_endpoint_foregenomics_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/pgx_foregenomics.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_pgx_endpoint_foregenomics_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_dashboard_package/src/routes/api.py contract_tests/test_pgx_endpoint_foregenomics_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_dashboard_package/src/routes/api.py
git status --porcelain
```

### Acceptance Criteria

1. /api/pgx-summary accepts source="foregenomics" and returns success true with summary and disclaimer_tags.
2. Summary must include a drugs list with >= 10 unique drugs for the foregenomics source (derived from snapshot).
3. Session storage works: for a provided session_id, the PGx summary is stored in UPLOADS[session_id]['pgx_summary'] for chat facts.
4. New contract test passes:
   - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_endpoint_foregenomics_contract.py

---

## Cycle 8 (Phase 5): Real-World Behavior Fixes (PubMed / ForeGenomics / Ollama)

These blocks exist because **Gate2 PASS ≠ user acceptance**.
We are now targeting the exact gaps observed in manual UI testing:
- Trait search must use `/api/search-traits` (if still using `/api/search-phenotypes`, results will look unrelated).
- PGx must not be “toy-only”; UI must be able to request ForeGenomics source.
- PubMed references must be real paper links whenever possible (and cache must not freeze “missing PubMed forever”).
- Chat must transparently report whether it used Ollama and which model.

## Block: C8.B1 UI PGx Summary Defaults to ForeGenomics Source

### Description

Update the UI so the PGx tab calls POST `/api/pgx-summary` with `source="foregenomics"` by default (or provides a visible toggle),
so the drug list is not trivially small.

### Dependencies

- Depends on: C7.B2 PGx Summary API Supports ForeGenomics Source

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_ui_pgx_source_foregenomics_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_ui_pgx_source_foregenomics_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check contract_tests/test_ui_pgx_source_foregenomics_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile contract_tests/test_ui_pgx_source_foregenomics_contract.py
git status --porcelain
```

### Acceptance Criteria

1. The PGx UI calls `/api/pgx-summary` with `source="foregenomics"` by default (or via explicit toggle).
2. The UI renders the returned `summary.drugs` and it is visibly “not tiny” (>= 10 unique drugs in the foregenomics source).
3. New contract test passes:
   - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_ui_pgx_source_foregenomics_contract.py

### Allow NOOP

- false

---

## Block: C8.B2 ForeGenomics Report Path Override (Env)

### Description

Make the ForeGenomics ingest **not be hardcoded to a snapshot file only**.
Add an environment-variable override so the backend can ingest a real local report produced by ForeGenomics runs.

Env contract:
- If `FOREGENOMICS_PGX_REPORT_PATH` is set, use that path for `source="foregenomics"`.
- Else, fall back to `data/pgx/foregenomics_report.tsv` (snapshot).

### Dependencies

- Depends on: C8.B1 UI PGx Summary Defaults to ForeGenomics Source

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_foregenomics_env_path_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/pgx_foregenomics.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_pgx_foregenomics_env_path_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_dashboard_package/src/routes/api.py contract_tests/test_pgx_foregenomics_env_path_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_dashboard_package/src/routes/api.py
git status --porcelain
```

### Acceptance Criteria

1. When `FOREGENOMICS_PGX_REPORT_PATH` is set, `/api/pgx-summary` with `source="foregenomics"` reads from that path.
2. When env var is not set, it falls back to `data/pgx/foregenomics_report.tsv`.
3. New contract test passes:
   - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_foregenomics_env_path_contract.py

### Allow NOOP

- false

---

## Block: C8.B3 GWAS Cache Self-Heal for PubMed (Stale If Missing)

### Description

Fix the “PubMed ID is always empty forever” failure mode:
old cached parquet files can freeze missing PubMed fields even after parser fixes.

Add a cache health rule to `load_gwas_data_from_cache`:
- If cache loads but is missing `PubMed_ID` column OR has PubMed empty for all rows, treat it as stale and return `None` (so the caller refetches).
- Provide an explicit opt-in toggle via env:
  - `GWAS_CACHE_REQUIRE_PUBMED=1` enables the self-heal rule (default OFF for backward compatibility).

### Dependencies

- Depends on: C6.B3 PubMed Meta Enrichment (Prefer PubMed When Available)

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_pubmed_selfheal_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_cache_pubmed_selfheal_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py contract_tests/test_cache_pubmed_selfheal_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py
git status --porcelain
```

### Acceptance Criteria

1. With `GWAS_CACHE_REQUIRE_PUBMED=1`, a cache file that has no PubMed information is treated as stale (returns `None`).
2. With env var unset, legacy behavior stays unchanged (cache loads if not expired).
3. New contract test passes:
   - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_pubmed_selfheal_contract.py

### Allow NOOP

- false

---

## Block: C8.B4 Chat Transparency: Report Ollama Model Used

### Description

Expose which model was used for chat so users can debug quality:
- If Ollama mode is enabled and used, return `llm: {enabled: true, provider: "ollama", model: "<tag>"}`.
- If falling back to deterministic, return `llm: {enabled: false, provider: "deterministic", model: ""}`.

Also update the UI to show this in the Chat panel under the answer.

### Dependencies

- Depends on: C6.B2 Chat Ollama Local LLM Mode

### Target Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_llm_info_contract.py

### Read Files

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md

### Do Not Touch

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/gwas_cache

### Tests Required

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests/test_chat_llm_info_contract.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_dashboard_package/src/routes/api.py contract_tests/test_chat_llm_info_contract.py --select E9,F63,F7,F82
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m py_compile gwas_dashboard_package/src/routes/api.py
git status --porcelain
```

### Acceptance Criteria

1. `/api/chat` responses always include `llm` object with provider + model transparency.
2. New contract test passes:
   - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_llm_info_contract.py

### Allow NOOP

- false
