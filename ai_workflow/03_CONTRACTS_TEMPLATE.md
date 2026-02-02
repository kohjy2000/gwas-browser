# Contracts

Contracts define testable acceptance rules for deliverables.

---

## Contract: API_SearchTraits_v1

### Type

API Endpoint

### Specification

| Field | Value |
|-------|-------|
| Method | POST |
| Path | /api/search-traits |
| Input | JSON body with keys query (string) and optional top_k (integer) |
| Output | JSON response with success and either results or message |

### Required Response Keys

- success (boolean)
- results (list) on success
- message (string) on error

### Validation Rules

1. Query shorter than 3 returns HTTP 400 with success false and a message string.
2. Valid query returns HTTP 200 with success true and a results list.
3. Each results item contains trait (string), efo_id (string), score (number).
4. Scoring rules: prefix match 1.0, contains match 0.8, token-prefix match 0.6.
5. Sorting rules: score descending, then trait ascending.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py

---

## Contract: Func_Cache_Load_v1

### Type

Function

### Specification

| Field | Value |
|-------|-------|
| Signature | load_gwas_data_from_cache(efo_id, config) |
| Input | efo_id string, config keys gwas_cache_directory and gwas_cache_expiry_days |
| Output | DataFrame or None |

### Validation Rules

1. If gwas_cache_directory is missing or empty, return None.
2. If parquet exists and meta is missing, load parquet (legacy support).
3. If meta exists, enforce expiry using fetched_at and gwas_cache_expiry_days; expired returns None.
4. Malformed meta must not crash; treat as expired and return None.
5. (Optional extension, C8.B3) If `GWAS_CACHE_REQUIRE_PUBMED=1` env var is set:
   - If loaded parquet is missing `PubMed_ID` column OR all `PubMed_ID` values are empty, treat as stale and return None.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py

---

## Contract: Func_Cache_Save_v1

### Type

Function

### Specification

| Field | Value |
|-------|-------|
| Signature | save_gwas_data_to_cache(df, efo_id, config) |
| Input | DataFrame, efo_id string, config key gwas_cache_directory |
| Output | Writes parquet and meta JSON |

### Validation Rules

1. If gwas_cache_directory is missing or empty, function performs no writes.
2. Writes a parquet file named by efo_id in the configured cache directory.
3. Writes a meta JSON file named by efo_id with keys efo_id, trait, fetched_at, association_count.
4. association_count equals number of rows in the saved DataFrame.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py

---

## Contract: Func_ReferenceFix_Parse_v1

### Type

Function

### Specification

| Field | Value |
|-------|-------|
| Signature | parse_gwas_association_data(raw_associations, trait_name, config) |
| Input | GWAS association list, trait name, config |
| Output | DataFrame with PubMed filled and association ID preserved |

### Validation Rules

1. If publicationInfo pubmedId is missing, fetch study JSON using the study link and fill PubMed_ID.
2. DataFrame includes GWAS_Association_ID and preserves associationId for each row.
3. Implementation must call requests.get for missing PubMed to allow monkeypatching in tests.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py

---

## Contract: Frontend_Gating_v1

### Type

Data File

### Specification

| Field | Value |
|-------|-------|
| HTML Path | /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html |
| JS Path | /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/js/dashboard.js |

### Validation Rules

1. HTML contains required IDs: trait-search-input, trait-search-results, selected-efo-id.
2. JS references /api/search-traits or search-traits and references selected-efo-id.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py

---

## Contract: Data_TraitList_JSON_v1

### Type

Data File

### Specification

| Field | Value |
|-------|-------|
| Trait list path | /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/trait_list.json |
| Meta path | /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/trait_list.meta.json |
| Format | JSON |

### Validation Rules

1. trait_list.json is a JSON list.
2. Each item contains keys trait, shortForm, uri.
3. trait_list.meta.json exists and contains updated_at and total_traits.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_trait_list_file_contract.py

