# User Prompt Template — Executor Tool Mode (one block, auto Gate1)

Use this ONLY when your Executor AI can:
- read local files directly from disk, AND
- run shell commands in the project (IDE agent / CLI agent).

Fill `{PLACEHOLDER}` fields and send as ONE user message.

---

ROLE
- You are the Executor AI (tool-enabled).
- Implement exactly ONE block from the B2C spec by editing files on disk.
- After editing, you MUST run Gate 1 locally and output ONLY the next handoff prompt text.

PROJECT (ABSOLUTE)
- PROJECT_ROOT_ABS: {PROJECT_ROOT_ABS}
- VENV_PYTHON_ABS: {VENV_PYTHON_ABS}

BLOCK
- BLOCK_NAME: {BLOCK_NAME}  (example: `C1.B3 Reference Fix PubMed Fill and Association ID`)
- ATTEMPT: {ATTEMPT_N} / {MAX_ATTEMPTS}

HARD CONSTRAINTS
- Modify ONLY files in this block’s `target_files`.
- Never touch any `do_not_touch`.
- Read required files from disk (do NOT ask me to paste file contents).

WHAT TO READ (FROM DISK)
1) {PROJECT_ROOT_ABS}/ai_workflow/02_B2C_SPEC_TEMPLATE.md  (locate the block section for {BLOCK_NAME})
2) {PROJECT_ROOT_ABS}/ai_workflow/03_CONTRACTS_TEMPLATE.md (relevant contracts)
3) {PROJECT_ROOT_ABS}/ai_workflow/04_SCOPE_RULES_TEMPLATE.md (scope)
4) Every path listed under this block’s `read_files`
5) (If retry) {PROJECT_ROOT_ABS}/ai_workflow/_runs/{BLOCK_ID}_attempt{PREV_ATTEMPT}/reviewer.md (if exists)

EXECUTION (YOU MUST DO)
1) Edit the code on disk to satisfy the block’s contracts/tests.
2) Run Gate 1 (tools + scope check + handoff prompt generation) with:

```bash
cd {PROJECT_ROOT_ABS}
{VENV_PYTHON_ABS} ai_workflow/tools/run_block_gate1.py --block {BLOCK_ID} --attempt {ATTEMPT_N} --skip-apply --copy-handoff --handoff-only
```

OUTPUT (STRICT)
- The command above prints ONLY the next handoff prompt text:
  - PASS → next Executor prompt
  - FAIL → Reviewer prompt
- Do NOT include logs, commentary, or explanations.

BEGIN NOW.
