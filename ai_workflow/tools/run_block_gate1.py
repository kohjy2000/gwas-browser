#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BlockSpec:
    block_name: str
    block_id: str
    target_files_abs: list[str]
    read_files_abs: list[str]
    tests_required_lines: list[str]


def _project_root_from_arg(path: str | None) -> Path:
    return Path(path).resolve() if path else Path.cwd().resolve()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _run(cmd: str, cwd: Path, log_path: Path) -> int:
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
    return proc.returncode


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
        "This workflow expects a git baseline for scope checking.\n"
        "Run once:\n"
        f"  cd {project_root}\n"
        "  git init\n"
        "  git add -A\n"
    )


def _sanitize_block_id(raw: str) -> str:
    # allow "C1.B2" but avoid filesystem traversal
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw).strip("_")
    return safe or "BLOCK"


def _parse_block_spec(project_root: Path, block_selector: str) -> BlockSpec:
    b2c_path = project_root / "ai_workflow" / "02_B2C_SPEC_TEMPLATE.md"
    if not b2c_path.exists():
        raise SystemExit(f"Missing: {b2c_path}")

    text = _read_text(b2c_path)
    blocks = list(re.finditer(r"^## Block: (.+?)\n(.*?)(?=^## Block: |\Z)", text, re.M | re.S))
    if not blocks:
        raise SystemExit("No blocks found in 02_B2C_SPEC_TEMPLATE.md")

    candidates: list[tuple[str, str]] = []
    for m in blocks:
        name = m.group(1).strip()
        body = m.group(2)
        block_id = name.split(" ", 1)[0].strip()
        candidates.append((name, body))

    matched: list[tuple[str, str]] = []
    for name, body in candidates:
        if block_selector == name:
            matched.append((name, body))
        elif name.startswith(block_selector + " "):
            matched.append((name, body))

    if not matched:
        raise SystemExit(f"Block not found: {block_selector}")
    if len(matched) > 1:
        names = "\n".join(f"- {n}" for n, _ in matched)
        raise SystemExit(f"Ambiguous block selector: {block_selector}\nMatches:\n{names}")

    block_name, body = matched[0]
    block_id = block_name.split(" ", 1)[0].strip()

    def _extract_list(section_title: str) -> list[str]:
        mm = re.search(rf"^### {re.escape(section_title)}\n\n(.*?)(?=^### |\n---\n|\Z)", body, re.M | re.S)
        if not mm:
            return []
        out: list[str] = []
        for line in mm.group(1).splitlines():
            line = line.strip()
            if line.startswith("- "):
                out.append(line[2:].strip())
        return out

    target_files = _extract_list("Target Files")
    read_files = _extract_list("Read Files")

    tm = re.search(r"^### Tests Required\n\n```bash\n(.*?)```", body, re.M | re.S)
    tests_required = []
    if tm:
        tests_required = [ln.rstrip() for ln in tm.group(1).splitlines() if ln.strip()]

    if not target_files:
        raise SystemExit(f"No target_files found for block: {block_name}")
    if not tests_required:
        raise SystemExit(f"No tests_required found for block: {block_name}")

    return BlockSpec(
        block_name=block_name,
        block_id=block_id,
        target_files_abs=target_files,
        read_files_abs=read_files,
        tests_required_lines=tests_required,
    )


def _abs_to_rel(project_root: Path, abs_path: str) -> str:
    p = Path(abs_path)
    if not p.is_absolute():
        return str(p)
    try:
        return str(p.resolve().relative_to(project_root))
    except Exception:
        raise SystemExit(f"Target/read path is not under project root: {abs_path}")


def _read_executor_output(executor_output_path: Path | None) -> str:
    if executor_output_path:
        return executor_output_path.read_text(encoding="utf-8")

    if sys.stdin.isatty():
        sys.stderr.write(
            "Paste Executor output now (NOOP / BEGIN_DIFF...END_DIFF / BEGIN EDITED FILE...END EDITED FILE).\n"
            "End with Ctrl-D.\n"
        )
    return sys.stdin.read()


