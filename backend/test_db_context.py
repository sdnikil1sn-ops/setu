import unittest
from unittest.mock import MagicMock, call

from db_context import (
    apply_connection_context,
    reset_request_db_context,
    set_request_db_context,
)


class TestRequestDatabaseContext(unittest.TestCase):
    def test_connection_context_is_transaction_local(self):
        tokens = set_request_db_context(
            auth_user_id="11111111-1111-1111-1111-111111111111",
            demo_mode=False,
        )
        try:
            conn = MagicMock()
            result = apply_connection_context(conn)
            self.assertIs(result, conn)
            cursor = conn.cursor.return_value.__enter__.return_value
            cursor.execute.assert_called_once()
            args = cursor.execute.call_args.args
            self.assertIn("set_config('setu.auth_user_id'", args[0])
            self.assertIn("set_config('setu.demo_mode'", args[0])
            self.assertEqual(
                args[1],
                ("11111111-1111-1111-1111-111111111111", "false"),
            )
        finally:
            reset_request_db_context(tokens)

    def test_demo_context_has_no_staff_identity(self):
        tokens = set_request_db_context(demo_mode=True)
        try:
            conn = MagicMock()
            apply_connection_context(conn)
            cursor = conn.cursor.return_value.__enter__.return_value
            self.assertEqual(
                cursor.execute.call_args.args[1],
                ("", "true"),
            )
        finally:
            reset_request_db_context(tokens)


if __name__ == "__main__":
    unittest.main()
