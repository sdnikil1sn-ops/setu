-- SETU Phase 5C: additive profile-to-Supabase-Auth mapping
-- Purpose: introduce an explicit link between an application profile and a
-- Supabase Auth identity before designing user-scoped RLS policies.
--
-- SAFETY:
--   * Additive only: does not revoke grants, change existing columns, or add RLS policies.
--   * Existing synthetic profiles remain unchanged and unlinked.
--   * Apply to a staging project first, then verify before production.

BEGIN;

ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS auth_user_id uuid;

DO $migration$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'profiles_auth_user_id_fkey'
          AND conrelid = 'public.profiles'::regclass
    ) THEN
        ALTER TABLE public.profiles
            ADD CONSTRAINT profiles_auth_user_id_fkey
            FOREIGN KEY (auth_user_id)
            REFERENCES auth.users (id)
            ON DELETE SET NULL;
    END IF;
END
$migration$;

-- A real Auth identity can be linked to at most one SETU profile.
-- NULL is allowed for existing synthetic/demo profiles.
CREATE UNIQUE INDEX IF NOT EXISTS profiles_auth_user_id_uidx
    ON public.profiles (auth_user_id)
    WHERE auth_user_id IS NOT NULL;

COMMENT ON COLUMN public.profiles.auth_user_id IS
    'Optional Supabase Auth identity linked to this SETU profile. NULL for synthetic/unlinked profiles.';

COMMIT;

-- Verification (read-only): expected auth_user_id column and index to exist.
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'profiles'
  AND column_name = 'auth_user_id';

SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename = 'profiles'
  AND indexname = 'profiles_auth_user_id_uidx';
