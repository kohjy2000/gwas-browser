# Definer Bundle

This file bundles the system prompt + workflow templates.
Use it only when your Definer AI cannot read local files.

PROJECT_ROOT: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
WORKFLOW_ROOT: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow


===== SYSTEM_PROMPT (P1_DEFINER_B2C.md)
PATH: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/10_PROMPTS/P1_DEFINER_B2C.md =====

# System Prompt: Definer (B2C Spec Generator)

You are the **Definer** agent in a multi-agent software engineering workflow. Your job is to produce a complete, unambiguous Block-to-Code (B2C) specification from a Project Brief.

---

## File Access (CLI/IDE Mode)

This workflow is intended to run in a CLI/IDE agent that can **read local files**.

1) **If you have filesystem access**: you MUST read the required files directly from disk. Do NOT ask the human to copy/paste templates.

2) **If you do NOT have filesystem access**: STOP immediately and ask the human to provide the full contents of the required files (do not proceed by guessing).

When filesystem access is available, prefer absolute paths to avoid ambiguity.

---

## Your Role

Given a filled-in Project Brief (`01_PROJECT_BRIEF_TEMPLATE.md`) and the current state of the codebase, you produce:

1. **B2C Spec** (`02_B2C_SPEC_TEMPLATE.md`) — ordered list of blocks with target files, dependencies, tests, and acceptance criteria.
2. **Contracts** (`03_CONTRACTS_TEMPLATE.md`) — testable acceptance contracts for each deliverable.
3. **Scope Rules** (`04_SCOPE_RULES_TEMPLATE.md`) — file-level access control per block.

---

## Hard Rules

1. **Every block must be atomic.** One block = one logical unit of work. If a block tries to do two unrelated things, split it.
2. **Every block must be testable.** If you cannot define at least one concrete test for a block, the block is too vague.
3. **Dependencies must form a DAG.** No circular dependencies. Every `depends_on` must reference a block that appears earlier in the execution order.
4. **Scope must be explicit.** Every block must list `target_files`, `read_files`, and `do_not_touch`. No implicit assumptions.
5. **No overlap in target_files and do_not_touch.** A file cannot be both modifiable and untouchable in the same block.
6. **Contracts must be concrete.** Use specific HTTP status codes, exact JSON key names, minimum row counts — not vague descriptions like "should work correctly."
7. **Test commands must be runnable.** Every `tests_required` entry must be a shell command that a human can copy-paste and execute.

---

## Output Format

Your output must contain exactly three sections, clearly separated:

```
## B2C SPEC

(Fill in 02_B2C_SPEC_TEMPLATE.md format for each block)

## CONTRACTS

(Fill in 03_CONTRACTS_TEMPLATE.md format for each deliverable)

## SCOPE RULES

(Fill in 04_SCOPE_RULES_TEMPLATE.md format for each block)
```

---

## Process

1. Read the Project Brief carefully.
2. Identify the deliverables (endpoints, data files, functions, UI components).
3. Order them by dependency (what must exist before what).
4. For each deliverable, define a block:
   - What files need to be created or modified?
   - What existing files provide context?
   - What files must not be touched?
   - What tests verify success?
   - What are the concrete acceptance criteria?
5. Define contracts for each endpoint/data file.
6. Cross-check:
   - Every file mentioned in `target_files` has at least one test covering it.
   - Every `do_not_touch` file is consistent across blocks.
   - Every dependency chain is acyclic.

---

## Required Inputs (read from disk when available)

At minimum, read these (project-specific absolute paths should be provided by the operator):

- Project brief: `.../ai_workflow/01_PROJECT_BRIEF_TEMPLATE.md`
- B2C spec template: `.../ai_workflow/02_B2C_SPEC_TEMPLATE.md`
- Contracts template: `.../ai_workflow/03_CONTRACTS_TEMPLATE.md`
- Scope rules template: `.../ai_workflow/04_SCOPE_RULES_TEMPLATE.md`

If the operator provides a filled Project Brief, treat it as source-of-truth and generate the B2C/Contracts/Scope accordingly.

---

## Domain Safety (High-Risk Projects)

If the Project Brief indicates a high-risk domain (medical, legal, financial):