---

## Contract: Data_ClinVar_Toy_TSV_v1

### Type

Data File

### Specification

| Field | Value |
|-------|-------|
| Path | /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/clinvar/clinvar_toy.tsv |
| Format | TSV |
| Encoding | UTF-8 |
| Header row | Yes |

### Validation Rules

1. Required columns: chrom, pos, ref, alt, clinical_significance, condition, gene, variation_id, rsid
2. Minimum rows: at least 3 data rows.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_clinvar_matcher_contract.py

---

## Contract: Func_ClinVar_Matcher_v1

### Type

Function

### Specification

| Field | Value |
|-------|-------|
| Purpose | Match user variants to the toy ClinVar TSV |
| Input | user variant table and ClinVar TSV path |
| Output | deterministic match report |

### Validation Rules

1. Primary match key normalizes to chrom-pos-ref-alt, chrom removes chr prefix, ref and alt are uppercased.
2. rsID is optional secondary match only.
3. Default filter returns pathogenic and likely_pathogenic only.
4. Ordering is deterministic.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_clinvar_matcher_contract.py

---

## Contract: API_ClinVarMatch_v1

### Type

API Endpoint

### Specification

| Field | Value |
|-------|-------|
| Method | POST |
| Path | /api/clinvar-match |
| Input | JSON body with session_id and optional significance filter |
| Output | JSON response with success, summary, matches |

### Validation Rules

1. Missing or invalid session_id returns HTTP 400 with success false.
2. Success returns HTTP 200 with deterministic matches ordering.
3. No network calls in contract tests.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_clinvar_endpoint_contract.py

---

## Contract: Data_PGx_Final_TSV_v1

### Type

Data File

### Specification

| Field | Value |
|-------|-------|
| Path | /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/pgx/final.tsv |
| Format | TSV |
| Encoding | UTF-8 |
| Header row | Yes |

### Validation Rules

1. Required columns: gene, diplotype, phenotype, drug, recommendation
2. Minimum rows: at least 1 data row.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_parser_contract.py

---

## Contract: API_PGxSummary_v1

### Type

API Endpoint

### Specification

| Field | Value |
|-------|-------|
| Method | POST |
| Path | /api/pgx-summary |
| Input | JSON body selecting a deterministic source |
| Output | JSON response with success, summary, disclaimer_tags |

### Validation Rules

1. Response is deterministic.
2. disclaimer_tags is present and non-empty.
3. No network calls in contract tests.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_endpoint_contract.py

---

## Contract: API_ChatCounseling_v1

### Type

API Endpoint

### Specification

| Field | Value |
|-------|-------|
| Method | POST |
| Path | /api/chat |
| Input | JSON body with message and optional context session reference |
| Output | JSON response with success, answer, disclaimer_tags, citations, risk_level |

### Required Response Keys

- success
- answer
- disclaimer_tags
- citations
- risk_level
 - (Optional extension, C8.B4) llm

### Validation Rules

1. disclaimer_tags is always present and non-empty.
2. citations is always present and references known IDs produced by the facts model.
3. risk_level is one of low, medium, high, critical.
4. No network calls in contract tests.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_endpoint_contract.py

---

## High-Risk Domain Contracts

### Disclaimer Contract

- Every /api/chat response MUST include disclaimer_tags.
- disclaimer_tags MUST be a non-empty list.
- Minimum accepted tags: not_medical_advice, consult_professional, research_only, no_emergency_use.

### Citation Contract

- Every /api/chat response MUST include citations.
- Each citation MUST reference a known ID string produced by the facts model.

### Risk Tag Contract

- Every /api/chat response MUST include risk_level and it MUST be one of low, medium, high, critical.

---

## Cycle 5 (Phase 2) UX Contracts (User-Facing Reality)

Cycle 1–4 contracts prove “API shape / toy logic / lints”. Cycle 5 contracts prove “the UI actually exposes and wires those features”.

