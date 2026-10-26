-- SETU Phase 5C.4: non-login, non-bypass API privilege group.
-- This is staging only. It does NOT create RLS policies and does NOT change
-- the API's current DATABASE_URL. Do not claim RLS is enforced after this step.
--
-- Prerequisite: 0002_profiles_auth_link.sql and 0003_controlled_profile_linking.sql.
-- Safe to rerun.

BEGIN;

DO $role$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'setu_api') THEN
        CREATE ROLE setu_api NOLOGIN NOBYPASSRLS;
    END IF;
END
$role$;

-- Normalize security attributes if the role already existed.
ALTER ROLE setu_api NOLOGIN NOBYPASSRLS;

GRANT USAGE ON SCHEMA public TO setu_api;

-- Read-only groundwork for the current API's SELECT endpoints.
-- RLS policies will still be required before this role can see rows.
GRANT SELECT ON TABLE
    public.alerts,
    public.audit_logs,
    public.bureaus,
    public.case_actions,
    public.case_links,
    public.complaint_cases,
    public.coordination_notes,
    public.ground_truth_clusters,
    public.ground_truth_pairs,
    public.institution_aliases,
    public.institution_groups,
    public.institution_resolution_ground_truth,
    public.institutions,
    public.profiles,
    public.regions,
    public.setu_dataset_manifest,
    public.sla_rules
TO setu_api;

-- Keep future tables created by postgres readable by the privilege group.
-- This does not grant access to other roles.
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    GRANT SELECT ON TABLES TO setu_api;

COMMIT;

-- Verification: expected NOLOGIN=true, BYPASSRLS=false, public_usage=true.
SELECT
    r.rolname,
    r.rolcanlogin,
    r.rolbypassrls,
    has_schema_privilege(r.rolname, 'public', 'USAGE') AS public_schema_usage,
    (
        SELECT count(*)
        FROM information_schema.tables t
        WHERE t.table_schema = 'public'
          AND t.table_type = 'BASE TABLE'
          AND has_table_privilege(r.rolname,
                format('%I.%I', t.table_schema, t.table_name), 'SELECT')
    ) AS public_tables_with_select
FROM pg_roles r
WHERE r.rolname = 'setu_api';

-- The expected count is 17 for the current SETU schema.