1. **Every user-facing endpoint** must have a disclaimer contract.
2. **Every factual claim** must have a citation contract.
3. Add a `risk_level` field to response contracts where applicable.
4. Include at least one test that verifies disclaimer presence.
5. Note these requirements explicitly in the relevant block's acceptance criteria.

---

## Quality Checklist (Self-Review Before Output)

Before producing your output, verify:

- [ ] Every block has a non-empty `target_files` list.
- [ ] Every block has at least one `tests_required` entry.
- [ ] No `target_files` / `do_not_touch` conflicts.
- [ ] Dependency chain is acyclic.
- [ ] Every contract has concrete validation rules (not vague).
- [ ] Test commands are copy-pasteable.
- [ ] High-risk domain safety requirements are addressed (if applicable).



===== 01_PROJECT_BRIEF_TEMPLATE.md
PATH: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/01_PROJECT_BRIEF_TEMPLATE.md =====

# Project Brief

> Fill in all `{PLACEHOLDER}` fields. Delete instructional comments after filling.

## 1. Project Name

`{PROJECT_NAME}`

## 2. One-Line Summary

{One sentence describing what this project does.}

## 3. Goals

<!-- List 2-5 concrete, measurable goals. -->

1. {GOAL_1}
2. {GOAL_2}
3. {GOAL_3}

## 4. Non-Goals (Explicit Exclusions)

<!-- What is deliberately out of scope for this project phase? -->

1. {NON_GOAL_1}
2. {NON_GOAL_2}

## 5. Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | {e.g., Python} | {e.g., 3.10} |
| Framework | {e.g., Flask} | {e.g., 3.x} |
| Database | {e.g., SQLite / PostgreSQL / None} | {version} |
| Testing | {e.g., pytest} | {version} |
| Linter | {e.g., ruff} | {version} |
| Package Manager | {e.g., pip / poetry / npm} | {version} |

## 6. Repository Layout

<!-- Show the top-level directory structure relevant to this project. -->

```
{PROJECT_ROOT}/
  src/
  tests/
  data/
  ...
```

## 7. Constraints

<!-- Hard constraints that all agents must respect. -->

- {CONSTRAINT_1: e.g., "No external API calls in tests"}
- {CONSTRAINT_2: e.g., "All endpoints must return JSON"}
- {CONSTRAINT_3: e.g., "Python 3.10 compatibility required"}

## 8. Domain-Specific Notes

<!-- For high-risk domains (medical, legal, financial), fill this section. Otherwise delete. -->

- **Domain**: {e.g., Medical / Legal / Financial / General}
- **Regulatory requirements**: {e.g., HIPAA, GDPR, None}
- **Disclaimer requirement**: {Yes / No — if Yes, all user-facing outputs must include a disclaimer}
- **Evidence citation requirement**: {Yes / No — if Yes, all factual claims must cite sources}

## 9. Success Criteria

<!-- How do we know the project phase is done? -->

- [ ] All contract tests pass (`pytest contract_tests/`)
- [ ] Linter clean (`ruff check`)
- [ ] {ADDITIONAL_CRITERION_1}
- [ ] {ADDITIONAL_CRITERION_2}



===== 02_B2C_SPEC_TEMPLATE.md
PATH: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/02_B2C_SPEC_TEMPLATE.md =====

# B2C Spec (Block-to-Code Specification)

> Each block represents one atomic unit of work. Blocks execute sequentially.
> Fill in one section per block. Add/remove blocks as needed.

## Global Settings

| Setting | Value |
|---------|-------|
| `max_attempts_per_block` | 3 |
| `loop_breaker_N` | 3 (same-cause fail = halt) |
| `auto_strategist_on_fail` | true |

---

## Block: `{BLOCK_NAME_1}`

### Description

{What this block does, in 1-3 sentences.}

### Dependencies

- Depends on: `{PREVIOUS_BLOCK_NAME}` (or "none" if first block)

### Target Files

<!-- Files the Executor is allowed to create or modify. -->

- `{REL_PATH_1}`
- `{REL_PATH_2}`

### Read Files

<!-- Files the Executor can read for context but must NOT modify. -->

- `{REL_PATH_3}`

### Do Not Touch

<!-- Files that must never be modified under any circumstances. -->

- `{REL_PATH_4}`
- `{REL_PATH_5}`

### Tests Required

<!-- Commands that the Reviewer/Tools will run to validate this block. -->

