-- Optional rollback for 0004_api_role_foundation.sql.
-- Run only if no later migration, role membership, or policy depends on setu_api.
-- The role must not have members or own objects.
BEGIN;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    REVOKE SELECT ON TABLES FROM setu_api;
REVOKE USAGE ON SCHEMA public FROM setu_api;
REVOKE SELECT ON ALL TABLES IN SCHEMA public FROM setu_api;
DROP ROLE setu_api;
COMMIT;
