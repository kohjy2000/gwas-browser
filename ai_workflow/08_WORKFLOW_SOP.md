# Workflow SOP (Standard Operating Procedure)

> This document defines the standard execution loop for the Agent OS workflow.
> All participants (Human, Definer, Executor, Strategy/Reviewer) must follow this procedure.

---

## Roles

| Role | Responsibility | Output |
|------|---------------|--------|
| **Definer** | Produces B2C spec, contracts, scope rules from project brief | Documents (02, 03, 04) |
| **Executor** | Implements code changes for one block at a time | Unified diff patch or edited files |
| **Tools** (Human/CI) | Runs tests, linter, diff-scope check | PASS / FAIL + logs |
| **Strategy/Reviewer** | Diagnoses failures, produces fix instructions | Diagnosis + fix plan |
| **Human Operator** | Oversees the loop, makes decisions at halt points | Go / No-go decisions |

---

## The Standard Loop

```
┌──────────────────────────────────────────────────────────┐
│                    PHASE 0: DEFINE                        │
│                                                          │
│  Human + Definer → Project Brief → B2C Spec → Contracts │
│                    → Scope Rules                         │
│                         │                                │
│                    ┌────▼────┐                            │
│                    │ Gate 0  │ (Document validation)      │
│                    └────┬────┘                            │
│                         │ PASS                           │
│                         ▼                                │
│              ┌─────────────────────┐                     │
│              │  PHASE 1: EXECUTE   │                     │
│              │  (per block)        │                     │
│              │                     │                     │
│              │  ┌───────────┐      │                     │
│          ┌──►│  │ Executor  │      │                     │
│          │   │  └─────┬─────┘      │                     │
│          │   │        │ patch      │                     │
│          │   │  ┌─────▼─────┐      │                     │
│          │   │  │   Tools   │      │                     │
│          │   │  │ (Human)   │      │                     │
│          │   │  └─────┬─────┘      │                     │
│          │   │        │            │                     │
│          │   │  ┌─────▼─────┐      │                     │
│          │   │  │  Gate 1   │      │                     │
│          │   │  └─────┬─────┘      │                     │
│          │   │     ┌──┴──┐         │                     │
│          │   │   PASS   FAIL       │                     │
│          │   │     │      │        │                     │
│          │   │     │  ┌───▼───┐    │                     │
│          │   │     │  │Strat/ │    │                     │
│          │   │     │  │Review │    │                     │
│          │   │     │  └───┬───┘    │                     │
│          │   │     │      │ fix    │                     │
│          └───┼─────┼──────┘        │                     │
│              │     │               │                     │
│              │     ▼ next block    │                     │
│              └─────────────────────┘                     │
│                         │ all blocks done                │
│                    ┌────▼────┐                            │
│                    │ Gate 2  │ (Integration)              │
│                    └─────────┘                            │
└──────────────────────────────────────────────────────────┘
```

---

## Detailed Loop Steps

### Step 1: Executor Invocation

- Input: Block spec (from `02_B2C_SPEC_TEMPLATE.md`) + read_files contents + fix instructions (if retry)
- System prompt: `10_PROMPTS/P3_EXECUTOR_PATCH_ONLY.md`
- Output: One of: `NOOP`, unified diff (`BEGIN_DIFF`...`END_DIFF`), or edited files (`BEGIN EDITED FILE`...`END EDITED FILE`)

### Step 2: Tools Execution (Human/CI)

The human operator (or CI pipeline) processes the Executor output and runs validation:

1. **Parse Executor output** according to format:
   - **Format 2** (`BEGIN_DIFF`...`END_DIFF`): Strip the marker lines. Save only the diff content between them as `output.patch`. Run `patch -p1 --dry-run < output.patch`, then `patch -p1 < output.patch`.
   - **Format 3** (`BEGIN EDITED FILE`...`END EDITED FILE`): For each block, extract file contents between markers. Backup the original target file, then overwrite it with the extracted contents.
   - **Format 1** (`NOOP`): No file changes. Skip to step 2.
2. **Contract tests**: `pytest {test_path} -v`
3. **Linter**: `ruff check {target_files} --select E9,F63,F7,F82`
4. **Diff-scope check**: Verify modified files are all in `target_files`

### Step 3: Gate 1 Evaluation

- **ALL pass** → Block = PASS. Advance to next block (go to Step 1 for next block).
- **ANY fail** → Block = FAIL. Go to Step 4.

### Step 4: Strategy/Reviewer Invocation

- Input: Failure logs (test output, lint errors, patch apply errors) + block spec + current file state
- System prompt: `10_PROMPTS/P2_STRATEGY_REVIEWER.md`
- Output: Root cause diagnosis + fix instructions

### Step 5: Retry Decision

- Feed fix instructions back to Executor → Return to Step 1.
- **Loop Breaker applies** (see below).

---

## Loop Breaker Rule (N=3)

> **If the same root cause causes failure 3 consecutive times for the same block, the loop HALTS.**

### Definition of "Same Root Cause"

Two failures have the same root cause if:
- The same test(s) fail with the same assertion error, OR
- The same lint rule triggers on the same file/line, OR
- The patch fails to apply for the same structural reason (wrong context lines, missing file)

### On Halt

1. **Stop execution** for this block.
2. Log the failure in `07_ISSUES_LOG_TEMPLATE.md` with severity `CRITICAL`.
3. Record the decision in `06_DECISION_LOG_TEMPLATE.md`.
4. **Return to Phase 0**: The spec for this block must be redefined.
   - The Definer re-examines the block spec, contracts, and scope rules.
   - The block spec is updated to address the root cause.
   - Gate 0 is re-run on the updated spec.
5. Re-enter Phase 1 with the updated spec.

### Human Override

The human operator may override the halt at their discretion:
- **Skip**: Mark block as skipped, continue to next block.
- **Force**: Accept current output despite failures.
- **Reset**: Reset to a different block index and restart.

---

## Block State Machine

```
  ┌─────────┐
  │ PENDING │
  └────┬────┘
       │ (start)
  ┌────▼────┐
  │EXECUTING│◄──────────────────┐
  └────┬────┘                   │
       │ (tools complete)       │ (retry with fix)
  ┌────▼────┐              ┌────┴────┐
  │ Gate 1  │──── FAIL ───►│STRATEGIST│
  └────┬────┘              └─────────┘
       │ PASS                   │
  ┌────▼────┐              (N=3 same cause)
  │  PASS   │                   │
  └─────────┘              ┌────▼────┐
                           │  HALT   │
                           └─────────┘
```

---

## Retry Accounting

| Attempt | Action |
|---------|--------|
| 1 | Executor produces initial output. Tools run. |
| 2 (on FAIL) | Strategist diagnoses. Executor retries with fix instructions. Tools run. |
| 3 (on FAIL) | Strategist diagnoses again. Executor retries. Tools run. |
| 3+ same cause | **HALT** — Loop breaker triggers. |

---

## Communication Protocol

All inter-agent communication is **file-based**:

| From → To | File Pattern |
|-----------|-------------|
| Definer → Executor | `02_B2C_SPEC_TEMPLATE.md` (block section) + read_files |
| Executor → Tools | Patch file or edited-file output |
| Tools → Reviewer | Test logs, lint output, diff |
| Reviewer → Strategist | Failure report |
| Strategist → Executor | Fix instructions |