```
pytest {TEST_PATH} -v
ruff check {TARGET_FILE} --select E9,F63,F7,F82
```

### Acceptance Criteria

<!-- Concrete pass/fail conditions. Reference 03_CONTRACTS_TEMPLATE.md if applicable. -->

1. {CRITERION_1: e.g., "Endpoint returns 200 with required keys"}
2. {CRITERION_2: e.g., "Linter reports 0 errors"}

### Allow NOOP

- `false` (default) / `true`

### Notes

{Any additional context for the Executor.}

---

## Block: `{BLOCK_NAME_2}`

<!-- Copy the section above for each additional block. -->

### Description

{...}

### Dependencies

- Depends on: `{BLOCK_NAME_1}`

### Target Files

- `{...}`

### Read Files

- `{...}`

### Do Not Touch

- `{...}`

### Tests Required

```
{...}
```

### Acceptance Criteria

1. {...}

### Allow NOOP

- `false`

### Notes

{...}

---

## Execution Order Summary

| Order | Block Name | Depends On |
|-------|-----------|------------|
| 1 | `{BLOCK_NAME_1}` | none |
| 2 | `{BLOCK_NAME_2}` | `{BLOCK_NAME_1}` |
| ... | ... | ... |



===== 03_CONTRACTS_TEMPLATE.md
PATH: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/03_CONTRACTS_TEMPLATE.md =====

# Contracts

> Define the acceptance contracts for each deliverable (endpoint, function, data file, etc.).
> These contracts are the source of truth for the Reviewer/Tools gate.

---

## Contract: `{CONTRACT_NAME_1}`

### Type

<!-- One of: API Endpoint, Function, Data File, Configuration, CLI Command -->

`{TYPE}`

### Specification

| Field | Value |
|-------|-------|
| Method / Signature | `{e.g., POST /api/example}` |
| Input | `{e.g., JSON body with keys: query (str), top_k (int)}` |
| Output | `{e.g., JSON with keys: success (bool), results (array)}` |

### Required Response Keys

<!-- For API endpoints: list all keys that MUST be present in a successful response. -->

- `success` (bool)
- `{KEY_2}` ({type})
- `{KEY_3}` ({type})

### Validation Rules

<!-- Concrete, testable assertions. -->

1. `success` is `true` on valid input.
2. `{KEY_2}` is a non-empty array when results exist.
3. HTTP 400 returned when `{INVALID_CONDITION}`.
4. HTTP 500 never exposes internal stack traces.

### Test File

`{REL_PATH_TO_TEST_FILE}`

### Example Request

```json
{
  "query": "example",
  "top_k": 10
}
```

### Example Response (Success)

```json
{
  "success": true,
  "results": [
    {"id": "001", "name": "Example", "score": 0.95}
  ]
}
```

### Example Response (Error)

```json
{
  "success": false,
  "message": "Query too short (minimum 3 characters)"
}
```

---

## Contract: `{CONTRACT_NAME_2}`

<!-- Copy the section above for each additional contract. -->

### Type

`{TYPE}`

### Specification

| Field | Value |
|-------|-------|
| ... | ... |

### Required Response Keys

- ...

### Validation Rules

1. ...

### Test File

`{REL_PATH}`

---

## Data File Contracts

> For blocks that produce data files (CSV, TSV, JSON, VCF, etc.).

### Contract: `{DATA_CONTRACT_NAME}`

| Field | Value |
|-------|-------|
| Path | `{REL_PATH}` |
| Format | `{TSV / CSV / JSON / VCF / ...}` |
| Minimum rows | `{N}` |
| Required columns / keys | `{COL_1, COL_2, ...}` |
| Encoding | `UTF-8` |
| Header row | `{Yes / No}` |

### Validation

```
# Example: check TSV has header + N data rows
head -1 {PATH} | grep -q "{EXPECTED_HEADER}"
wc -l {PATH}  # expect >= {N+1}
```

---

## High-Risk Domain Contracts (Optional)

> Fill this section for medical, legal, or financial projects.

### Disclaimer Contract

- Every user-facing response MUST include a `disclaimer_tags` field.
- `disclaimer_tags` MUST be a non-empty array.
- Accepted tags: `{e.g., "not_medical_advice", "consult_professional", "research_only"}`.

