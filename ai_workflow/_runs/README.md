# _runs/ — Minimal cross-session memory

Use this folder to persist “what happened” per block so you can continue even if you start a new AI session.

Recommended per-block attempt folder name:

- `{BLOCK_ID}_attempt{N}` (example: `C1.B2_attempt1`)

Recommended files inside each folder:

- `block.md` — the block section copied from `ai_workflow/02_B2C_SPEC_TEMPLATE.md`
- `executor_output.txt` — raw Executor output (patch-only / edited-file)
- `apply.log` — patch apply output (optional)
- `pytest.log` — test output
- `ruff.log` — lint output
- `changed_files.txt` — output of `git status --porcelain`
- `reviewer.md` — Strategy/Reviewer diagnosis + fix instructions (if FAIL)

The only purpose of this folder is continuity. It is not a build artifact and can be deleted any time.

