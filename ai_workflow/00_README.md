# Agent OS — General-Purpose Analysis & Coding Workflow

Version: `ver_260201`

## Overview

This document set defines a **general-purpose, multi-agent workflow** for analysis and coding tasks. It is designed so that AI agents (Definer, Executor, Strategy/Reviewer) can read these documents directly and perform structured work without ambiguity.

The workflow is **project-agnostic**. To use it for a specific project, copy this folder and fill in the templates.

## Document Index

| File | Purpose |
|------|---------|
| `00_README.md` | This file. Overview and navigation. |
| `01_PROJECT_BRIEF_TEMPLATE.md` | High-level project description, goals, constraints. |
| `02_B2C_SPEC_TEMPLATE.md` | Block-to-Code specification: per-block task definitions. |
| `03_CONTRACTS_TEMPLATE.md` | API contracts, test expectations, acceptance criteria. |
| `04_SCOPE_RULES_TEMPLATE.md` | File-level access control: target/read/do-not-touch lists. |
| `05_RUNBOOK_TEMPLATE.md` | Step-by-step execution instructions for the human operator. |
| `06_DECISION_LOG_TEMPLATE.md` | Record of architectural and design decisions. |
| `07_ISSUES_LOG_TEMPLATE.md` | Tracker for bugs, blockers, and open questions. |
| `08_WORKFLOW_SOP.md` | Standard Operating Procedure: the execution loop definition. |
| `09_QA_GATES.md` | Quality gates (Gate 0, 1, 2) definitions and pass criteria. |
| `10_PROMPTS/P1_DEFINER_B2C.md` | System prompt for the Definer agent. |
| `10_PROMPTS/P2_STRATEGY_REVIEWER.md` | System prompt for the Strategy/Reviewer agent. |
| `10_PROMPTS/P3_EXECUTOR_PATCH_ONLY.md` | System prompt for the Executor agent (patch-only output). |
| `11_USER_PROMPTS/` | Copy/paste user-message templates to start each role. |
| `tools/make_definer_bundle.py` | Optional: generate 1-file bundle for cloud chats. |

## Quick Start

1. Copy this folder into your project workspace.
2. Write a minimal seed in `01_PROJECT_BRIEF_TEMPLATE.md` (goal + constraints + DoD).
3. Fill only paths/commands in `05_RUNBOOK_TEMPLATE.md` (project_root, venv python, tests).
4. Run Definer in **conversation mode** to generate the first draft of:
   - `02_B2C_SPEC_TEMPLATE.md`
   - `03_CONTRACTS_TEMPLATE.md`
   - `04_SCOPE_RULES_TEMPLATE.md`
5. Follow `08_WORKFLOW_SOP.md` to execute the block loop.
6. Use `09_QA_GATES.md` to validate at each gate.

Fast start (one message):
- System prompt: `10_PROMPTS/P1_DEFINER_B2C.md`
- User message: “Read `01_PROJECT_BRIEF_TEMPLATE.md` + `05_RUNBOOK_TEMPLATE.md`, ask up to 5 questions, then (after answers) output complete filled text for **all 5 docs** (`01/02/03/04/05`).”

Gate 0 (always verify, never rely on agent claims):

```bash
cd <project_root>
python ai_workflow/tools/validate_gate0_docs.py
```

### Recommended mode: CLI/IDE (filesystem access)

If your AI can read local files, prefer this mode:
- Give the AI the project root (absolute path)
- Tell it to open and read the templates directly
- Avoid copy/paste of long files

Start here:
- `11_USER_PROMPTS/U0_START_HERE.md`

---

## Conversation-first workflow (recommended)

You do NOT need to hand-edit all templates yourself.

Practical flow:

1) You write a minimal seed (5–10 minutes):
- `01_PROJECT_BRIEF_TEMPLATE.md` (goal + constraints + success criteria)
- `05_RUNBOOK_TEMPLATE.md` (absolute paths + test/lint commands)

2) Definer asks a small set of questions (to remove ambiguity), then writes the documents.

3) You iterate by conversation:
- Definer updates the templates based on your answers
- Executor implements 1 block at a time
- Tools decide PASS/FAIL
- Strategy/Reviewer writes fix instructions on FAIL

See:
- `README.md` (operator guide)
- `11_USER_PROMPTS/` (copy/paste user-message templates)

Executor (IDE/CLI filesystem mode) minimal usage:
- Give only PROJECT_ROOT + BLOCK_NAME + ATTEMPT, and instruct “read required files from disk and output patch only”.

## Principles

- **Deterministic output**: Every agent prompt is designed to produce structured, parseable output.
- **Scope enforcement**: File-level access control prevents unintended side effects.
- **Loop breaker**: Same-cause failure 3 times triggers halt and spec redefinition.
- **Human-in-the-loop**: Tools/tests are executed by the human (or CI), not by the AI.
- **Domain safety**: High-risk domains (medical, legal, financial) require explicit disclaimers and evidence citations.
