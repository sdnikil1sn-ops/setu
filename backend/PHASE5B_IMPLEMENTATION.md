# SETU Phase 5B — Security patch and test instructions

## Changes in this patch

- `/api/v1/summary` now requires an approved profile and is restricted to `Admin` and `Senior Management`.
- `/api/v1/overlaps/semantic-check`, when explicitly enabled, now requires an approved profile and is restricted to `Admin` and `Senior Management`.
- Institution list queries select only the six fields returned by that endpoint, instead of querying every column and filtering afterward.
- Institution-resolution candidates are capped at five and restricted to the documented response fields.
- Runtime database modules prefer `SETU_API_DATABASE_URL`, while preserving the existing `DATABASE_URL` fallback.
- The dataset importer prefers `SETU_IMPORTER_DATABASE_URL`, while preserving the existing `DATABASE_URL` fallback.
- Database-backed smoke scripts no longer connect to the database just because pytest imports their files. Run those scripts manually when you intentionally want a live read-only database check.
- Added `run_phase5b_tests.ps1` to compile Python files and run the full automated pytest suite.

## Run the automated tests on Windows PowerShell

From `E:\App\Project\setu\backend`:

```powershell
.\run_phase5b_tests.ps1
```

If required dependencies are not installed in the backend virtual environment:

```powershell
.\run_phase5b_tests.ps1 -InstallDependencies
```

The installation option creates `.venv` if missing and installs the packages declared by `requirements-dev.txt`. It does not apply database migrations or change Supabase roles.

## Database URL transition

The code supports these optional environment variables:

- `SETU_API_DATABASE_URL`: least-privilege runtime connection used by `main.py`, `institution_resolution.py`, and `overlap_engine.py`.
- `SETU_IMPORTER_DATABASE_URL`: separate importer connection used by `import_dataset.py`.
- `DATABASE_URL`: legacy fallback, retained to avoid breaking the existing application before the new roles are provisioned and tested.

Do not set the new variables until the matching database roles have been created, granted only required privileges, and tested against the actual Supabase schema. The legacy fallback means the app remains compatible, but it does **not** by itself remove the current RLS-bypass risk.

## Database security changes intentionally not automated

This patch does not create roles, change grants, add RLS policies, or enable `FORCE ROW LEVEL SECURITY`. The live schema currently has no policies visible in `pg_policies`; a safe policy migration must be designed together with trusted transaction-scoped user context and verified against real role assignments. Blindly applying broad policies could expose cross-bureau cases or break legitimate reads.

Before deploying the new connection variables, verify:

1. Every role has the expected `rolbypassrls = false`.
2. The API can read only the tables and columns it needs.
3. The importer can insert only approved dataset rows and manifest records.
4. Unauthorized, synthetic, unassigned, cross-region, cross-bureau, and restricted-case access is denied.
5. The automated test suite passes and a rollback connection string is available.

## Scope notes

- This patch preserves existing endpoint shapes except that the summary and semantic-check endpoints now enforce management-role authorization.
- The existing application-level case scoping is retained.
- No live Supabase credentials were included or used, and no live database changes were performed.
