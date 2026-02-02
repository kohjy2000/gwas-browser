# Project Brief

## 1. Project Name

GWAS Browser Toy Cycle 1 to 4

## 2. One-Line Summary

A Flask-based GWAS browser and variant analyzer with GWAS trait search, local GWAS cache, GWAS parsing reference-fix rules, ClinVar pathogenic matching from uploaded VCF using a toy TSV database, deterministic PGx summary from a toy final TSV, and a facts-based counseling chat endpoint that enforces disclaimers and citations.

## 3. Goals

1. Cycle 1: Keep existing contract tests passing while locking Cycle 1 behavior for trait search, cache behavior, reference-fix parsing, trait list handling, and frontend gating.
2. Cycle 2: Add VCF upload to ClinVar pathogenic matching report using a fixed toy ClinVar TSV and a fixed normalization key.
3. Cycle 3: Add deterministic PGx summary from a toy final TSV with minimal-context parsing rules.
4. Cycle 4: Add a facts-based counseling chat endpoint with mandatory disclaimer tags and citations in the response.
5. Cycle 5 (Phase 2): Make the *actual UI/UX* match the intended features (not just contract tests):
   - Visible trait search must behave well for partial inputs (e.g., "Obes" → "obesity" top suggestion, not unrelated items).
   - References must not be a blanket "No publication reference available" when a study URL can be used.
   - ClinVar / PGx / Chat must be visible in the UI and actually callable from the UI.
   - Chat must use session-based facts (no manual facts paste; session_id-driven).
6. Cycle 6 (Phase 3): Add “online + local LLM” capabilities safely:
   - Trait search must consult the GWAS Catalog REST API when local cache has no good match, then persist new traits into the local cache file.
   - Counseling chat must support an Ollama-backed local LLM mode, while preserving disclaimer_tags + citations as mandatory and keeping contract tests network-free via mocking.

## 4. Non-Goals

1. Production clinical decision support or medically validated interpretation.
2. Network-dependent tests. Contract tests must not call external services.
3. Requiring a specific Ollama model tag to exist at test time (model choice must be configurable).

## 5. Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.10.18 |
| Framework | Flask | 3.0.3 |
| Database | None (file-based toy data and parquet cache) | N/A |
| Testing | pytest | 8.4.1 |
| Linter | ruff | 0.1.1 |
| Package Manager | pip | via /Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pip |

## 6. Repository Layout

Project root:

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser

Key paths:

- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/main.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/routes/api.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/index.html
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/static/js/dashboard.js
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/gwas_variant_analyzer/gwas_catalog_handler.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/scripts/update_trait_list.py
- /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests

## 7. Constraints

- Backend must remain Flask and keep the API prefix /api.
- Use the venv interpreter for all runnable commands: /Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python
- Existing Cycle 1 contract tests must keep passing unless explicitly replaced by a new contract:
  - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_search_traits_contract.py
  - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_cache_contract.py
  - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_reference_fix_contract.py
  - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/contract_tests/test_frontend_contract.py
- Contract tests must not depend on network. Any network call must be mocked or monkeypatched.
- Per-block diff scope must be enforced. Only files listed in a block target_files may change.

## 8. Domain Notes

- Domain: Medical (genomics), toy and research-only
- Disclaimer requirement: Yes for Cycle 4 chat responses (mandatory)
- Evidence citation requirement: Yes for Cycle 4 chat responses (mandatory)

## 9. Success Criteria

- Gate 0 doc validation passes:
  - cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
  - /Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python ai_workflow/tools/validate_gate0_docs.py
- All contract tests pass:
  - /Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests
- Linter is clean on touched files:
  - /Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m ruff check gwas_dashboard_package/src gwas_variant_analyzer/gwas_variant_analyzer
- Product UX smoke checks pass (automated; no browser required):
  - /Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python ai_workflow/tools/run_smoke_app.py