### Citation Contract

- Every factual claim MUST include a `citations` field.
- Each citation MUST reference a known source ID (e.g., `facts.id`, `pubmed_id`).
- Unsupported claims are a FAIL condition.

### Risk Tag Contract

- Responses involving `{HIGH_RISK_TOPIC}` MUST include `risk_level` field.
- Accepted values: `low`, `medium`, `high`, `critical`.



===== 04_SCOPE_RULES_TEMPLATE.md
PATH: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/04_SCOPE_RULES_TEMPLATE.md =====

# Scope Rules

> This document defines file-level access control for every block.
> **Violation of these rules is an immediate FAIL and halt condition.**

---

## Definitions

### `target_files`
Files that the Executor is **allowed to create or modify**. The Executor's output (patch or edited file) MUST only affect files listed here.

### `read_files`
Files that the Executor can **read for context** but MUST NOT modify. These provide necessary background information (e.g., existing imports, data schemas, helper functions).

### `do_not_touch`
Files and directories that MUST NEVER be modified under any circumstances. If an Executor output would affect any file in this list, the entire output is **rejected immediately**.

---

## Enforcement Rules

| Rule | Description | Consequence |
|------|-------------|-------------|
| **R1** | Executor output may only modify files in `target_files`. | FAIL + rollback |
| **R2** | Files in `do_not_touch` must not appear in any diff/patch. | FAIL + rollback |
| **R3** | Files in `read_files` must not appear in any diff/patch. | FAIL + rollback |
| **R4** | Files not listed in any category must not be modified. | FAIL + rollback |
| **R5** | New file creation is only allowed if `allow_missing_targets: true` is set AND the new file path is listed in `target_files`. | FAIL + rollback |

**On any violation**: The Reviewer MUST reject the output, restore all backups, and report the violation. The Strategist then diagnoses the failure.

---

## Per-Block Scope Definitions

### Block: `{BLOCK_NAME_1}`

**target_files:**
- `{REL_PATH_1}`
- `{REL_PATH_2}`

**read_files:**
- `{REL_PATH_3}`
- `{REL_PATH_4}`

**do_not_touch:**
- `{REL_PATH_5}`
- `{DIR_PATH_1}/`

**allow_missing_targets:** `{true / false}`

---

### Block: `{BLOCK_NAME_2}`

**target_files:**
- `{...}`

**read_files:**
- `{...}`

**do_not_touch:**
- `{...}`

**allow_missing_targets:** `{true / false}`

---

## Global Do-Not-Touch List

> Files/directories that are off-limits for ALL blocks in this project.

- `{e.g., .env}`
- `{e.g., credentials/}`
- `{e.g., node_modules/}`
- `{e.g., venv/}`
- `{e.g., .git/}`

---

## Scope Validation Checklist

Use this checklist during Gate 1 review:

- [ ] Every file in the Executor's diff is listed in `target_files` for the current block.
- [ ] No file in `do_not_touch` was modified.
- [ ] No file in `read_files` was modified.
- [ ] No unlisted file was modified.
- [ ] If new files were created, `allow_missing_targets` is `true` and paths match `target_files`.



===== 05_RUNBOOK_TEMPLATE.md
PATH: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/05_RUNBOOK_TEMPLATE.md =====

# Runbook

> Step-by-step instructions for the human operator executing this workflow.
> Fill in `{PLACEHOLDER}` fields for your project.

---

## Prerequisites

### Environment

- [ ] Python `{VERSION}` installed
- [ ] Virtual environment activated: `source {VENV_PATH}/bin/activate`
- [ ] Dependencies installed: `pip install -r {REQUIREMENTS_PATH}`
- [ ] AI models available: `{e.g., ollama list | grep deepseek-r1:32b}`

### AI Execution Mode (Recommended)

This workflow works best when you run AIs in a CLI/IDE agent that can:

- Read local files by absolute path
- (Optionally) edit files directly in the repo

If your AI cannot read local files (typical cloud chat), you must either:

- Use the optional bundle script (below) and paste ONE bundle, or
- Manually paste the required file contents.

### Verify Project Root

```bash
cd {PROJECT_ROOT}
ls {EXPECTED_FILE_OR_DIR}   # Confirm you're in the right place
```

---

## Optional: Generate a single “Definer bundle” file

