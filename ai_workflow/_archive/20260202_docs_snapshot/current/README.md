# AI Workflow (Docs-Driven) — Operator Guide

This folder (`ai_workflow/`) is a **general-purpose workflow** to run analysis/coding tasks with 3 AI roles:

- **Definer**: turns a brief into blocks + contracts + scope + runnable runbook
- **Executor**: implements exactly one block (patch-only or edited-file output)
- **Strategy/Reviewer**: diagnoses tool failures and writes fix instructions (no code)

The workflow is designed to be used from **CLI/IDE agents with filesystem access**, so the AI can read templates directly.

---

## Canonical flow (the only loop you need)

Once Gate0 docs are filled, you repeat this loop per block:

1) **Executor runs ONE block**
   - Recommended: tool-enabled Executor (edits files + runs Gate1 + prints next prompt)
2) **Gate1 decides PASS/FAIL (tools + scope)**
   - In tool-enabled mode: Executor runs it.
   - In patch-only chat mode: you run it once.
3) **If FAIL → Strategy/Reviewer writes fix instructions → Executor retries**
4) **If PASS → copy the printed “next Executor prompt” and continue**

This design exists because PASS/FAIL must be decided by tools (pytest/ruff/scope), not by LLM “confidence”.

---

## Role boundaries (non-negotiable)

- **Definer / Strategy-Reviewer**: define/diagnose only. **Must NOT run commands** or claim PASS/FAIL.
- **Executor**: the only role that edits files and runs tools (Gate1/Gate2) in IDE/CLI tool mode.
- **Human**: triggers the next step (or delegates to a tool-enabled Executor) but should not be forced to run multi-step command sequences.

---

## Fast start (simple)

1) You edit only 2 files first:
- `01_PROJECT_BRIEF_TEMPLATE.md` → goal(3 lines) + constraints(3 lines) + DoD
- `05_RUNBOOK_TEMPLATE.md` → absolute paths only (project_root, venv, requirements, test commands)

2) Start Definer (spec writer) in one conversation:
- System prompt: `10_PROMPTS/P1_DEFINER_B2C.md`
- User message (copy/paste, then edit the project root path):

    Project root is `{PROJECT_ROOT_ABS}`.
    Read `ai_workflow/01_PROJECT_BRIEF_TEMPLATE.md` and `ai_workflow/05_RUNBOOK_TEMPLATE.md` first.
    Ask up to 5 clarification questions.
    After I answer, output complete filled text for ALL 5 docs:
    - `ai_workflow/01_PROJECT_BRIEF_TEMPLATE.md`
    - `ai_workflow/02_B2C_SPEC_TEMPLATE.md`
    - `ai_workflow/03_CONTRACTS_TEMPLATE.md`
    - `ai_workflow/04_SCOPE_RULES_TEMPLATE.md`
    - `ai_workflow/05_RUNBOOK_TEMPLATE.md`
    Include absolute-path FILE headers in your output (so I can paste/overwrite files reliably).

3) Paste Definer’s outputs into the 5 files above.

4) Verify Gate 0 (do not trust “I finished” claims):

```bash
cd {PROJECT_ROOT_ABS}
python ai_workflow/tools/validate_gate0_docs.py
```

Gate 0 is PASS only when it prints:

    GATE0_DOCS: PASS

---

## Executor usage (minimal, IDE/CLI filesystem mode)

In IDE/CLI agents, the Executor can read files directly from disk. You should NOT paste large file contents.

### Recommended: tool-enabled Executor (zero operator commands)

If your Executor can read files + run shell commands (IDE/CLI agent), use:
- System prompt: `10_PROMPTS/P4_EXECUTOR_TOOL_MODE_AUTORUN.md`
- User prompt: `11_USER_PROMPTS/U3B_EXECUTOR_TOOL_MODE_AUTORUN.md`

In this mode, the Executor:
- edits code on disk for the chosen block
- runs Gate1 itself (`--skip-apply --handoff-packet`)
- outputs a short “Block Result” summary, then the next handoff prompt text (PASS → next Executor, FAIL → Reviewer)