## Contract: UI_VisibleTraitSearch_v1

### Type

Frontend (HTML + JS)

### Specification

| Field | Value |
|-------|-------|
| HTML Path | /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html |
| Visible Search Input ID | trait-search-input |
| Suggestions Container ID | trait-search-results |
| Selected EFO ID Input ID | selected-efo-id |
| Endpoint | POST /api/search-traits |

### Validation Rules

1. The visible search box must use POST /api/search-traits while the user types (debounce OK).
2. The contract-required elements must not be hidden via `display:none` + `aria-hidden=true` in the default UI.
3. "Obes" / "obes" must yield "obesity" as the first suggestion item shown to the user.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_ui_visible_trait_search_contract.py

---

## Contract: UI_Panels_ClinVar_PGx_v1

### Type

Frontend (HTML + JS)

### Specification

| Field | Value |
|-------|-------|
| HTML Path | /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html |
| Tab Button IDs | tab-gwas, tab-clinvar, tab-pgx, tab-chat |
| Panel IDs | panel-gwas, panel-clinvar, panel-pgx, panel-chat |
| ClinVar Run Button ID | run-clinvar-btn |
| PGx Run Button ID | run-pgx-btn |
| ClinVar Result Container ID | clinvar-results |
| PGx Result Container ID | pgx-results |
| Endpoints | POST /api/clinvar-match, POST /api/pgx-summary |

### Validation Rules

1. ClinVar(rare variant) and PGx must be visible as **tabs** in the UI, not only implemented as backend endpoints.
2. Default visibility rule: before VCF upload succeeds (no session_id), `tab-clinvar`, `tab-pgx`, `tab-chat` are hidden or disabled and present a clear “upload first” UX.
3. After VCF upload succeeds (session_id exists), UI must enable/show `tab-clinvar`, `tab-pgx`, `tab-chat`.
4. UI must call /api/clinvar-match and /api/pgx-summary using the current session_id obtained from /api/upload-vcf.
5. UI must render results into the page (not only console logs), inside `clinvar-results` / `pgx-results`.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_ui_panels_clinvar_pgx_contract.py

---

## Contract: API_Chat_SessionFacts_v2

### Type

API Endpoint

### Specification

| Field | Value |
|-------|-------|
| Method | POST |
| Path | /api/chat |
| Input | JSON body with message, and session_id (required when available) |
| Output | JSON response with success, answer, disclaimer_tags, citations, risk_level |

### Validation Rules

1. If session_id is provided and the session has any facts available, /api/chat must produce a non-empty answer and must not return a "no facts loaded" message.
2. disclaimer_tags and citations remain mandatory on every response.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_session_facts_contract.py

---

## Contract: Data_Reference_URL_Fallback_v2

### Type

Backend Output Contract (Customer-Friendly Variants)

### Specification

| Field | Value |
|-------|-------|
| Module | /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/customer_friendly_processor.py |
| Field | variants[].reference |

### Validation Rules

1. variants[].reference must be a URL string when any study link is available (PubMed URL preferred, otherwise GWAS study URL).
2. The literal string "No publication reference available" must not appear in end-user variants[].reference outputs.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_url_fallback_contract.py

---

## Cycle 6 (Phase 3) Online + Local LLM Contracts

## Contract: API_SearchTraits_RemoteGWASCatalog_v2

### Type

API Endpoint (with optional remote fallback)

### Specification

| Field | Value |
|-------|-------|
| Method | POST |
| Path | /api/search-traits |
| Local source | data/trait_list.json (fallback: gwas_dashboard_package/config/efo_mapping.json) |
| Remote source | GWAS Catalog REST API efoTraits search |
| Remote URL pattern | https://www.ebi.ac.uk/gwas/rest/api/efoTraits/search/findByEfoTrait?trait=<QUERY> |

### Validation Rules

