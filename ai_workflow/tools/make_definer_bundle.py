#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _section(title: str, body: str) -> str:
    return f"\n\n===== {title} =====\n\n{body}\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a single markdown bundle for Definer AI (for AIs without filesystem access)."
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root (default: current directory).",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output markdown path (e.g., ai_workflow/_bundles/definer_bundle.md).",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    workflow_root = project_root / "ai_workflow"

    paths = {
        "SYSTEM_PROMPT (P1_DEFINER_B2C.md)": workflow_root / "10_PROMPTS" / "P1_DEFINER_B2C.md",
        "01_PROJECT_BRIEF_TEMPLATE.md": workflow_root / "01_PROJECT_BRIEF_TEMPLATE.md",
        "02_B2C_SPEC_TEMPLATE.md": workflow_root / "02_B2C_SPEC_TEMPLATE.md",
        "03_CONTRACTS_TEMPLATE.md": workflow_root / "03_CONTRACTS_TEMPLATE.md",
        "04_SCOPE_RULES_TEMPLATE.md": workflow_root / "04_SCOPE_RULES_TEMPLATE.md",
        "05_RUNBOOK_TEMPLATE.md": workflow_root / "05_RUNBOOK_TEMPLATE.md",
    }

    missing = [k for k, p in paths.items() if not p.exists()]
    if missing:
        raise SystemExit(f"Missing required files: {missing}")

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = (project_root / out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    header = (
        "# Definer Bundle\n\n"
        "This file bundles the system prompt + workflow templates.\n"
        "Use it only when your Definer AI cannot read local files.\n\n"
        f"PROJECT_ROOT: {project_root}\n"
        f"WORKFLOW_ROOT: {workflow_root}\n"
    )

    parts = [header]
    for title, path in paths.items():
        parts.append(_section(f"{title}\nPATH: {path}", _read_text(path)))

    out_path.write_text("".join(parts), encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

