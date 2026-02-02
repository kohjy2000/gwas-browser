# QA Gates

> This document defines the three quality gates in the workflow.
> Each gate has explicit pass/fail criteria. No gate may be skipped.

---

## Gate 0: Document & Spec Validation

**When**: Before any code execution begins (end of Phase 0).

**Purpose**: Ensure all specifications are complete, consistent, and unambiguous.

### Checks

| # | Check | Pass Condition |
|---|-------|----------------|
| G0-1 | Project Brief complete | All `{PLACEHOLDER}` fields in `01_PROJECT_BRIEF_TEMPLATE.md` are filled |
| G0-2 | B2C Spec complete | Every block in `02_B2C_SPEC_TEMPLATE.md` has: description, target_files, tests_required, acceptance criteria |
| G0-3 | Contracts defined | Every block with an endpoint or data output has a matching contract in `03_CONTRACTS_TEMPLATE.md` |
| G0-4 | Scope rules defined | Every block has target_files, read_files, do_not_touch in `04_SCOPE_RULES_TEMPLATE.md` |
| G0-5 | No scope conflicts | No file appears in both `target_files` and `do_not_touch` for the same block |
| G0-6 | Dependencies valid | Block dependency chain has no cycles; every `depends_on` references an existing block |
| G0-7 | Test files specified | Every `tests_required` command references a test file path that exists (or is in `target_files` with `allow_missing_targets: true`) |
| G0-8 | Read files exist | Every file in `read_files` exists on disk |
| G0-9 | Domain safety (if applicable) | High-risk domain projects have disclaimer and citation contracts defined |

### Verdict

- **PASS**: All checks pass. Proceed to Phase 1.
- **FAIL**: Fix the failing checks. Re-run Gate 0. Do not proceed until PASS.

---

## Gate 1: Block-Level Validation (Tools Review)

**When**: After each Executor output is applied (per block, per attempt).

**Purpose**: Verify that the Executor's changes are correct, scoped, and functional.

### Checks

| # | Check | Tool | Pass Condition |
|---|-------|------|----------------|
| G1-1 | Patch applies cleanly | `patch -p1 --dry-run` | Exit code 0 |
| G1-2 | Contract tests pass | `pytest {test_path} -v` | All tests pass (exit code 0) |
| G1-3 | Linter clean | `ruff check {target_files} --select E9,F63,F7,F82` | 0 errors |
| G1-4 | Diff scope valid | `diff --name-only` (or equivalent) | All modified files are in `target_files` |
| G1-5 | No do-not-touch violations | File hash comparison | Files in `do_not_touch` are unchanged |
| G1-6 | NOOP check | Patch content analysis | If `allow_noop_patch: false`, patch must be non-empty |
| G1-7 | Syntax valid | `python -m py_compile {file}` (or language equivalent) | Exit code 0 for all modified files |

### Verdict

- **PASS**: All checks pass. Block is complete. Advance to next block.
- **FAIL**: Report failing checks. Invoke Strategist. Retry (up to loop breaker N=3).

### Report Format

```markdown
# Block Tools Review — {BLOCK_NAME}

## Results
- G1-1 patch apply: {PASS/FAIL} (exit={N})
- G1-2 contract tests: {PASS/FAIL} ({N} passed, {M} failed)
- G1-3 lint: {PASS/FAIL} ({N} errors)
- G1-4 diff scope: {PASS/FAIL}
- G1-5 do-not-touch: {PASS/FAIL}
- G1-6 noop check: {PASS/FAIL}
- G1-7 syntax check: {PASS/FAIL}

## Errors
{List of specific error messages, if any}

## Verdict
- {PASS / FAIL}
```

---

## Gate 2: Integration Validation

**When**: After all blocks in a cycle pass Gate 1.

**Purpose**: Verify that all blocks work together correctly.

### Checks

| # | Check | Tool | Pass Condition |
|---|-------|------|----------------|
| G2-1 | Full test suite | `pytest {all_tests_path} -v` | All tests pass |
| G2-2 | Full linter | `ruff check {src_path}` | 0 errors (or only pre-existing warnings) |
| G2-3 | Smoke test | `{smoke_test_command}` | Application starts and responds to health check |
| G2-4 | No regressions | Compare with baseline test count | No previously-passing tests now fail |
| G2-5 | Domain safety (if applicable) | Manual review | Disclaimers present, citations valid |

### Verdict

- **PASS**: Cycle complete. Deliverable is ready.
- **FAIL**: Identify which block(s) caused the integration failure. Re-enter Phase 1 for those blocks.

### Report Format

```markdown
# Integration Review — Cycle {CYCLE_NAME}

## Results
- G2-1 full tests: {PASS/FAIL} ({N} passed, {M} failed, {K} skipped)
- G2-2 full lint: {PASS/FAIL}
- G2-3 smoke test: {PASS/FAIL/SKIPPED}
- G2-4 regressions: {PASS/FAIL} ({N} new failures)
- G2-5 domain safety: {PASS/FAIL/N_A}

## Verdict
- {PASS / FAIL}
```

---

## Gate Summary Matrix

| Gate | When | Scope | Blocker? |
|------|------|-------|----------|
| Gate 0 | Before execution | All documents | Yes — cannot start Phase 1 |
| Gate 1 | Per block attempt | Single block | Yes — block cannot advance |
| Gate 2 | After all blocks pass | Full cycle | Yes — cycle not complete |
