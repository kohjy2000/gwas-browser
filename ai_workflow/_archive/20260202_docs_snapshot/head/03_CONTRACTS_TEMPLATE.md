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