If you need to feed a cloud chat AI (no filesystem access), create one markdown file that contains all required inputs:

```bash
cd {PROJECT_ROOT}
python ai_workflow/tools/make_definer_bundle.py --out ai_workflow/_bundles/definer_bundle.md
```

Then paste the contents of `ai_workflow/_bundles/definer_bundle.md` into the Definer chat.

---

## Phase 0: Document Preparation

1. Fill in `01_PROJECT_BRIEF_TEMPLATE.md` completely.
2. Define blocks in `02_B2C_SPEC_TEMPLATE.md`.
3. Write contracts in `03_CONTRACTS_TEMPLATE.md`.
4. Set scope rules in `04_SCOPE_RULES_TEMPLATE.md`.
5. Run Gate 0 validation (see `09_QA_GATES.md`).

---

## Phase 1: Block Execution Loop

For each block in execution order:

### Step 1 — Prepare Context

```bash
# Gather the files the Executor needs to read
cat {READ_FILE_1}
cat {READ_FILE_2}
```

### Step 2 — Invoke Executor

Feed the Executor:
- System prompt: `10_PROMPTS/P3_EXECUTOR_PATCH_ONLY.md`
- User message: Block spec from `02_B2C_SPEC_TEMPLATE.md` + file contents from Step 1

### Step 3 — Apply Output

**Format 2 (BEGIN_DIFF...END_DIFF):** Extract only the lines *between* the markers (exclude `BEGIN_DIFF` and `END_DIFF` themselves), save as `output.patch`, then:

```bash
patch -p1 --dry-run < output.patch   # Dry-run first
patch -p1 < output.patch             # Apply if dry-run passed
```

**Format 3 (BEGIN EDITED FILE...END EDITED FILE):** For each block, extract the lines between `BEGIN EDITED FILE <path>` and `END EDITED FILE`, then overwrite the target:

```bash
cp {TARGET_FILE} {BACKUP_DIR}/{TARGET_FILE}.bak   # Backup first
# Write extracted contents to {TARGET_FILE}
```

**Format 1 (NOOP):** No action needed. Proceed to Step 4.

### Step 4 — Run Tools (Gate 1)

```bash
# Run contract tests
pytest {TEST_PATH} -v

# Run linter
ruff check {TARGET_FILES} --select E9,F63,F7,F82

# Verify diff scope
git diff --name-only   # Must only show target_files
```

### Step 5 — Evaluate

- **All tools PASS** → Mark block as PASS. Proceed to next block.
- **Any tool FAIL** → Invoke Strategy/Reviewer (see Step 6).

### Step 6 — Strategy/Reviewer (on FAIL)

Feed the Strategy/Reviewer:
- System prompt: `10_PROMPTS/P2_STRATEGY_REVIEWER.md`
- Failure context: test output, lint output, diff

The Strategist produces a diagnosis and fix instructions.

### Step 7 — Retry

Feed fix instructions back to the Executor along with the original block spec.
Return to Step 2.

**Loop Breaker**: If the same root cause fails 3 times → HALT. Return to Phase 0 and redefine the spec.

---

## Phase 2: Integration

After all blocks pass Gate 1:

1. Run full test suite: `pytest {ALL_TESTS_PATH} -v`
2. Run full linter: `ruff check {SRC_PATH}`
3. Run smoke test (if applicable): `{SMOKE_TEST_COMMAND}`
4. Evaluate Gate 2 (see `09_QA_GATES.md`).

---

## Rollback Procedure

If a block corrupts the codebase:

```bash
# Restore from backup (created before each patch apply)
cp -r {BACKUP_DIR}/* {PROJECT_ROOT}/

# Or use git
git checkout -- {AFFECTED_FILES}
```

---

## Log Locations

| Log | Path |
|-----|------|
| Executor raw output | `{RUNS_DIR}/{RUN_ID}/outputs/` |
| Patch apply log | `{RUNS_DIR}/{RUN_ID}/qc/` |
| Reviewer report | `{CYCLE_DIR}/handoff/blocks/` |
| Strategist diagnosis | `{CYCLE_DIR}/handoff/blocks/` |
| Decision log | `06_DECISION_LOG_TEMPLATE.md` |
| Issues log | `07_ISSUES_LOG_TEMPLATE.md` |

