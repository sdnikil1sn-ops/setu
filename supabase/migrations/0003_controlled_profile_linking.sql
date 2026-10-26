    -- SETU Phase 5C.2: controlled linking of a real SETU profile to Supabase Auth.
    -- Prerequisite: migration 0002_profiles_auth_link.sql has been applied.
    -- This migration creates a narrowly scoped SECURITY DEFINER function only.
    -- It does NOT create RLS policies, change existing table grants, or link rows.

    BEGIN;

    CREATE OR REPLACE FUNCTION public.link_setu_profile_to_auth_user(
        p_profile_user_id text,
        p_auth_user_id uuid
    )
    RETURNS TABLE (
        profile_user_id text,
        linked_auth_user_id uuid
    )
    LANGUAGE plpgsql
    SECURITY DEFINER
    SET search_path = pg_catalog, public, auth
    AS $function$
    DECLARE
        v_profile public.profiles%ROWTYPE;
    BEGIN
        IF p_profile_user_id IS NULL OR btrim(p_profile_user_id) = '' THEN
            RAISE EXCEPTION 'A profile user_id is required'
                USING ERRCODE = '22023';
        END IF;

        IF p_auth_user_id IS NULL THEN
            RAISE EXCEPTION 'A Supabase Auth user UUID is required'
                USING ERRCODE = '22023';
        END IF;

        SELECT p.*
        INTO v_profile
        FROM public.profiles AS p
        WHERE p.user_id = p_profile_user_id
        FOR UPDATE;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'SETU profile does not exist'
                USING ERRCODE = 'P0002';
        END IF;

        -- Synthetic/demo profiles must never be promoted by this function.
        IF v_profile.is_synthetic IS TRUE OR v_profile.demo_only IS TRUE THEN
            RAISE EXCEPTION 'Synthetic or demo profiles cannot be linked'
                USING ERRCODE = '42501';
        END IF;

        IF v_profile.role IS NULL OR v_profile.role NOT IN (
            'Admin',
            'Bureau Head',
            'Desk Officer',
            'Regional Officer',
            'Senior Management'
        ) THEN
            RAISE EXCEPTION 'Profile role is not eligible for authentication'
                USING ERRCODE = '42501';
        END IF;

        IF v_profile.role = 'Bureau Head' AND v_profile.bureau_id IS NULL THEN
            RAISE EXCEPTION 'Bureau Head profile requires bureau_id'
                USING ERRCODE = '23514';
        END IF;

        IF v_profile.role = 'Regional Officer' AND v_profile.region_id IS NULL THEN
            RAISE EXCEPTION 'Regional Officer profile requires region_id'
                USING ERRCODE = '23514';
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM auth.users AS u
            WHERE u.id = p_auth_user_id
        ) THEN
            RAISE EXCEPTION 'Supabase Auth user does not exist'
                USING ERRCODE = 'P0002';
        END IF;

        -- Idempotent retry is safe when the exact same link already exists.
        IF v_profile.auth_user_id = p_auth_user_id THEN
            RETURN QUERY SELECT v_profile.user_id, v_profile.auth_user_id;
            RETURN;
        END IF;

        IF v_profile.auth_user_id IS NOT NULL THEN
            RAISE EXCEPTION 'SETU profile is already linked to another Auth user'
                USING ERRCODE = '23505';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM public.profiles AS p
            WHERE p.auth_user_id = p_auth_user_id
            AND p.user_id <> p_profile_user_id
        ) THEN
            RAISE EXCEPTION 'Auth user is already linked to another SETU profile'
                USING ERRCODE = '23505';
        END IF;

        UPDATE public.profiles AS p
        SET auth_user_id = p_auth_user_id
        WHERE p.user_id = p_profile_user_id
        AND p.auth_user_id IS NULL;

        RETURN QUERY
        SELECT p.user_id, p.auth_user_id
        FROM public.profiles AS p
        WHERE p.user_id = p_profile_user_id;
    END;
    $function$;

    -- Never expose the SECURITY DEFINER function to public/ordinary user roles.
    REVOKE ALL ON FUNCTION public.link_setu_profile_to_auth_user(text, uuid)
        FROM PUBLIC;
    REVOKE ALL ON FUNCTION public.link_setu_profile_to_auth_user(text, uuid)
        FROM anon, authenticated;
    GRANT EXECUTE ON FUNCTION public.link_setu_profile_to_auth_user(text, uuid)
        TO service_role;

    COMMENT ON FUNCTION public.link_setu_profile_to_auth_user(text, uuid) IS
        'Privileged SETU profile-to-Auth link. Call only from a trusted administrative provisioning workflow after independently verifying the person and assigned profile.';

    COMMIT;

    -- Verification (read-only): should return one function row.
    SELECT
        p.proname AS function_name,
        pg_get_function_identity_arguments(p.oid) AS arguments,
        p.prosecdef AS security_definer
    FROM pg_proc AS p
    JOIN pg_namespace AS n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
    AND p.proname = 'link_setu_profile_to_auth_user';

    -- Verification (read-only): ordinary user roles should not have EXECUTE.
    SELECT
        has_function_privilege(
            'anon',
            'public.link_setu_profile_to_auth_user(text, uuid)',
            'EXECUTE'
        ) AS anon_can_execute,
        has_function_privilege(
            'authenticated',
            'public.link_setu_profile_to_auth_user(text, uuid)',
            'EXECUTE'
        ) AS authenticated_can_execute,
        has_function_privilege(
            'service_role',
            'public.link_setu_profile_to_auth_user(text, uuid)',
            'EXECUTE'
        ) AS service_role_can_execute;