1. Local fuzzy search remains first.
2. If local results are empty (or top score below a configured threshold), the endpoint must attempt remote GWAS Catalog search.
3. Remote is controlled by env/config (default OFF in tests).
4. When remote returns valid traits, the endpoint returns them in the normal results schema and persists them into data/trait_list.json (dedupe).
5. Contract tests must not perform network calls; they must monkeypatch the HTTP client and verify the remote branch is executed.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_remote_cache_contract.py

---

## Contract: API_Chat_OllamaMode_v1

### Type

API Endpoint (local LLM optional)

### Specification

| Field | Value |
|-------|-------|
| Method | POST |
| Path | /api/chat |
| Mode | deterministic (default), ollama (optional) |
| Ollama host env | OLLAMA_HOST (example: http://127.0.0.1:11434) |
| Ollama model env | OLLAMA_MODEL_CHAT (example: llama3.1:8b-instruct or qwen2.5:7b-instruct) |

### Validation Rules

1. In ollama mode, the backend must call the Ollama HTTP API (mocked in tests).
2. The backend must validate LLM output and still enforce disclaimer_tags + citations (non-empty).
3. citations must reference known fact IDs (from facts model / session facts).
4. Contract tests must not require Ollama running; they must monkeypatch the Ollama call and provide a deterministic fake response.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_chat_ollama_mode_contract.py

---

## Contract: Func_PubMed_Meta_Enrichment_v2

### Type

Function (parsing correctness)

### Specification

| Field | Value |
|-------|-------|
| Module | /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py |
| Function | parse_gwas_association_data(raw_associations, trait_name, config) |
| Output Column | PubMed_ID |

### Validation Rules

1. If multiple association records map to the same (rsid, alt) key and any record has PubMed metadata, the output PubMed_ID must be non-empty.
2. PubMed_ID must be normalized to a string integer when possible.
3. No network calls in contract test (use crafted raw_associations list; no HTTP).

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pubmed_meta_enrichment_contract.py

---

## Contract: Data_PGx_ForeGenomics_Report_v1

### Type

Data File

### Specification

| Field | Value |
|-------|-------|
| Snapshot Path | /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/data/pgx/foregenomics_report.tsv |
| Format | TSV (UTF-8, header row) |

### Validation Rules

1. Must include at least these columns: Sample, Drug, Gene, Genotype, Phenotype, Recommendation.
2. Must contain >= 10 unique Drug values (to guarantee “richer than toy”).

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_foregenomics_parser_contract.py

---

## Contract: Func_PGx_ForeGenomics_Parser_v1

### Type

Function

### Specification

| Field | Value |
|-------|-------|
| Module | /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/pgx_foregenomics.py |
| Function | parse_foregenomics_report_tsv(path) |
| Output | Normalized DataFrame with gene/drug rows |

### Validation Rules

1. Returns deterministic results from the snapshot TSV.
2. Normalized output must expose at minimum: gene, drug, genotype, phenotype, recommendation, guideline_ids.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_foregenomics_parser_contract.py

---

## Contract: API_PGxSummary_ForeGenomics_v2

### Type

API Endpoint

### Specification

| Field | Value |
|-------|-------|
| Method | POST |
| Path | /api/pgx-summary |
| Input | JSON: {"source": "foregenomics", "session_id": "..."} |
| Output | JSON: {"success": bool, "summary": {...}, "disclaimer_tags": [...]} |

### Validation Rules

1. For source="foregenomics", summary.drugs must include >= 10 unique drugs (derived from the snapshot).
2. For a valid session_id, the summary is stored into UPLOADS[session_id]["pgx_summary"] for chat facts.
3. No network calls in contract tests.
4. (Optional extension, C8.B2) If `FOREGENOMICS_PGX_REPORT_PATH` is set, the backend must read that file for source="foregenomics" instead of the snapshot path.

### Test File

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_pgx_endpoint_foregenomics_contract.py