### Fallback: patch-only chat Executor (one operator command)

Run Gate 1 (apply + tools review) with ONE command.

Use this ONLY when your Executor cannot run commands / cannot edit files directly (chat-style).

Recommended (macOS): copy the Executor output to your clipboard, then run:

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python ai_workflow/tools/run_block_gate1.py --block C1.B2 --attempt 1 --executor-output-clipboard --copy-handoff
```

What you get:
- It applies the Executor output (diff or edited-file).
- It runs the block’s `tests_required`.
- It enforces scope (only `target_files` may change).
- It writes logs under `ai_workflow/_runs/<block_id>_attemptN/`.
- It prints PASS/FAIL as JSON.
- It copies the next handoff prompt to clipboard:
  - PASS → next Executor prompt
  - FAIL → Reviewer prompt

If you are not on macOS, omit `--executor-output-clipboard --copy-handoff` and paste to stdin (Ctrl-D).

---

## Reviewer usage (minimal)

If a block fails tools/tests:

1) Set the Strategy/Reviewer system prompt:
- `10_PROMPTS/P2_STRATEGY_REVIEWER.md`

2) Provide only:
- PROJECT_ROOT_ABS
- BLOCK_NAME
- ATTEMPT
- tell it to read the block spec + scope + saved logs from `ai_workflow/_runs/`

---

## Minimal setup (you do this once per project)

Edit only these two first (small seed, 5–10 minutes):

1) `01_PROJECT_BRIEF_TEMPLATE.md`
- 3–7 bullets: goal, constraints, risk, DoD, “do_not_touch” areas.

2) `05_RUNBOOK_TEMPLATE.md`
- Fill absolute paths and commands:
  - `{PROJECT_ROOT}`, `{VENV_PATH}`, `{REQUIREMENTS_PATH}`, `{TEST_PATH}`
  - copy/pasteable `pytest ...` and `ruff ...`

Everything else can be generated/iterated with Definer by conversation.

---

## Gate2 (final integrity check)

After all blocks pass Gate1, run Gate2 to validate full integrity (not just per-block):

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python ai_workflow/tools/run_gate2.py
```

Gate2 checks:
- Full `contract_tests`
- Full `ruff` across both packages
- Import smoke (no server run)

---

## When Gate2 passes but the app still “doesn’t work” (Phase 2 / Cycle 5)

Gate2는 “코드 무결성”만 보장한다. 실제 UI/UX가 별로면(검색 품질, 레퍼런스, ClinVar/PGx 탭/패널, chat facts) **Cycle 5(C5.B1~C5.B4)** 를 추가로 수행한다.

권장 흐름(Executor tool-mode):
- C5.B1 → C5.B2 → C5.B3 → C5.B4 (각 블록마다 Gate1 1회)
- 다시 Gate2 + `ai_workflow/tools/run_smoke_app.py`

---

## Start conversations (standard protocol)

Use these as **user messages**. Pair them with the system prompts in `10_PROMPTS/`.

### 1) Definer (two-step: questions → write docs)

System prompt:
- `10_PROMPTS/P1_DEFINER_B2C.md`

User message step A (questions only):
- `11_USER_PROMPTS/U1A_DEFINER_QUESTIONS.md`

After you answer the questions, user message step B (write all docs):
- `11_USER_PROMPTS/U1B_DEFINER_WRITE_DOCS.md`

### 2) Executor (one block)

System prompt:
- `10_PROMPTS/P3_EXECUTOR_PATCH_ONLY.md`

User message:
- `11_USER_PROMPTS/U3_START_EXECUTOR.md`

### 3) Strategy/Reviewer (on FAIL)

System prompt:
- `10_PROMPTS/P2_STRATEGY_REVIEWER.md`

User message:
- `11_USER_PROMPTS/U2_START_STRATEGY_REVIEWER.md`

---

## Why “questions first”?

Because most failures come from spec ambiguity, not coding skill:
- wrong endpoint path/method
- missing/extra response keys
- touching out-of-scope files
- tests not runnable

A short Q&A up front makes the spec executable and reduces retries.
