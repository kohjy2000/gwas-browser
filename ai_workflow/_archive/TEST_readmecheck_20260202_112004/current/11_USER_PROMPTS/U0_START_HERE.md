# Start Here — Which AI do I use, and what do I paste?

This folder contains **user-message templates**. You normally use them together with the **system prompts** in `ai_workflow/10_PROMPTS/`.

## Recommended AI roles

1) **Definer AI** (best performance)
- Use when: starting a project or redefining a block after repeated failure.
- System prompt: `/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/10_PROMPTS/P1_DEFINER_B2C.md`
- User prompts (2-step conversation):
  - Questions first: `/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/11_USER_PROMPTS/U1A_DEFINER_QUESTIONS.md`
  - Then write docs: `/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/11_USER_PROMPTS/U1B_DEFINER_WRITE_DOCS.md`

2) **Strategy/Reviewer AI** (diagnosis only)
- Use when: tools/tests fail after applying an Executor output.
- System prompt: `/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/10_PROMPTS/P2_STRATEGY_REVIEWER.md`
- User prompt: `/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/11_USER_PROMPTS/U2_START_STRATEGY_REVIEWER.md`

3) **Executor AI** (implementation only)
- Use when: implementing exactly one block from the B2C spec.
- Recommended (tool-enabled IDE/CLI Executor, auto Gate1):
  - System prompt: `/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/10_PROMPTS/P4_EXECUTOR_TOOL_MODE_AUTORUN.md`
  - User prompt: `/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/11_USER_PROMPTS/U3B_EXECUTOR_TOOL_MODE_AUTORUN.md`
- Fallback (chat Executor, patch-only):
  - System prompt: `/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/10_PROMPTS/P3_EXECUTOR_PATCH_ONLY.md`
  - User prompt: `/Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser/ai_workflow/11_USER_PROMPTS/U3_START_EXECUTOR.md`

## Phase 2 / Cycle 5 (UX)

If Gate2 passes but the UI/UX is still unacceptable, continue with Cycle 5 blocks:
- C5.B1 → C5.B2 → C5.B3 → C5.B4

## CLI/IDE mode (recommended)

If you run AIs inside a CLI/IDE agent that can read local files, do **not** copy/paste templates:
- Provide the project root path.
- Instruct the AI to open/read the listed files by absolute path.

Recommended Definer flow:
1) Run questions-first prompt (short).
2) Answer questions.
3) Run write-docs prompt (outputs the filled templates).

## Cloud-chat mode (no filesystem access)

Generate a single bundle and paste it:

```bash
cd /Users/june-young/Research_Local/08_GWAS_browser/ver_260201_toy_gwas_browser
python ai_workflow/tools/make_definer_bundle.py --out ai_workflow/_bundles/definer_bundle.md
```
