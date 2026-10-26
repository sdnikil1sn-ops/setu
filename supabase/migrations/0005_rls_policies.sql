-- SETU Phase 5C.5: explicit read policies for the staged setu_api role.
-- Apply only after Phase 5C.5 Python tests pass.
-- Existing API uses postgres and remains operational; do NOT switch credentials yet.
-- All policies are TO setu_api only. anon/authenticated policies are not added.
-- Synthetic/demo profiles cannot be used to authorize real staff access.

BEGIN;

CREATE OR REPLACE FUNCTION public.setu_current_auth_user_id()
RETURNS uuid
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
DECLARE
    raw_user_id text;
BEGIN
    raw_user_id := current_setting('setu.auth_user_id', true);
    IF raw_user_id IS NULL OR btrim(raw_user_id) = '' THEN
        RETURN NULL;
    END IF;
    RETURN raw_user_id::uuid;
EXCEPTION
    WHEN invalid_text_representation THEN
        RETURN NULL;
END;
$function$;

CREATE OR REPLACE FUNCTION public.setu_is_demo_request()
RETURNS boolean
LANGUAGE sql
STABLE
SET search_path = pg_catalog, public
AS $function$
    SELECT COALESCE(current_setting('setu.demo_mode', true) = 'true', false);
$function$;