def _capture_git_diff_or_noop(project_root: Path) -> str:
    chunks: list[str] = []
    for cmd in ("git diff", "git diff --cached"):
        proc = subprocess.run(
            cmd,
            cwd=str(project_root),
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            chunks.append(proc.stdout.rstrip("\n") + "\n")
    combined = "\n".join(chunks).strip("\n")
    if not combined:
        return "NOOP\n"
    return "BEGIN_DIFF\n" + combined + "\nEND_DIFF\n"

def _read_clipboard_text() -> str:
    # macOS: pbpaste
    proc = subprocess.run(
        "pbpaste",
        shell=True,
        executable="/bin/bash",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        if proc.returncode == 127:
            raise SystemExit(
                "Clipboard read failed: `pbpaste` not found (macOS only).\n"
                "Use stdin mode instead (omit --executor-output-clipboard) or pass --executor-output-file.\n"
            )
        raise SystemExit("Failed to read clipboard (pbpaste). Copy the Executor output first.")
    return proc.stdout


def _copy_to_clipboard(text: str) -> None:
    # macOS: pbcopy
    proc = subprocess.run(
        "pbcopy",
        shell=True,
        executable="/bin/bash",
        input=text,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        if proc.returncode == 127:
            raise SystemExit(
                "Clipboard copy failed: `pbcopy` not found (macOS only).\n"
                "Re-run without --copy-handoff and open the prompt file from summary.json.\n"
            )
        raise SystemExit("Failed to copy to clipboard (pbcopy).")


def _extract_between_markers(text: str, start: str, end: str) -> str | None:
    m = re.search(rf"{re.escape(start)}\n(.*?)\n{re.escape(end)}", text, re.S)
    if not m:
        return None
    return m.group(1).rstrip("\n") + "\n"


def _parse_edited_files(text: str) -> list[tuple[str, str]]:
    files: list[tuple[str, str]] = []
    pat = re.compile(r"^BEGIN EDITED FILE (.+?)\n(.*?)\nEND EDITED FILE$", re.M | re.S)
    for m in pat.finditer(text.strip()):
        path = m.group(1).strip()
        content = m.group(2) + "\n"
        files.append((path, content))
    return files


def _validate_rel_path(rel_path: str) -> None:
    p = Path(rel_path)
    if p.is_absolute():
        raise SystemExit(f"Executor output used absolute path (not allowed): {rel_path}")
    if ".." in p.parts:
        raise SystemExit(f"Executor output used parent traversal (not allowed): {rel_path}")


def _apply_executor_output(
    project_root: Path,
    spec: BlockSpec,
    attempt_dir: Path,
    executor_output: str,
) -> None:
    executor_output = executor_output.strip("\n")
    (attempt_dir / "executor_output.txt").write_text(executor_output + "\n", encoding="utf-8")

    allowed_rel_targets = {_abs_to_rel(project_root, p) for p in spec.target_files_abs}

    if executor_output.strip() == "NOOP":
        (attempt_dir / "apply.log").write_text("NOOP\n", encoding="utf-8")
        return

    diff_body = _extract_between_markers(executor_output, "BEGIN_DIFF", "END_DIFF")
    if diff_body is not None:
        # Validate that diff touches only allowed files.
        touched = []
        for line in diff_body.splitlines():
            if line.startswith("diff --git "):
                parts = line.split()
                if len(parts) >= 4:
                    a = parts[2].removeprefix("a/")
                    b = parts[3].removeprefix("b/")
                    touched.extend([a, b])
        for rel in {t for t in touched if t}:
            _validate_rel_path(rel)
            if rel not in allowed_rel_targets:
                raise SystemExit(f"Diff touches out-of-scope file: {rel}")

        patch_path = attempt_dir / "output.patch"
        patch_path.write_text(diff_body, encoding="utf-8")

        # Backup target files
        backup_dir = attempt_dir / "backup"
        for rel in allowed_rel_targets:
            src = project_root / rel
            if src.exists():
                dst = backup_dir / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        # Apply patch (dry-run then apply)
        apply_log = attempt_dir / "apply.log"
        dry_cmd = f"patch -p1 --dry-run < {patch_path}"
        rc = _run(dry_cmd, project_root, apply_log)
        if rc != 0:
            raise SystemExit(f"patch dry-run failed (see {apply_log})")
        rc = _run(f"patch -p1 < {patch_path}", project_root, apply_log)
        if rc != 0:
            raise SystemExit(f"patch apply failed (see {apply_log})")
        return

    edited_files = _parse_edited_files(executor_output)
    if edited_files:
        # Backup target files and overwrite edited files
        backup_dir = attempt_dir / "backup"
        for rel in allowed_rel_targets:
            src = project_root / rel
            if src.exists():
                dst = backup_dir / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        for rel_path, content in edited_files:
            _validate_rel_path(rel_path)
            if rel_path not in allowed_rel_targets:
                raise SystemExit(f"Edited file out of scope: {rel_path}")
            out_path = project_root / rel_path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(content, encoding="utf-8")

        (attempt_dir / "apply.log").write_text("EDITED FILE APPLY OK\n", encoding="utf-8")
        return

    raise SystemExit("Executor output format not recognized (expected NOOP / BEGIN_DIFF..END_DIFF / BEGIN EDITED FILE..END EDITED FILE).")


def _run_gate1_tools(project_root: Path, spec: BlockSpec, attempt_dir: Path) -> dict:
    logs_dir = attempt_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    combined_log = logs_dir / "gate1.log"
    combined_log.write_text("", encoding="utf-8")

    results: list[dict] = []

    def _append(cmd: str, out: str) -> None:
        with combined_log.open("a", encoding="utf-8") as f:
            f.write("\n$ " + cmd + "\n")
            f.write(out)

    for i, line in enumerate(spec.tests_required_lines, 1):
        cmd = line
        # run each line as an individual shell command
        proc = subprocess.run(
            cmd,
            cwd=str(project_root),
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        _append(cmd, proc.stdout)
        results.append({"n": i, "cmd": cmd, "returncode": proc.returncode})

        # Keep common outputs for reviewer convenience
        if "pytest" in cmd:
            (logs_dir / "pytest.log").write_text(proc.stdout, encoding="utf-8")
        if "ruff" in cmd:
            (logs_dir / "ruff.log").write_text(proc.stdout, encoding="utf-8")
        if cmd.strip().startswith("git status --porcelain"):
            (attempt_dir / "changed_files.txt").write_text(proc.stdout, encoding="utf-8")

    # Always collect changed files (even if spec didn't include it)
    proc = subprocess.run(
        "git status --porcelain",
        cwd=str(project_root),
        shell=True,
        executable="/bin/bash",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    (attempt_dir / "changed_files.txt").write_text(proc.stdout, encoding="utf-8")

    all_ok = all(r["returncode"] == 0 for r in results)
    return {"all_ok": all_ok, "commands": results}


def _scope_check(project_root: Path, spec: BlockSpec, attempt_dir: Path) -> tuple[bool, list[str]]:
    changed = (attempt_dir / "changed_files.txt").read_text(encoding="utf-8").splitlines()
    changed_paths = []
    for line in changed:
        # porcelain: "XY path"
        parts = line.strip().split(maxsplit=1)
        if len(parts) == 2:
            changed_paths.append(parts[1])

    allowed_rel_targets = {_abs_to_rel(project_root, p) for p in spec.target_files_abs}
    bad = [p for p in changed_paths if p not in allowed_rel_targets]
    ok = len(bad) == 0
    (attempt_dir / "scope_check.json").write_text(
        json.dumps({"changed": changed_paths, "allowed": sorted(allowed_rel_targets), "bad": bad}, indent=2),
        encoding="utf-8",
    )
    return ok, bad


def _list_blocks(project_root: Path) -> list[str]:
    b2c_path = project_root / "ai_workflow" / "02_B2C_SPEC_TEMPLATE.md"
    text = _read_text(b2c_path)
    names = []
    for m in re.finditer(r"^## Block: (.+)$", text, re.M):
        names.append(m.group(1).strip())
    return names


def _next_block_name(project_root: Path, current_block_name: str) -> str | None:
    blocks = _list_blocks(project_root)
    if not blocks:
        return None
    # match by exact name first, else by id prefix (e.g., "C1.B2")
    current_id = current_block_name.split(" ", 1)[0].strip()

    idx = None
    for i, name in enumerate(blocks):
        if name == current_block_name:
            idx = i
            break
    if idx is None:
        for i, name in enumerate(blocks):
            if name.startswith(current_id + " "):
                idx = i
                break
    if idx is None:
        return None
    if idx + 1 >= len(blocks):
        return None
    return blocks[idx + 1]


def _write_handoff_prompts(project_root: Path, spec: BlockSpec, attempt_dir: Path, status: str) -> dict[str, str]:
    prompts_dir = attempt_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    project_root_abs = str(project_root)
    block_name = spec.block_name
    block_id = spec.block_id
    attempt = int(re.search(r"_attempt(\d+)$", attempt_dir.name).group(1)) if re.search(r"_attempt(\d+)$", attempt_dir.name) else 1

    prompts: dict[str, str] = {}

    if status == "PASS":
        nxt = _next_block_name(project_root, block_name)
        if nxt:
            user_msg = (
                f"PROJECT_ROOT_ABS={project_root_abs}\n"
                f"BLOCK_NAME={nxt}\n"
                f"ATTEMPT=1/3\n\n"
                "디스크에서 직접 읽어라(나는 파일 내용 붙여넣기 안 함):\n"
                "- ai_workflow/02_B2C_SPEC_TEMPLATE.md 에서 BLOCK_NAME 섹션\n"
                "- ai_workflow/03_CONTRACTS_TEMPLATE.md 관련 계약\n"
                "- ai_workflow/04_SCOPE_RULES_TEMPLATE.md 스코프\n"
                "- 해당 블록 read_files 전부\n\n"
                "target_files만 수정해서 해당 블록의 contract_tests를 PASS로 만들어라.\n"
                "출력은 패치만: NOOP 또는 BEGIN_DIFF/END_DIFF 또는 BEGIN EDITED FILE/END EDITED FILE\n"
                "(설명 금지, 경로는 프로젝트 상대경로)\n"
            )
            p = prompts_dir / "PROMPT_NEXT_EXECUTOR.txt"
            p.write_text(user_msg, encoding="utf-8")
            prompts["next_executor"] = str(p)
        return prompts

    # FAIL: reviewer prompt + retry executor prompt
    reviewer_msg = (
        f"PROJECT_ROOT_ABS={project_root_abs}\n"
        f"BLOCK_NAME={block_name}\n"
        f"ATTEMPT={attempt}/3\n\n"
        "디스크에서 직접 읽어라(나는 로그/파일 내용 붙여넣기 안 함):\n"
        f"- ai_workflow/02_B2C_SPEC_TEMPLATE.md 에서 {block_name} 섹션\n"
        f"- ai_workflow/04_SCOPE_RULES_TEMPLATE.md 에서 {block_name} 스코프\n"
        f"- ai_workflow/_runs/{block_id}_attempt{attempt}/executor_output.txt\n"
        f"- ai_workflow/_runs/{block_id}_attempt{attempt}/logs/gate1.log\n"
        f"- ai_workflow/_runs/{block_id}_attempt{attempt}/changed_files.txt\n"
        f"- ai_workflow/_runs/{block_id}_attempt{attempt}/scope_check.json\n\n"
        "해야 할 일:\n"
        "- 실패의 1차 원인(root cause)을 로그 근거로 1개로 요약\n"
        "- target_files 범위 안에서만 고치도록 Executor용 fix instructions 작성\n"
        "- 마지막에 'Executor에게 그대로 붙여넣을 재시도 프롬프트'를 한 덩어리로 출력\n"
    )
    p = prompts_dir / "PROMPT_REVIEWER.txt"
    p.write_text(reviewer_msg, encoding="utf-8")
    prompts["reviewer"] = str(p)

    next_attempt = min(attempt + 1, 3)
    retry_msg = (
        f"PROJECT_ROOT_ABS={project_root_abs}\n"
        f"BLOCK_NAME={block_name}\n"
        f"ATTEMPT={next_attempt}/3\n\n"
        "디스크에서 직접 읽어라(나는 파일 내용 붙여넣기 안 함):\n"
        "- ai_workflow/02_B2C_SPEC_TEMPLATE.md 에서 BLOCK_NAME 섹션\n"
        "- ai_workflow/03_CONTRACTS_TEMPLATE.md 관련 계약\n"
        "- ai_workflow/04_SCOPE_RULES_TEMPLATE.md 스코프\n"
        "- 해당 블록 read_files 전부\n"
        f"- ai_workflow/_runs/{block_id}_attempt{attempt}/reviewer.md (있으면 반드시 읽고 그 지시를 우선 적용)\n\n"
        "출력은 패치만: NOOP 또는 BEGIN_DIFF/END_DIFF 또는 BEGIN EDITED FILE/END EDITED FILE\n"
        "(설명 금지, 경로는 프로젝트 상대경로)\n"
    )
    p = prompts_dir / "PROMPT_RETRY_EXECUTOR.txt"
    p.write_text(retry_msg, encoding="utf-8")
    prompts["retry_executor"] = str(p)
    return prompts


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply Executor output and run Gate 1 tools for one block.")
    parser.add_argument("--project-root", default=None, help="Project root (default: current directory).")
    parser.add_argument("--block", required=True, help="Block selector (e.g., 'C1.B2' or full block name).")
    parser.add_argument("--attempt", type=int, required=True, help="Attempt number (1..3).")
    parser.add_argument(
        "--skip-apply",
        action="store_true",
        help="Skip applying Executor output (assumes files already modified). Still runs tools + scope check + prompt generation.",
    )
    parser.add_argument(
        "--handoff-only",
        action="store_true",
        help="Print only the chosen handoff prompt text (no JSON). Useful for tool-enabled Executors.",
    )
    parser.add_argument(
        "--executor-output-file",
        default=None,
        help="Path to a file containing Executor output. If omitted, reads from stdin (paste then Ctrl-D).",
    )
    parser.add_argument(
        "--executor-output-clipboard",
        action="store_true",
        help="Read Executor output from clipboard (macOS pbpaste).",
    )
    parser.add_argument(
        "--copy-handoff",
        action="store_true",
        help="Copy the next handoff prompt to clipboard (PASS -> next executor, FAIL -> reviewer).",
    )
    args = parser.parse_args()

    project_root = _project_root_from_arg(args.project_root)
    _ensure_git_or_exit(project_root)

    spec = _parse_block_spec(project_root, args.block)
    attempt_dir = project_root / "ai_workflow" / "_runs" / f"{_sanitize_block_id(spec.block_id)}_attempt{args.attempt}"
    attempt_dir.mkdir(parents=True, exist_ok=True)

    if args.skip_apply:
        # Tool-enabled executor may have already modified files. Capture current git diff for continuity.
        (attempt_dir / "executor_output.txt").write_text(_capture_git_diff_or_noop(project_root), encoding="utf-8")
        (attempt_dir / "apply.log").write_text("SKIP_APPLY\n", encoding="utf-8")
    else:
        executor_output_path = Path(args.executor_output_file).resolve() if args.executor_output_file else None
        if args.executor_output_clipboard:
            executor_output = _read_clipboard_text()
        else:
            executor_output = _read_executor_output(executor_output_path)
        if not executor_output.strip():
            raise SystemExit("Empty Executor output.")

        _apply_executor_output(project_root, spec, attempt_dir, executor_output)

    tools = _run_gate1_tools(project_root, spec, attempt_dir)
    scope_ok, scope_bad = _scope_check(project_root, spec, attempt_dir)

    status = "PASS" if tools["all_ok"] and scope_ok else "FAIL"
    prompts = _write_handoff_prompts(project_root, spec, attempt_dir, status)

    copied = None
    if args.copy_handoff and prompts:
        # prefer next executor on PASS, else reviewer on FAIL
        chosen_path = prompts.get("next_executor") if status == "PASS" else prompts.get("reviewer")
        if chosen_path:
            chosen_text = Path(chosen_path).read_text(encoding="utf-8")
            _copy_to_clipboard(chosen_text)
            copied = chosen_path

    chosen_path = None
    if prompts:
        chosen_path = prompts.get("next_executor") if status == "PASS" else prompts.get("reviewer")

    summary = {
        "block_name": spec.block_name,
        "block_id": spec.block_id,
        "attempt": args.attempt,
        "tools_all_ok": tools["all_ok"],
        "scope_ok": scope_ok,
        "scope_bad": scope_bad,
        "status": status,
        "attempt_dir": str(attempt_dir),
        "prompts": prompts,
        "clipboard_copied": copied,
        "handoff_prompt": chosen_path,
    }
    (attempt_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if args.handoff_only:
        if chosen_path:
            sys.stdout.write(Path(chosen_path).read_text(encoding="utf-8"))
        else:
            sys.stdout.write("")
    else:
        print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
