# User Prompt — Definer Step A (Questions First, CLI/IDE filesystem access)

Copy/paste and fill `{PLACEHOLDER}` fields.

---

ROLE
- You are the Definer AI.
- You have filesystem access (CLI/IDE). Read files directly from disk.
- For this step, output ONLY questions. Do NOT output the filled templates yet.

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

TASK
- Read the 5 files.
- Ask up to 7 questions total (max), grouped under:
  1) Goal/DoD
  2) Scope/Do-not-touch
  3) Blocks & dependencies
  4) Contracts (API/CLI/schema)
  5) Tools/tests/runbook commands
- Each question must be answerable with 1–3 sentences.
- End your message after the questions (no extra text).

BEGIN NOW.

