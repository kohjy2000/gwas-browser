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
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python ai_workflow/tools/run_block_gate1.py --block C1.B2 --attempt 1 --skip-apply --copy-handoff --handoff-packet --executor-mode tool
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

### Gate 2 (recommended: single command)

Gate2 목적: “각 블록이 자기 테스트만 통과하는 수준(Gate1)”을 넘어, **프로젝트 전체가 실행/통합 관점에서도 깨끗한 상태**인지 최종 판정.

역할 규칙(반드시 준수):
- Definer/Strategy-Reviewer는 **실행 금지**(명령 실행/판정 금지). 진단/문서만.
- Executor만 Gate1/Gate2를 실행하고 PASS/FAIL을 도구 결과로 확정한다.

아래 한 줄로 Gate2를 실행한다 (로그/summary 자동 저장):

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python ai_workflow/tools/run_gate2.py
```

PASS 조건(도구 기준):
- `pytest -q contract_tests` 전체 PASS
- `ruff check gwas_dashboard_package/src gwas_variant_analyzer/gwas_variant_analyzer` 전체 PASS
- import smoke PASS (api 모듈/핵심 모듈 import)

아티팩트:
- `ai_workflow/_runs/GATE2_*/summary.json`
- `ai_workflow/_runs/GATE2_*/logs/*.log`

Optional smoke test:

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python gwas_dashboard_package/src/main.py
```

Recommended automated smoke test (local server + HTTP checks, then exit):

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python ai_workflow/tools/run_smoke_app.py
```

---

## Phase 2 (Product UX): Cycle 5 Blocks (when Gate2 PASS but “the app still feels broken”)

Gate2가 PASS여도, 실제 UI가 기대대로 동작하지 않으면(검색 품질/레퍼런스/ClinVar·PGx 노출/챗봇 facts) **Cycle 5로 들어간다**.

역할 규칙(반드시 준수):
- Definer/Strategy-Reviewer는 “정의/진단만” (실행/판정 금지)
- Executor만 파일 수정 + Gate1 실행

Cycle 5 블록 순서(권장):
1) C5.B1 Visible Trait Search Uses /api/search-traits
2) C5.B2 ClinVar and PGx Panels Visible and Wired
3) C5.B3 Chat Must Use Session Facts (No Manual Facts Paste)
4) C5.B4 References Must Be URLs (PubMed or Study URL)

각 블록은 Gate1 1줄 커맨드로 실행한다(Executor tool-mode가 직접 실행하는 것이 최적):

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python ai_workflow/tools/run_block_gate1.py --block C5.B1 --attempt 1 --skip-apply --copy-handoff --handoff-packet --executor-mode tool
```

모든 Cycle 5 블록이 PASS하면, 다시 Gate2 + smoke를 실행한다:

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python ai_workflow/tools/run_gate2.py
/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python ai_workflow/tools/run_smoke_app.py
```

---

## Rollback Procedure

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
git checkout -- .
```

---

## Phase 3 (Online + Local LLM): Cycle 6

Cycle 6는 “원격 trait 보강”과 “로컬 LLM(ollama) 연결”을 추가한다.

### Remote trait search (GWAS Catalog)

- 기본 원칙: 테스트는 네트워크 금지. 런타임에서만 원격 호출 허용(옵션).
- 권장: 원격 결과는 로컬 캐시(data/trait_list.json)에 합쳐서 다음부터는 로컬만으로도 검색 가능하게 한다.

### Ollama (local LLM) for chat

Executor가 아래를 확인/설정한다 (Definer/Reviewer는 실행 금지):

```bash
ollama --version || true
ollama list || true
```

권장 모델(예시, 하나만 골라 pull):

```bash
ollama pull llama3.1:8b-instruct
```

또는:

```bash
ollama pull qwen2.5:7b-instruct
```

환경변수(예시):

```bash
export OLLAMA_HOST=http://127.0.0.1:11434
export OLLAMA_MODEL_CHAT=llama3.1:8b-instruct
```

주의: contract_tests에서는 Ollama가 없어도 PASS해야 한다(테스트는 monkeypatch/mock로만 검증).
