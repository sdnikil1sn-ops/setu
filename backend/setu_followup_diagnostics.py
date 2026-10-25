"""Focused SETU follow-up diagnostics; no DB writes and no secret values printed."""
from pathlib import Path
import ast
import re
import os

ROOT = Path(__file__).resolve().parent
print("SETU FOLLOW-UP DIAGNOSTICS")
print(f"Backend: {ROOT}")
print("This script does not change application files or database rows.")

# 1) Inspect potentially unsafe exception responses, with filename and line only.
print("\n--- A. Exception handling: source locations for manual review ---")
source_names = ("main.py", "auth.py", "db_context.py", "overlap_engine.py")
patterns = [
    re.compile(r"(?i)\bdetail\s*=\s*(?:str\s*\(\s*exc\s*\)|repr\s*\(\s*exc\s*\)|traceback)"),
    re.compile(r"(?i)\bHTTPException\s*\([^)]*(?:str\s*\(\s*exc\s*\)|repr\s*\(\s*exc\s*\))"),
    re.compile(r"(?i)\b(traceback\.print_exc|print\s*\(\s*exc\s*\)|logger\.(?:exception|error)\s*\()"),
]
hits = []
for name in source_names:
    path = ROOT / name
    if not path.exists():
        continue
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for i, line in enumerate(lines, 1):
        if any(p.search(line) for p in patterns):
            hits.append((name, i, line.strip()[:220]))
if hits:
    for name, line_no, excerpt in hits:
        print(f"{name}:{line_no}: {excerpt}")
    print("Review each hit: internal logging can be appropriate; returning raw exception text to an API client is usually not.")
else:
    print("No direct match in the four scanned files. This is a heuristic scan, not proof.")

# 2) Confirm test files that exercise the security boundary.
print("\n--- B. Existing security-test inventory ---")
test_names = [
    "test_rls_migration_contract.py",
    "test_setu_phase6_direct_login_rls.py",
    "test_db_context.py",
    "test_case_authorization.py",
    "test_single_case_scope.py",
    "test_sensitive_endpoint_authorization.py",
]
for name in test_names:
    path = ROOT / name
    if not path.exists():
        print(f"MISSING: {name}")
        continue
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        count = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")
                    for n in ast.walk(tree))
        print(f"FOUND: {name} ({count} test functions)")
    except Exception as e:
        print(f"UNREADABLE: {name} ({type(e).__name__})")

# 3) Report presence only, never values.
print("\n--- C. Configuration status (presence only) ---")
try:
    from dotenv import dotenv_values
    env_values = dotenv_values(ROOT / ".env") if (ROOT / ".env").exists() else {}
except Exception:
    env_values = {}
def configured(key):
    return bool(os.getenv(key) or env_values.get(key))
for key in ("SETU_API_DATABASE_URL", "SUPABASE_URL", "SETU_API_TOKEN",
            "SETU_IMPORTER_DATABASE_URL", "SETU_BACKUP_DIR", "SETU_LOG_LEVEL"):
    value = os.getenv(key) or env_values.get(key)
    if key == "SETU_BACKUP_DIR" and value:
        exists = Path(value).exists()
        print(f"{key}: configured; target_exists={exists}")
    else:
        print(f"{key}: {'configured' if configured(key) else 'not configured'}")

# 4) Report backup/logging clues in project config without printing secret values.
print("\n--- D. Backup/logging configuration clues ---")
files = [ROOT / "main.py", ROOT / "logging_config.py", ROOT / "backup.py",
         ROOT / "pyproject.toml", ROOT / "requirements.txt"]
clues = re.compile(r"(?i)(logging\.basicConfig|dictConfig|RotatingFileHandler|TimedRotatingFileHandler|backup|pg_dump|restore)")
found = []
for path in files:
    if not path.exists():
        continue
    for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if clues.search(line):
            found.append(f"{path.name}:{i}")
print("\n".join(found[:80]) if found else "No obvious backup/logging implementation clues in the selected files.")
if len(found) > 80:
    print(f"... {len(found)-80} additional matching lines omitted")

print("\n--- E. Required decisions that cannot be auto-certified ---")
print("Restricted-row isolation: requires test fixtures and role-specific assertions; a zero-row live table is inconclusive.")
print("Live overlap: synthetic scoring passes, but database candidate retrieval needs eligible non-sensitive sample data.")
print("Importer credentials: leave unset until a separate least-privilege importer role is deliberately configured.")
print("Backup: a directory setting is not enough; verify a real backup and successful restore in a non-production target.")
print("Authenticated E2E: requires valid test-user tokens for the intended roles; do not paste tokens into chat.")
print("End of diagnostics.")
