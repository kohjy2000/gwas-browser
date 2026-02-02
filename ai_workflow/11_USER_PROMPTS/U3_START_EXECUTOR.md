# User Prompt Template — Start Executor Session (one block)

Copy/paste and fill `{PLACEHOLDER}` fields.

---

ROLE
- You are the Executor AI.
- Implement exactly ONE block from the B2C spec.
- Output MUST follow the patch-only rules from the system prompt. No prose.

PROJECT (ABSOLUTE)
- PROJECT_ROOT: {PROJECT_ROOT_ABS}
- TODAY: {YYYY-MM-DD}

BLOCK
- BLOCK_NAME: {BLOCK_NAME}
- ATTEMPT: {ATTEMPT_N} / {MAX_ATTEMPTS}

HARD CONSTRAINTS (RESTATE)
- Modify ONLY files in `target_files` for this block.
- Never touch `do_not_touch`.
- If you are not 100% confident your unified diff context lines match, use Edited File format.
- Output file paths in your patch as project-relative paths (strip `{PROJECT_ROOT_ABS}/`).
- I will save your raw output into `/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/_runs/` so the next session can continue.

FILE ACCESS MODE (IMPORTANT)
- You are running in an IDE/CLI agent with filesystem access.
- You MUST read the required files directly from disk. Do NOT ask me to paste full file contents unless you truly cannot access files.

FILES TO READ (FROM DISK)
1) {PROJECT_ROOT_ABS}/ai_workflow/02_B2C_SPEC_TEMPLATE.md  (locate the block section for {BLOCK_NAME})
2) {PROJECT_ROOT_ABS}/ai_workflow/03_CONTRACTS_TEMPLATE.md (relevant contracts for this block)
3) {PROJECT_ROOT_ABS}/ai_workflow/04_SCOPE_RULES_TEMPLATE.md (scope for this block)
4) Every path listed under this block’s `read_files`
5) (If retry) {PROJECT_ROOT_ABS}/ai_workflow/_runs/{BLOCK_NAME}_attempt{ATTEMPT_N}/reviewer.md (if it exists)

OUTPUT REQUIREMENT (STRICT)
- Output exactly one of:
  - NOOP
  - BEGIN_DIFF ... END_DIFF
  - BEGIN EDITED FILE ... END EDITED FILE
- Output nothing else.

BEGIN NOW.
