# User Prompt — Definer Step B (Write the 5 Docs)

Copy/paste and fill `{PLACEHOLDER}` fields.

---

ROLE
- You are the Definer AI.
- You have filesystem access (CLI/IDE). Read files directly from disk.
- For this step, output ONLY the filled documents (no extra commentary).

PROJECT (ABSOLUTE)
- PROJECT_ROOT: {PROJECT_ROOT_ABS}
- WORKFLOW_ROOT: {PROJECT_ROOT_ABS}/ai_workflow
- TODAY: {YYYY-MM-DD}

FILES TO READ (FROM DISK)
1) {WORKFLOW_ROOT}/01_PROJECT_BRIEF_TEMPLATE.md
2) {WORKFLOW_ROOT}/02_B2C_SPEC_TEMPLATE.md
3) {WORKFLOW_ROOT}/03_CONTRACTS_TEMPLATE.md
4) {WORKFLOW_ROOT}/04_SCOPE_RULES_TEMPLATE.md
5) {WORKFLOW_ROOT}/05_RUNBOOK_TEMPLATE.md

INPUTS (MY ANSWERS TO YOUR QUESTIONS)
- I will paste concise answers in the next message.

TASK
- Update/fill all 5 documents to a “first executable draft”.
- Make blocks small (1–2 days each).
- Every block must include:
  - target_files / read_files / do_not_touch
  - tests_required (copy/pasteable commands)
  - acceptance criteria (concrete PASS conditions)
  - allow_noop (true/false)
- Set `max_attempts_per_block = 3`.
- Do NOT leave template placeholders (e.g., `{PROJECT_ROOT}`, `{BLOCK_NAME_1}`, `{REL_PATH_1}`, `{CONTRACT_NAME_1}`) in the output.
- The filled docs must pass Gate 0 doc validation:
  - `python ai_workflow/tools/validate_gate0_docs.py` must print `GATE0_DOCS: PASS` when run from `{PROJECT_ROOT_ABS}`.

OUTPUT FORMAT (STRICT)
- Output 5 sections, in this exact order.
- Each section must begin with:
  FILE: <absolute path>
  VERSION: v1
  LAST_UPDATED: {YYYY-MM-DD}

1) FILE: {WORKFLOW_ROOT}/01_PROJECT_BRIEF_TEMPLATE.md
2) FILE: {WORKFLOW_ROOT}/02_B2C_SPEC_TEMPLATE.md
3) FILE: {WORKFLOW_ROOT}/03_CONTRACTS_TEMPLATE.md
4) FILE: {WORKFLOW_ROOT}/04_SCOPE_RULES_TEMPLATE.md
5) FILE: {WORKFLOW_ROOT}/05_RUNBOOK_TEMPLATE.md

BEGIN NOW.
