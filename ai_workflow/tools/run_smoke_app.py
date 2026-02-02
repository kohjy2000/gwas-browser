#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


def _project_root_from_arg(path: str | None) -> Path:
    return Path(path).resolve() if path else Path.cwd().resolve()


def _make_server(app, host: str, port: int):
    # werkzeug is a Flask dependency
    from werkzeug.serving import make_server  # type: ignore

    return make_server(host, port, app, threaded=True)


def _wait_ready(base_url: str, timeout_s: float) -> None:
    import requests  # type: ignore

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            r = requests.get(base_url + "/", timeout=1)
            if r.status_code == 200:
                return
        except Exception:
            time.sleep(0.1)
    raise TimeoutError(f"Server did not become ready within {timeout_s}s: {base_url}")


def _write_fixture_vcf(path: Path) -> None:
    # Matches toy ClinVar TSV: chrom=1 pos=1000 ref=A alt=G
    path.write_text(
        "##fileformat=VCFv4.2\n"
        "##contig=<ID=1>\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tsample1\n"
        "1\t1000\trs121913529\tA\tG\t.\tPASS\t.\tGT\t0/1\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the running GWAS browser (toy project).")
    parser.add_argument("--project-root", default=None, help="Project root (default: current directory).")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host for local server.")
    parser.add_argument("--port", type=int, default=0, help="Bind port (0 = random free port).")
    parser.add_argument("--timeout", type=float, default=10.0, help="Startup timeout in seconds.")
    args = parser.parse_args()

    project_root = _project_root_from_arg(args.project_root)

    # Ensure the project root is importable even when running this script by path
    # (otherwise sys.path[0] becomes ai_workflow/tools and imports like
    # `gwas_dashboard_package...` fail).
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    try:
        import requests  # type: ignore
    except Exception as e:  # pragma: no cover
        raise SystemExit(f"Missing dependency: requests ({e})")

    # Import the Flask app without running the dev server.
    try:
        from gwas_dashboard_package.src.main import app  # type: ignore
    except Exception as e:
        raise SystemExit(f"Failed to import Flask app: {e}")

    server = _make_server(app, args.host, args.port)
    port = int(server.server_port)
    base_url = f"http://{args.host}:{port}"

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    checks: list[Check] = []
    session_id = None
    try:
        _wait_ready(base_url, args.timeout)

        # 1) Home page contains expected elements
        r = requests.get(base_url + "/", timeout=5)
        ok = r.status_code == 200 and "trait-search-input" in r.text and "selected-efo-id" in r.text
        checks.append(
            Check(
                "GET / (frontend served)",
                ok,
                f"status={r.status_code}, contains_ids={ok}",
            )
        )

        # 2) search-traits validation (len<3 -> 400)
        r = requests.post(base_url + "/api/search-traits", json={"query": "ab"}, timeout=5)
        ok = r.status_code == 400 and r.json().get("success") is False
        checks.append(Check("POST /api/search-traits (short query)", ok, f"status={r.status_code}"))

        # 3) search-traits happy path
        r = requests.post(base_url + "/api/search-traits", json={"query": "diabetes", "top_k": 3}, timeout=5)
        j = r.json()
        ok = r.status_code == 200 and j.get("success") is True and isinstance(j.get("results"), list)
        checks.append(Check("POST /api/search-traits (happy)", ok, f"status={r.status_code}, n={len(j.get('results') or [])}"))

        # 4) Upload VCF + ClinVar match
        with TemporaryDirectory() as td:
            vcf_path = Path(td) / "fixture.vcf"
            _write_fixture_vcf(vcf_path)
            with vcf_path.open("rb") as f:
                r = requests.post(base_url + "/api/upload-vcf", files={"vcfFile": ("fixture.vcf", f)}, timeout=20)
            j = r.json()
            session_id = j.get("session_id")
            ok = bool(r.status_code == 200 and j.get("success") is True and isinstance(session_id, str) and session_id)
            checks.append(Check("POST /api/upload-vcf", ok, f"status={r.status_code}, session_id={session_id!r}"))

            if ok:
                r = requests.post(
                    base_url + "/api/clinvar-match",
                    json={"session_id": session_id, "significance_filter": "pathogenic"},
                    timeout=10,
                )
                j = r.json()
                ok2 = r.status_code == 200 and j.get("success") is True and isinstance(j.get("matches"), list)
                checks.append(Check("POST /api/clinvar-match", ok2, f"status={r.status_code}, matches={len(j.get('matches') or [])}"))

        # 5) PGx summary
        r = requests.post(base_url + "/api/pgx-summary", json={"source": "toy"}, timeout=10)
        j = r.json()
        ok = r.status_code == 200 and j.get("success") is True and isinstance(j.get("summary"), dict) and isinstance(j.get("disclaimer_tags"), list)
        checks.append(Check("POST /api/pgx-summary", ok, f"status={r.status_code}, keys={sorted(list((j.get('summary') or {}).keys()))}"))

        # 6) Chat (facts + disclaimers + citations)
        payload = {
            "message": "Give me a research-only summary based on the provided facts.",
            "gwas_associations": [{"trait": "Type 2 Diabetes", "variant": "rs7903146", "p_value": "1e-8", "pubmed_id": "12345"}],
            "clinvar_matches": [{"variant_key": "1-1000-A-G", "clinical_significance": "pathogenic", "gene": "LDLR"}],
            "pgx_summary": {"genes": ["CYP2C19"], "drugs": ["clopidogrel"], "total_rows": 1},
        }
        r = requests.post(base_url + "/api/chat", json=payload, timeout=10)
        j = r.json()
        ok = (
            r.status_code == 200
            and j.get("success") is True
            and isinstance(j.get("answer"), str)
            and isinstance(j.get("disclaimer_tags"), list)
            and isinstance(j.get("citations"), list)
            and isinstance(j.get("risk_level"), str)
        )
        checks.append(Check("POST /api/chat", ok, f"status={r.status_code}, citations={len(j.get('citations') or [])}"))

    finally:
        server.shutdown()

    ok_all = all(c.ok for c in checks)
    summary = {
        "status": "PASS" if ok_all else "FAIL",
        "base_url": base_url,
        "checks": [c.__dict__ for c in checks],
    }
    print(json.dumps(summary, indent=2))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
