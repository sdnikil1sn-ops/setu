# SETU update5 — audit and patch notes

## Scope of this audit

Reviewed the API/runtime modules most relevant to authentication, authorization, database access, institution resolution, overlap scoring, and semantic comparison; the test files; dependency manifest; Supabase foundation migration; `.gitignore`; and both PRD documents. Evaluation/import scripts and datasets were inventoried but not all reviewed line-by-line in this pass. The archive does **not** contain the React/Vite frontend described by the PRD, so frontend behavior and end-to-end UI integration remain unaudited. No live Supabase credentials were present in the archive, and no live database changes were made.

## Changes made in this update

1. Added explicit profile authorization to `GET /api/v1/overlaps/candidates`. Until the overlap engine enforces bureau/region scope itself, only `Admin` and `Senior Management` roles may access cross-bureau candidate results.
2. Removed the duplicate overlap route registration.
3. Added regression coverage for a non-management role being denied overlap results and for institution resolution being denied when the profile check fails.
4. Cleaned duplicated patch decorators in `test_auth.py`.
5. Guarded the read-only database diagnostic in `test_db.py` so test discovery does not connect to the live database as a module-import side effect.
6. Re-encoded `requirements.txt` as UTF-8 and added the runtime packages imported by the project (`psycopg[binary]`, `rapidfuzz`, and `google-genai`). Added `requirements-dev.txt` for pytest.
7. Expanded `.gitignore` for environment files, pytest cache, and backup files.

## Findings still requiring work

### High priority

- The API still uses the same `DATABASE_URL` in `main.py`, `institution_resolution.py`, and `overlap_engine.py`. A separate least-privilege API connection has **not** been introduced yet.
- The current API handlers are read-only, but they connect as the existing database role. Database least privilege and an RLS policy design are not complete.
- The checked-in migration creates tables and indexes but does not declare RLS enablement or policies. This differs from the previously reported live Supabase state; migration/live-schema drift must be reconciled deliberately, not by blindly applying `FORCE ROW LEVEL SECURITY`.
- `/api/v1/summary` returns row counts for internal tables, including evaluation ground truth and audit/profile tables. Review whether the public/demo summary should include those counts.
- The overlap engine filters restricted records but does not implement per-region or per-bureau scope filtering. The new API role gate is intentionally conservative, not a substitute for future query-level scope enforcement.
- The institution resolution handler returns candidate details to any user whose profile passes `require_case_profile`; role-specific permission rules for this operation remain to be defined.

### Functional scope gaps against the included PRD

The archive has no frontend, and the current API has no coordination decision/write endpoints, case-link persistence workflow, coordination notes, alert acknowledgement endpoints, SLA administration, or CSV/PDF export routes. These features should be planned and implemented in dependency order; they are not claimed complete by this patch.

### Packaging and repository hygiene

The uploaded ZIP included `.git`, a Windows `.venv`, pytest cache, bytecode, and `test_auth.py.broken-backup`. These are excluded from the cleaned delivery archive because they are machine-specific or backup artifacts. Keep `.env` and all real credentials outside the archive.

## Verification status

- Static syntax compilation and structural checks are run for this update.
- Full pytest execution could not be performed in this environment because the archive's virtual environment is Windows-specific and the current execution environment has no network access to install the required native database and fuzzy-matching dependencies. Run the regression suite locally after installing `requirements-dev.txt`.
- No live database migrations or privilege changes were applied.
