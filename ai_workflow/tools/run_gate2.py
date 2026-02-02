#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class CmdResult:
    name: str
    cmd: str
    returncode: int
    log_path: str


def _project_root_from_arg(path: str | None) -> Path:
    return Path(path).resolve() if path else Path.cwd().resolve()

def _load_env_kv_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _load_project_env(project_root: Path) -> None:
    _load_env_kv_file(project_root / "ai_workflow" / ".env.local")
    _load_env_kv_file(project_root / ".env")


def _run(cmd: str, cwd: Path, log_path: Path) -> CmdResult:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        shell=True,
        executable="/bin/bash",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    log_path.write_text(proc.stdout, encoding="utf-8")
    return CmdResult(
        name=log_path.stem,
        cmd=cmd,
        returncode=proc.returncode,
        log_path=str(log_path),
    )


def _ensure_git_or_exit(project_root: Path) -> None:
    proc = subprocess.run(
        "git rev-parse --is-inside-work-tree",
        cwd=str(project_root),
        shell=True,
        executable="/bin/bash",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode == 0:
        return
    raise SystemExit(
        "Gate2 expects a git baseline for sanity/scope checks.\n"
        "Run once:\n"
        f"  cd {project_root}\n"
        "  git init\n"
        "  git add -A\n"
    )


def _now_run_id() -> str:
    return datetime.now(timezone.utc).strftime("GATE2_%Y%m%d_%H%M%S")


def _summary_text(project_root: Path, run_dir: Path, results: list[CmdResult]) -> str:
    ok = all(r.returncode == 0 for r in results)

    lines: list[str] = []
    lines.append("# Gate2 결과(통합 Integrity)")
    lines.append(f"- 프로젝트 루트: {project_root}")
    lines.append(f"- 런 아티팩트: {run_dir}")
    lines.append(f"- 결과: {'PASS' if ok else 'FAIL'}")
    lines.append("")
    lines.append("## 체크 항목")
    for r in results:
        status = "PASS" if r.returncode == 0 else f"FAIL (exit={r.returncode})"
        lines.append(f"- {r.name}: {status}")
        lines.append(f"  - cmd: {r.cmd}")
        lines.append(f"  - log: {r.log_path}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate2: full integrity (tests + ruff + import smoke).")
    parser.add_argument("--project-root", default=None, help="Project root (default: current directory).")
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory under ai_workflow/_runs (default: auto timestamp folder).",
    )
    args = parser.parse_args()

    project_root = _project_root_from_arg(args.project_root)
    _load_project_env(project_root)
    _ensure_git_or_exit(project_root)

    runs_root = project_root / "ai_workflow" / "_runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    run_id = args.out_dir or _now_run_id()
    run_dir = runs_root / run_id
    logs_dir = run_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    results: list[CmdResult] = []

    # 1) Full contract tests
    results.append(
        _run(
            "/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python -m pytest -q contract_tests",
            cwd=project_root,
            log_path=logs_dir / "pytest_contract_tests.log",
        )
    )

    # 2) Full ruff
    results.append(
        _run(
            "/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/ruff check gwas_dashboard_package/src gwas_variant_analyzer/gwas_variant_analyzer",
            cwd=project_root,
            log_path=logs_dir / "ruff_full.log",
        )
    )

    # 3) Import smoke (no server run)
    results.append(
        _run(
            "/Users/june-young/Research_Local/08_GWAS_browser/venv/bin/python - <<'PY'\n"
            "import importlib\n"
            "mods=[\n"
            " 'gwas_dashboard_package',\n"
            " 'gwas_dashboard_package.src.main',\n"
            " 'gwas_dashboard_package.src.routes.api',\n"
            " 'gwas_variant_analyzer.utils',\n"
            " 'gwas_variant_analyzer.gwas_catalog_handler',\n"
            " 'gwas_variant_analyzer.chat_facts',\n"
            "]\n"
            "for m in mods:\n"
            "  importlib.import_module(m)\n"
            "print('IMPORT_SMOKE: PASS')\n"
            "PY",
            cwd=project_root,
            log_path=logs_dir / "import_smoke.log",
        )
    )

    ok = all(r.returncode == 0 for r in results)

    summary = {
        "project_root": str(project_root),
        "run_dir": str(run_dir),
        "status": "PASS" if ok else "FAIL",
        "checks": [r.__dict__ for r in results],
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(_summary_text(project_root, run_dir, results))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
