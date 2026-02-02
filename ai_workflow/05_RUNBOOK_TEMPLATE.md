# Runbook

Step-by-step instructions for executing this workflow for this repo.

Project root:

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser

Workflow docs root:

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow

---

## Prerequisites

### Environment

- Python interpreter to use for all commands:
  - /Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python
- Activate venv:
  - source /Users/june-young/Research_Local/08_GWAS_browser/venv/bin/activate
- Install dependencies:
  - /Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pip install -r /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/requirements.txt
  - /Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pip install -r /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_variant_analyzer/requirements.txt
  - /Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pip install -U ruff==0.1.1

### Scope Check Baseline (recommended)

This workflow uses `git status --porcelain` to verify "only target_files changed".

If this folder is not a git repo yet, create a local baseline once:

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
git init
git add -A
```

### Verify Project Root

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
ls /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/gwas_dashboard_package/src/main.py
```

---

## Gate 0 Validation

Gate 0 must PASS before any code execution starts.

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python ai_workflow/tools/validate_gate0_docs.py
```

Expected output:

GATE0_DOCS: PASS

---

## Required Tools Commands

These commands are the tools-first ground truth for PASS or FAIL.

Contract tests:

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests
```

Ruff command, preferred:

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pip install -U ruff==0.1.1
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_dashboard_package/src gwas_variant_analyzer/gwas_variant_analyzer
```

If /Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff is unavailable, fallback:

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
ruff check gwas_dashboard_package/src gwas_variant_analyzer/gwas_variant_analyzer
```

---

## Phase 1: Block Execution Loop

Block definitions and order:

/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/02_B2C_SPEC_TEMPLATE.md

### One-command Gate 1 (recommended)

Instead of manually applying patches and running multiple commands, use:

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python ai_workflow/tools/run_block_gate1.py --block C1.B2 --attempt 1 --executor-output-clipboard --copy-handoff
```

It will:
- read the Executor output from clipboard (macOS) (or stdin if you omit `--executor-output-clipboard`)
- apply it (diff or edited-file; or NOOP)
- run the block’s tests_required commands
- write logs under `ai_workflow/_runs/<block_id>_attemptN/`
- print PASS/FAIL as JSON (and write handoff prompts under `.../prompts/`)
- copy the next handoff prompt to clipboard (PASS → next Executor, FAIL → Reviewer) when `--copy-handoff` is set

### Tool-enabled Executor shortcut (optional)

If your Executor can edit files + run commands (IDE agent / CLI agent), it can run Gate1 by itself:

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python ai_workflow/tools/run_block_gate1.py --block C1.B2 --attempt 1 --skip-apply --copy-handoff --handoff-only
```

This mode assumes the Executor already applied the code edits on disk, so Gate1 only runs tools + scope check + prompt generation.

### Persisting context across sessions (minimal, recommended)

Executor and Strategy/Reviewer do not “remember” previous chats reliably. To continue smoothly across new sessions, keep a small per-block artifact folder:

- Base folder: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/_runs
- One folder per block attempt, e.g.:
  - /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/_runs/C1.B2_attempt1

Store these files (simple, copy/paste from your terminal/chat):
- block.md (the block section copied from 02_B2C_SPEC_TEMPLATE.md)
- executor_output.txt (raw patch-only output from the Executor)
- apply.log (patch apply output, if any)
- pytest.log (test output)
- ruff.log (lint output)
- reviewer.md (Strategy/Reviewer diagnosis + fix steps, if any)

Handoff prompts (auto-generated by the Gate1 runner):
- PASS → next-block Executor prompt:
  - `ai_workflow/_runs/<block_id>_attemptN/prompts/PROMPT_NEXT_EXECUTOR.txt`
- FAIL → Reviewer prompt:
  - `ai_workflow/_runs/<block_id>_attemptN/prompts/PROMPT_REVIEWER.txt`
- FAIL → retry Executor prompt (after reviewer writes `reviewer.md`):
  - `ai_workflow/_runs/<block_id>_attemptN/prompts/PROMPT_RETRY_EXECUTOR.txt`

Rule of thumb:
- Starting a new Executor session: paste block.md + relevant read_files + reviewer.md (if retry).
- Starting a new Reviewer session: paste block.md + executor_output.txt + pytest.log + ruff.log + the changed-files list.

For each block in order:

1. Prepare context
   - Provide the Executor the exact block section plus the contents of every read_files path for that block.
2. Invoke Executor
   - System prompt: /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/10_PROMPTS/P3_EXECUTOR_PATCH_ONLY.md
3. Apply output
   - If output is a unified diff, apply with patch -p1 after a dry-run.
4. Gate 1 tools
   - Run the exact tests_required commands listed in the block.
   - Then verify diff scope:

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
git status --porcelain
```

PASS conditions for Gate 1:
- All commands in tests_required exit with code 0.
- git status --porcelain shows only files listed in target_files for the block.
- No read_files or do_not_touch paths appear in the diff.

Loop breaker:
- If the same root cause fails 3 times on the same block, stop and redefine the spec.

Cycle 3A minimal-context rule:
- For the PGx parser block, provide only the minimal necessary files to the Executor.

---

## Phase 2: Integration

After all blocks pass Gate 1:

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_dashboard_package/src gwas_variant_analyzer/gwas_variant_analyzer
```

Optional smoke test:

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python gwas_dashboard_package/src/main.py
```

---

## Rollback Procedure

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
git checkout -- .
```
