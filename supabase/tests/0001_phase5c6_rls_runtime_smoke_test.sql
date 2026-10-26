-- SETU Phase 5C.6 FIX: RLS runtime smoke test without temporary tables.
-- Run this whole script as one execution after migration 0005 has succeeded.
-- The test does not modify application rows. The temporary role grant is rolled back.
-- If an error occurs before ROLLBACK, run ROLLBACK; before doing anything else.

BEGIN;

GRANT setu_api TO postgres;
SET LOCAL ROLE setu_api;

DO $test$
DECLARE
    v_institutions bigint;
    v_demo_cases bigint;
    v_demo_profiles bigint;
    v_demo_audit_logs bigint;
    v_demo_actions bigint;
    v_unlinked_profiles bigint;
    v_unlinked_cases bigint;
    v_unlinked_restricted_cases bigint;
    v_unlinked_actions bigint;
    v_unlinked_links bigint;
    v_unlinked_alerts bigint;
    v_unlinked_notes bigint;
    v_unlinked_audit_logs bigint;
BEGIN
    -- Simulate demo-token request context.
    PERFORM set_config('setu.auth_user_id', '', true);
    PERFORM set_config('setu.demo_mode', 'true', true);

    SELECT count(*) INTO v_institutions FROM public.institutions;
    SELECT count(*) INTO v_demo_cases FROM public.complaint_cases;
    SELECT count(*) INTO v_demo_profiles FROM public.profiles;
    SELECT count(*) INTO v_demo_audit_logs FROM public.audit_logs;
    SELECT count(*) INTO v_demo_actions FROM public.case_actions;

    IF v_demo_cases <> 0 OR v_demo_profiles <> 0
       OR v_demo_audit_logs <> 0 OR v_demo_actions <> 0 THEN
        RAISE EXCEPTION
            'FAIL demo context: cases %, profiles %, audit logs %, case actions %',
            v_demo_cases, v_demo_profiles, v_demo_audit_logs, v_demo_actions;
    END IF;

    -- Simulate a verified Auth UUID that is not linked to any real profile.
    PERFORM set_config(
        'setu.auth_user_id',
        '11111111-1111-4111-8111-111111111111',
        true
    );
    PERFORM set_config('setu.demo_mode', 'false', true);

    SELECT count(*) INTO v_unlinked_profiles FROM public.profiles;
    SELECT count(*) INTO v_unlinked_cases FROM public.complaint_cases;
    SELECT count(*) INTO v_unlinked_restricted_cases
        FROM public.complaint_cases WHERE is_restricted IS TRUE;
    SELECT count(*) INTO v_unlinked_actions FROM public.case_actions;
    SELECT count(*) INTO v_unlinked_links FROM public.case_links;
    SELECT count(*) INTO v_unlinked_alerts FROM public.alerts;
    SELECT count(*) INTO v_unlinked_notes FROM public.coordination_notes;
    SELECT count(*) INTO v_unlinked_audit_logs FROM public.audit_logs;

    IF v_unlinked_profiles <> 0 OR v_unlinked_cases <> 0
       OR v_unlinked_restricted_cases <> 0 OR v_unlinked_actions <> 0
       OR v_unlinked_links <> 0 OR v_unlinked_alerts <> 0
       OR v_unlinked_notes <> 0 OR v_unlinked_audit_logs <> 0 THEN
        RAISE EXCEPTION
            'FAIL unlinked identity exposed protected rows: profiles %, cases %, restricted %, actions %, links %, alerts %, notes %, audit logs %',
            v_unlinked_profiles, v_unlinked_cases, v_unlinked_restricted_cases,
            v_unlinked_actions, v_unlinked_links, v_unlinked_alerts,
            v_unlinked_notes, v_unlinked_audit_logs;
    END IF;

    RAISE NOTICE
        'PASS: demo and unlinked-identity checks passed. Institutions visible in demo context: %',
        v_institutions;
END;
$test$;

-- A PASS NOTICE above means assertions succeeded. This final row is a simple status marker.
SELECT 'PASS - RLS runtime smoke test assertions completed'::text AS result;

ROLLBACK;
