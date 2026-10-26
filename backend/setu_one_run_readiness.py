from __future__ import annotations

import os
import re
import sys
import json
import shutil
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "setu_one_run_readiness_report.txt"
results: list[tuple[str, str, str]] = []
details: list[str] = []

def record(name: str, status: str, note: str) -> None:
    results.append((name, status, note))
    print(f"[{status}] {name}: {note}")

def run_cmd(label: str, args: list[str], timeout: int = 900) -> tuple[int, str]:
    print(f"\n--- {label} ---")
    try:
        p = subprocess.run(
            args, cwd=ROOT, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=timeout, check=False
        )
        output = p.stdout or ""
        print(output[-12000:])
        return p.returncode, output
    except Exception as exc:
        print(f"Could not run command: {type(exc).__name__}: {exc}")
        return 999, str(exc)

def env_present(name: str) -> bool:
    return bool(os.getenv(name, "").strip())

def check_http(path: str, expected: set[int], headers: dict[str, str] | None = None) -> tuple[bool, str]:
    base = os.getenv("SETU_AUDIT_BASE_URL", "http://127.0.0.1:8081").rstrip("/")
    req = urllib.request.Request(base + path, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            code = resp.status
            body = resp.read(1200).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        code = exc.code
        body = exc.read(1200).decode("utf-8", "replace")
    except Exception as exc:
        return False, f"API unavailable ({type(exc).__name__}); start the API or set SETU_AUDIT_BASE_URL"
    # Do not print tokens or full response bodies.
    return code in expected, f"HTTP {code}; expected {sorted(expected)}"

def main() -> int:
    print("SETU ONE-RUN READINESS CHECK")
    print(f"Backend: {ROOT}")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("Safety: no application/database rows are changed by this runner.")
    print("A PASS means only the stated check passed; BLOCKED means evidence/configuration is missing.")

    # 1. Full automated suite
    if shutil.which("pytest") or (ROOT / ".venv" / "Scripts" / "pytest.exe").exists():
        pytest_exe = str(ROOT / ".venv" / "Scripts" / "pytest.exe") if (ROOT / ".venv" / "Scripts" / "pytest.exe").exists() else "pytest"
        code, out = run_cmd("Full test suite", [pytest_exe, "-q"], 1200)
        record("Full automated tests", "PASS" if code == 0 else "FAIL", "pytest -q exit " + str(code))
    else:
        code, out = run_cmd("Full test suite", [sys.executable, "-m", "pytest", "-q"], 1200)
        record("Full automated tests", "PASS" if code == 0 else "FAIL", "python -m pytest exit " + str(code))

    # 2. RLS and role coverage: inventory existing tests; do not fake a live-data PASS.
    rls_files = [
        "test_rls_migration_contract.py", "test_setu_phase6_direct_login_rls.py",
        "test_db_context.py", "test_case_authorization.py", "test_single_case_scope.py",
        "test_sensitive_endpoint_authorization.py"
    ]
    present = [name for name in rls_files if (ROOT / name).exists()]
    record("Security test inventory", "PASS" if len(present) >= 4 else "REVIEW",
           f"{len(present)}/{len(rls_files)} expected test files found")
    live_fixture_vars = [
        "SETU_RLS_TEST_DATABASE_URL",
        "SETU_RLS_ALLOWED_CASE_ID",
        "SETU_RLS_RESTRICTED_CASE_ID",
        "SETU_RLS_OUT_OF_SCOPE_CASE_ID",
    ]
    missing_fixture = [name for name in live_fixture_vars if not env_present(name)]
    if missing_fixture:
        record("Real-row RLS isolation", "BLOCKED",
               "No dedicated controlled RLS fixture configuration; missing " + ", ".join(missing_fixture))
    else:
        record("Real-row RLS isolation", "REVIEW",
               "Fixture variables exist, but this generic runner will not assume schema/role semantics; execute project-specific assertions against the isolated test DB")

    # 3. Role-by-role E2E tokens: presence only, never print values.
    role_vars = [
        "SETU_AUDIT_TOKEN_ADMIN",
        "SETU_AUDIT_TOKEN_SENIOR_MANAGEMENT",
        "SETU_AUDIT_TOKEN_BUREAU_HEAD",
        "SETU_AUDIT_TOKEN_REGIONAL_OFFICER",
        "SETU_AUDIT_TOKEN_DESK_OFFICER",
    ]
    configured_roles = [name for name in role_vars if env_present(name)]
    missing_roles = [name for name in role_vars if not env_present(name)]
    if len(configured_roles) == len(role_vars):
        record("Role-by-role E2E credentials", "REVIEW",
               "All five token variables are present; actual role-by-role endpoint assertions still require project-specific expectations")
    else:
        record("Role-by-role E2E credentials", "BLOCKED",
               f"{len(configured_roles)}/{len(role_vars)} token variables configured; missing: " + ", ".join(missing_roles))

    # 4. Overlap detection: run unit/scoring tests and optional live smoke test.
    overlap_test = ROOT / "test_overlap_engine.py"
    if overlap_test.exists():
        code, out = run_cmd("Overlap engine tests", [sys.executable, "-m", "pytest", "-q", str(overlap_test)], 600)
        record("Overlap scoring/tests", "PASS" if code == 0 else "FAIL", "overlap test exit " + str(code))
        if env_present("SETU_OVERLAP_TEST_DATABASE_URL") and os.getenv("SETU_OVERLAP_TEST_DATABASE_URL", "").strip().lower().endswith(("_test", "_testing")):
            record("Live overlap candidate retrieval", "REVIEW",
                   "Dedicated test DB URL appears configured; run the repository's documented live-db smoke test and confirm eligible fixture pairs")
        else:
            record("Live overlap candidate retrieval", "BLOCKED",
                   "No explicitly named isolated overlap test DB configured; zero live candidates cannot prove retrieval")
    else:
        record("Overlap scoring/tests", "BLOCKED", "test_overlap_engine.py not found")
        record("Live overlap candidate retrieval", "BLOCKED", "No project-specific live candidate test was run")

    # 5. Backup/restore: safe checks only; never overwrite a DB or create a backup of prod silently.
    backup_dir_value = os.getenv("SETU_BACKUP_DIR", "").strip()
    restore_url = os.getenv("SETU_RESTORE_TEST_DATABASE_URL", "").strip()
    pg_dump = shutil.which("pg_dump")
    pg_restore = shutil.which("pg_restore")
    if backup_dir_value and Path(backup_dir_value).expanduser().exists() and Path(backup_dir_value).expanduser().is_dir():
        record("Backup directory", "PASS", "SETU_BACKUP_DIR exists and is a directory")
    else:
        record("Backup directory", "BLOCKED", "SETU_BACKUP_DIR is absent or does not point to an existing directory")
    if pg_dump and pg_restore:
        record("PostgreSQL backup tools", "PASS", "pg_dump and pg_restore are available")
    else:
        record("PostgreSQL backup tools", "BLOCKED", "pg_dump/pg_restore not both found on PATH")
    if restore_url and re.search(r"(_restore_test|_test|_testing)(?:\?|$)", restore_url, re.I):
        record("Restore target guard", "REVIEW", "Test-like target name detected; restore NOT executed automatically to avoid destructive changes")
    else:
        record("Backup restore proof", "BLOCKED",
               "No clearly designated SETU_RESTORE_TEST_DATABASE_URL ending in _restore_test, _test, or _testing; no restore attempted")

    # 6. Exception and logging scan (heuristic, reports locations only).
    source_files = [ROOT / n for n in ("main.py", "auth.py", "db_context.py", "overlap_engine.py")]
    hits: list[str] = []
    raw_pattern = re.compile(r"detail\s*=\s*str\s*\(\s*exc\s*\)|detail\s*=\s*repr\s*\(\s*exc\s*\)", re.I)
    for path in source_files:
        if not path.exists():
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            if raw_pattern.search(line):
                hits.append(f"{path.name}:{i}")
    log_level = os.getenv("SETU_LOG_LEVEL", "").strip()
    if hits:
        record("Exception-detail heuristic scan", "REVIEW", "Potential raw exception details at " + ", ".join(hits))
    else:
        record("Exception-detail heuristic scan", "PASS", "No direct detail=str(exc)/repr(exc) pattern found in selected files")
    if log_level:
        record("Log-level configuration", "PASS", f"SETU_LOG_LEVEL is set ({log_level.upper()}); value not validated against app configuration")
    else:
        record("Log-level configuration", "REVIEW", "SETU_LOG_LEVEL is unset; inspect actual logging configuration and deployment defaults")

    # 7. Importer: no importer is invoked; check whether a dedicated credential exists.
    if env_present("SETU_IMPORTER_DATABASE_URL"):
        record("Importer credential presence", "REVIEW",
               "SETU_IMPORTER_DATABASE_URL is configured; verify its grants are least-privilege before enabling import")
    else:
        record("Importer credential presence", "BLOCKED",
               "SETU_IMPORTER_DATABASE_URL is not configured; importer remains unverified and should stay disabled")

    # 8. Basic HTTP checks, if server is reachable.
    ok, note = check_http("/health", {200})
    record("Health endpoint", "PASS" if ok else "BLOCKED", note)
    ok, note = check_http("/api/v1/summary", {401, 403})
    record("Unauthenticated sensitive endpoint denial", "PASS" if ok else "REVIEW", note)
    api_token = os.getenv("SETU_API_TOKEN", "").strip()
    if api_token:
        ok, note = check_http("/api/v1/institutions", {200}, {"X-SETU-API-TOKEN": api_token})
        record("Demo-token institutions route", "PASS" if ok else "REVIEW", note)
        ok, note = check_http("/api/v1/summary", {401, 403}, {"X-SETU-API-TOKEN": api_token})
        record("Demo-token sensitive route denial", "PASS" if ok else "REVIEW", note)
    else:
        record("Demo-token route checks", "BLOCKED", "SETU_API_TOKEN is not configured in this process environment; no token value printed")

    # Save concise report.
    lines = [
        "SETU ONE-RUN READINESS REPORT",
        f"Backend: {ROOT}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        *[f"{status}\t{name}\t{note}" for name, status, note in results],
        "",
        "Interpretation: this is a triage report, not a production certification.",
        "RLS fixture assertions and restore validation are deliberately not auto-run without an isolated target and explicit project-specific test logic."
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n--- SUMMARY ---")
    for status in ("FAIL", "BLOCKED", "REVIEW", "PASS"):
        count = sum(1 for _, s, _ in results if s == status)
        print(f"{status}={count}")
    print(f"Report saved: {REPORT}")
    return 1 if any(status == "FAIL" for _, status, _ in results) else 0

if __name__ == "__main__":
    raise SystemExit(main())