CREATE OR REPLACE FUNCTION public.setu_current_profile()
RETURNS TABLE (
    user_id text,
    role text,
    bureau_id text,
    region_id text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
    SELECT p.user_id, p.role, p.bureau_id, p.region_id
    FROM public.profiles AS p
    WHERE p.auth_user_id = public.setu_current_auth_user_id()
      AND p.is_synthetic IS FALSE
      AND p.demo_only IS FALSE
      AND p.role IN (
          'Admin', 'Senior Management', 'Regional Officer',
          'Bureau Head', 'Desk Officer'
      )
    LIMIT 1;
$function$;

CREATE OR REPLACE FUNCTION public.setu_has_real_profile()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
    SELECT EXISTS (SELECT 1 FROM public.setu_current_profile());
$function$;

CREATE OR REPLACE FUNCTION public.setu_is_management()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
    SELECT EXISTS (
        SELECT 1 FROM public.setu_current_profile() p
        WHERE p.role IN ('Admin', 'Senior Management')
    );
$function$;

CREATE OR REPLACE FUNCTION public.setu_can_read_case(target_case_id text)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
    SELECT EXISTS (
        SELECT 1
        FROM public.complaint_cases c
        CROSS JOIN LATERAL public.setu_current_profile() p
        WHERE c.case_id = target_case_id
          AND c.is_restricted IS FALSE
          AND CASE p.role
              WHEN 'Admin' THEN true
              WHEN 'Senior Management' THEN true
              WHEN 'Regional Officer' THEN c.region_id = p.region_id
              WHEN 'Bureau Head' THEN c.current_bureau_id = p.bureau_id
              WHEN 'Desk Officer' THEN c.assigned_user_id = p.user_id
              ELSE false
          END
    );
$function$;

CREATE OR REPLACE FUNCTION public.setu_can_read_link(target_link_id text)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
    SELECT EXISTS (
        SELECT 1
        FROM public.case_links l
        WHERE l.link_id = target_link_id
          AND public.setu_can_read_case(l.case_a)
          AND public.setu_can_read_case(l.case_b)
    );
$function$;

-- These helpers are internal policy primitives, not public RPC endpoints.
REVOKE ALL ON FUNCTION public.setu_current_auth_user_id() FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.setu_is_demo_request() FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.setu_current_profile() FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.setu_has_real_profile() FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.setu_is_management() FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.setu_can_read_case(text) FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.setu_can_read_link(text) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION public.setu_current_auth_user_id() TO setu_api;
GRANT EXECUTE ON FUNCTION public.setu_is_demo_request() TO setu_api;
GRANT EXECUTE ON FUNCTION public.setu_current_profile() TO setu_api;
GRANT EXECUTE ON FUNCTION public.setu_has_real_profile() TO setu_api;
GRANT EXECUTE ON FUNCTION public.setu_is_management() TO setu_api;
GRANT EXECUTE ON FUNCTION public.setu_can_read_case(text) TO setu_api;
GRANT EXECUTE ON FUNCTION public.setu_can_read_link(text) TO setu_api;

-- Ensure RLS remains enabled. Do not FORCE it: setu_api is not table owner.
ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bureaus ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.case_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.case_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.complaint_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coordination_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ground_truth_clusters ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ground_truth_pairs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.institution_aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.institution_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.institution_resolution_ground_truth ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.institutions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.regions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.setu_dataset_manifest ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sla_rules ENABLE ROW LEVEL SECURITY;

-- Remove only policies owned by this migration, allowing safe reruns.
DROP POLICY IF EXISTS setu_profiles_select_self ON public.profiles;
DROP POLICY IF EXISTS setu_institutions_select ON public.institutions;
DROP POLICY IF EXISTS setu_aliases_select_staff ON public.institution_aliases;
DROP POLICY IF EXISTS setu_cases_select_scoped ON public.complaint_cases;
DROP POLICY IF EXISTS setu_actions_select_scoped ON public.case_actions;
DROP POLICY IF EXISTS setu_links_select_scoped ON public.case_links;
DROP POLICY IF EXISTS setu_alerts_select_scoped ON public.alerts;
DROP POLICY IF EXISTS setu_notes_select_scoped ON public.coordination_notes;
DROP POLICY IF EXISTS setu_audit_select_management ON public.audit_logs;
DROP POLICY IF EXISTS setu_bureaus_select_staff ON public.bureaus;
DROP POLICY IF EXISTS setu_regions_select_staff ON public.regions;
DROP POLICY IF EXISTS setu_groups_select_staff ON public.institution_groups;
DROP POLICY IF EXISTS setu_sla_select_staff ON public.sla_rules;
DROP POLICY IF EXISTS setu_gt_pairs_select_management ON public.ground_truth_pairs;
DROP POLICY IF EXISTS setu_gt_clusters_select_management ON public.ground_truth_clusters;
DROP POLICY IF EXISTS setu_resolution_gt_select_management ON public.institution_resolution_ground_truth;
DROP POLICY IF EXISTS setu_manifest_select_management ON public.setu_dataset_manifest;

-- A profile can read only its own real, approved profile row.
CREATE POLICY setu_profiles_select_self ON public.profiles
FOR SELECT TO setu_api
USING (
    auth_user_id = public.setu_current_auth_user_id()
    AND is_synthetic IS FALSE
    AND demo_only IS FALSE
);

-- Demo token is deliberately limited to the existing institution-list route.
-- This policy permits the server's demo request context to read institution rows;
-- API middleware continues to reject demo tokens on all other routes.
CREATE POLICY setu_institutions_select ON public.institutions
FOR SELECT TO setu_api
USING (
    public.setu_is_demo_request()
    OR public.setu_has_real_profile()
);

CREATE POLICY setu_aliases_select_staff ON public.institution_aliases
FOR SELECT TO setu_api
USING (public.setu_has_real_profile());

CREATE POLICY setu_cases_select_scoped ON public.complaint_cases
FOR SELECT TO setu_api
USING (public.setu_can_read_case(case_id));

CREATE POLICY setu_actions_select_scoped ON public.case_actions
FOR SELECT TO setu_api
USING (public.setu_can_read_case(case_id));

CREATE POLICY setu_links_select_scoped ON public.case_links
FOR SELECT TO setu_api
USING (public.setu_can_read_link(link_id));

CREATE POLICY setu_alerts_select_scoped ON public.alerts
FOR SELECT TO setu_api
USING (
    CASE
        -- If an alert refers to a link, both linked cases must be visible.
        WHEN link_id IS NOT NULL
            THEN public.setu_can_read_link(link_id)
        WHEN case_id IS NOT NULL
            THEN public.setu_can_read_case(case_id)
        ELSE false
    END
);

CREATE POLICY setu_notes_select_scoped ON public.coordination_notes
FOR SELECT TO setu_api
USING (public.setu_can_read_link(link_id));

CREATE POLICY setu_audit_select_management ON public.audit_logs
FOR SELECT TO setu_api
USING (public.setu_is_management());

CREATE POLICY setu_bureaus_select_staff ON public.bureaus
FOR SELECT TO setu_api
USING (public.setu_has_real_profile());

CREATE POLICY setu_regions_select_staff ON public.regions
FOR SELECT TO setu_api
USING (public.setu_has_real_profile());

CREATE POLICY setu_groups_select_staff ON public.institution_groups
FOR SELECT TO setu_api
USING (public.setu_has_real_profile());

CREATE POLICY setu_sla_select_staff ON public.sla_rules
FOR SELECT TO setu_api
USING (public.setu_has_real_profile());

CREATE POLICY setu_gt_pairs_select_management ON public.ground_truth_pairs
FOR SELECT TO setu_api
USING (public.setu_is_management());

CREATE POLICY setu_gt_clusters_select_management ON public.ground_truth_clusters
FOR SELECT TO setu_api
USING (public.setu_is_management());

CREATE POLICY setu_resolution_gt_select_management ON public.institution_resolution_ground_truth
FOR SELECT TO setu_api
USING (public.setu_is_management());

CREATE POLICY setu_manifest_select_management ON public.setu_dataset_manifest
FOR SELECT TO setu_api
USING (public.setu_is_management());

COMMIT;

-- Verification summary: expected 17 policies, one on each public table.
SELECT
    count(*) AS setu_policy_count,
    count(DISTINCT tablename) AS tables_with_setu_policies
FROM pg_policies
WHERE schemaname = 'public'
  AND policyname LIKE 'setu\_%' ESCAPE '\';

-- Expected: 17 policies across 17 tables.
-- This migration intentionally adds SELECT policies only; it grants no writes.
