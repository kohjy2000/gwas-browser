#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import shutil
import subprocess
import json
from pathlib import Path


DOCSET_FILES = (
    "01_PROJECT_BRIEF_TEMPLATE.md",
    "02_B2C_SPEC_TEMPLATE.md",
    "03_CONTRACTS_TEMPLATE.md",
    "04_SCOPE_RULES_TEMPLATE.md",
    "05_RUNBOOK_TEMPLATE.md",
    "README.md",
)

DOCSET_DIRS = (
    "10_PROMPTS",
    "11_USER_PROMPTS",
)


def _project_root_from_arg(path: str | None) -> Path:
    return Path(path).resolve() if path else Path.cwd().resolve()


def _timestamp() -> str:
    # local time; stable and human-friendly
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _is_git_repo(project_root: Path) -> bool:
    proc = subprocess.run(
        "git rev-parse --is-inside-work-tree",
        cwd=str(project_root),
        shell=True,
        executable="/bin/bash",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def _copy_current(workflow_root: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in DOCSET_FILES:
        src = workflow_root / name
        if src.exists():
            shutil.copy2(src, out_dir / name)
    for name in DOCSET_DIRS:
        src_dir = workflow_root / name
        if src_dir.exists() and src_dir.is_dir():
            shutil.copytree(src_dir, out_dir / name, dirs_exist_ok=True)

def _copy_flat_with_suffix(workflow_root: Path, out_dir: Path, suffix: str) -> None:
    """
    Create a flat folder with suffix-renamed copies for quick grepping/comparison.
    Example output name: 01_PROJECT_BRIEF_TEMPLATE__GWAS_BROWSER_cycle6_20260202_112000.md
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in DOCSET_FILES:
        src = workflow_root / name
        if not src.exists():
            continue
        stem = src.stem
        dst_name = f"{stem}__{suffix}{src.suffix}"
        shutil.copy2(src, out_dir / dst_name)


def _write_head_snapshot(project_root: Path, workflow_root: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in DOCSET_FILES:
        rel = (workflow_root / name).relative_to(project_root)
        proc = subprocess.run(
            f"git show HEAD:{rel}",
            cwd=str(project_root),
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if proc.returncode == 0 and proc.stdout:
            (out_dir / name).write_text(proc.stdout, encoding="utf-8")
    for name in DOCSET_DIRS:
        rel_dir = (workflow_root / name).relative_to(project_root)
        proc = subprocess.run(
            f"git ls-tree -r --name-only HEAD {rel_dir}",
            cwd=str(project_root),
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if proc.returncode != 0:
            continue
        for rel_path in [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]:
            file_proc = subprocess.run(
                f"git show HEAD:{rel_path}",
                cwd=str(project_root),
                shell=True,
                executable="/bin/bash",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if file_proc.returncode == 0:
                dst = out_dir / Path(rel_path).name
                # Preserve directory structure under 10_PROMPTS/ and 11_USER_PROMPTS/
                try:
                    dst = out_dir / Path(rel_path).relative_to(rel_dir)
                except Exception:
                    dst = out_dir / Path(rel_path).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(file_proc.stdout, encoding="utf-8")

def _git_head_sha(project_root: Path) -> str | None:
    proc = subprocess.run(
        "git rev-parse HEAD",
        cwd=str(project_root),
        shell=True,
        executable="/bin/bash",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _git_dirty(project_root: Path) -> bool:
    proc = subprocess.run(
        "git status --porcelain",
        cwd=str(project_root),
        shell=True,
        executable="/bin/bash",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        return False
    return bool(proc.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive ai_workflow docset (current + optional git HEAD snapshot).")
    parser.add_argument("--project-root", default=None, help="Project root (default: cwd).")
    parser.add_argument("--workflow-root", default="ai_workflow", help="ai_workflow directory (default: ./ai_workflow).")
    parser.add_argument("--prefix", required=True, help="Archive folder prefix (e.g., GWAS_BROWSER).")
    parser.add_argument("--tag", default="", help="Optional tag (e.g., cycle6, uxfix, refactor).")
    parser.add_argument("--no-head", action="store_true", help="Do not save git HEAD snapshot.")
    args = parser.parse_args()

    project_root = _project_root_from_arg(args.project_root)
    workflow_root = (project_root / args.workflow_root).resolve()
    if not workflow_root.exists():
        raise SystemExit(f"Missing workflow root: {workflow_root}")

    tag_part = f"_{args.tag}" if args.tag else ""
    ts = _timestamp()
    archive_id = f"{args.prefix}{tag_part}_{ts}"
    base = workflow_root / "_archive" / archive_id

    _copy_current(workflow_root, base / "current")
    _copy_flat_with_suffix(workflow_root, base / "flat", f"{args.prefix}{tag_part}_{ts}".strip("_"))

    if not args.no_head and _is_git_repo(project_root):
        _write_head_snapshot(project_root, workflow_root, base / "head")

    meta = {
        "archive_id": archive_id,
        "created_at_local": ts,
        "project_root": str(project_root),
        "workflow_root": str(workflow_root),
        "prefix": args.prefix,
        "tag": args.tag,
        "git": {
            "is_repo": _is_git_repo(project_root),
            "head": _git_head_sha(project_root) if _is_git_repo(project_root) else None,
            "dirty": _git_dirty(project_root) if _is_git_repo(project_root) else None,
        },
    }
    (base / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"ARCHIVE_OK: {base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
