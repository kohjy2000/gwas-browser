#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    path: Path
    message: str


_BRACE_TOKEN_RE = re.compile(r"\{[^\n\}]{1,120}\}")

# We intentionally avoid flagging JSON/dict examples like:
# {"success": true, "results": [...]}
# Instead we flag template placeholders (e.g., {PROJECT_ROOT}, {BLOCK_NAME_1}, {e.g., ...}, {true / false}).
_PLACEHOLDER_HINTS = (
    "PLACEHOLDER",
    "PROJECT_NAME",
    "PROJECT_ROOT",
    "VENV_PATH",
    "REQUIREMENTS_PATH",
    "TEST_PATH",
    "ALL_TESTS_PATH",
    "SRC_PATH",
    "SMOKE_TEST_COMMAND",
    "EXPECTED_FILE_OR_DIR",
    "BACKUP_DIR",
    "RUNS_DIR",
    "RUN_ID",
    "CYCLE_DIR",
    "BLOCK_NAME",
    "REL_PATH",
    "DIR_PATH",
    "GOAL_",
    "NON_GOAL_",
    "CONSTRAINT_",
    "ADDITIONAL_CRITERION",
    "CONTRACT_NAME",
    "TYPE",
    "KEY_",
    "INVALID_CONDITION",
    "HIGH_RISK_TOPIC",
    "COL_",
)


def _looks_like_json_or_dict(inner: str) -> bool:
    # heuristic: JSON/dict examples typically contain quotes, colons, or commas
    # e.g. {"a": 1} or {'a': 1}
    if ('"' in inner or "'" in inner) and ":" in inner:
        return True
    return False


def _is_placeholder_token(inner: str) -> bool:
    s = inner.strip()
    if not s:
        return False
    if _looks_like_json_or_dict(s):
        return False
    if "e.g." in s or "..." in s:
        return True
    if "true / false" in s or "Yes / No" in s:
        return True
    return any(hint in s for hint in _PLACEHOLDER_HINTS)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _find_placeholders(path: Path, text: str) -> list[Finding]:
    matches = []
    for m in _BRACE_TOKEN_RE.finditer(text):
        inner = m.group(0)[1:-1]
        if _is_placeholder_token(inner):
            matches.append(m)

    if not matches:
        return []
    # show only a few example placeholders to avoid noisy output
    examples: list[str] = []
    for m in matches[:8]:
        examples.append(m.group(0))
    more = "" if len(matches) <= 8 else f" (+{len(matches) - 8} more)"
    return [
        Finding(
            path=path,
            message=f"contains unresolved placeholders: {', '.join(examples)}{more}",
        )
    ]


def _validate_b2c(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    block_lines = [ln.strip() for ln in text.splitlines() if ln.startswith("## Block:")]
    if not block_lines:
        findings.append(Finding(path, "no blocks found (expected at least 1 '## Block: ...')"))
        return findings

    placeholder_blocks = [ln for ln in block_lines if "{" in ln and "}" in ln]
    if len(placeholder_blocks) == len(block_lines):
        findings.append(Finding(path, "all block names look like placeholders (spec is not filled)"))

    # basic contamination checks (common copy/paste mistakes)
    if re.search(r"^# Runbook\b", text, flags=re.M):
        findings.append(Finding(path, "appears to contain Runbook content (# Runbook found)"))
    if re.search(r"^## Phase 0: Document Preparation\b", text, flags=re.M):
        findings.append(Finding(path, "appears to contain Runbook sections (Phase 0 found)"))

    return findings


def _validate_scope(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    if "### Block:" not in text:
        findings.append(Finding(path, "no per-block scope sections found (expected '### Block: ...')"))
    return findings


def _validate_runbook(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    # ensure the runbook has *some* concrete commands
    if "pytest" not in text:
        findings.append(Finding(path, "no pytest command found (runbook likely incomplete)"))
    if "ruff" not in text:
        findings.append(Finding(path, "no ruff command found (runbook likely incomplete)"))
    return findings


def validate(workflow_root: Path) -> tuple[list[Finding], list[Finding]]:
    docs = {
        "brief": workflow_root / "01_PROJECT_BRIEF_TEMPLATE.md",
        "b2c": workflow_root / "02_B2C_SPEC_TEMPLATE.md",
        "contracts": workflow_root / "03_CONTRACTS_TEMPLATE.md",
        "scope": workflow_root / "04_SCOPE_RULES_TEMPLATE.md",
        "runbook": workflow_root / "05_RUNBOOK_TEMPLATE.md",
    }

    missing: list[Finding] = []
    for name, path in docs.items():
        if not path.exists():
            missing.append(Finding(path, f"missing required workflow doc: {name}"))

    if missing:
        return missing, []

    findings: list[Finding] = []
    for path in docs.values():
        text = _read(path)
        findings.extend(_find_placeholders(path, text))

        if path.name == "02_B2C_SPEC_TEMPLATE.md":
            findings.extend(_validate_b2c(path, text))
        elif path.name == "04_SCOPE_RULES_TEMPLATE.md":
            findings.extend(_validate_scope(path, text))
        elif path.name == "05_RUNBOOK_TEMPLATE.md":
            findings.extend(_validate_runbook(path, text))

    return [], findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate 0 doc validation for ai_workflow/")
    parser.add_argument(
        "--workflow-root",
        default="ai_workflow",
        help="Path to ai_workflow directory (default: ./ai_workflow)",
    )
    args = parser.parse_args()

    workflow_root = Path(args.workflow_root).resolve()
    missing, findings = validate(workflow_root)

    if missing:
        print("GATE0_DOCS: FAIL (missing files)")
        for f in missing:
            print(f"- {f.path}: {f.message}")
        return 2

    if findings:
        print("GATE0_DOCS: FAIL")
        for f in findings:
            print(f"- {f.path}: {f.message}")
        return 1

    print("GATE0_DOCS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
