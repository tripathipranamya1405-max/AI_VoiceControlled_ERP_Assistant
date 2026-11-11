import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from app import auth, database
from app.erp_gateway import ROLE_PERMISSIONS, dispatch
from app.main import dashboard_summary, download_sales_report


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.original_db_path = database.DB_PATH
        self.temp_dir = tempfile.TemporaryDirectory()
        database.DB_PATH = Path(self.temp_dir.name) / "auth-test.db"
        database.init_db()
        self.env_patch = patch.dict(
            os.environ,
            {"ERP_AUTH_ENABLED": "1", "ERP_DEMO_ENABLED": "1"},
            clear=False,
        )
        self.env_patch.start()
        os.environ.pop("ERP_AUTH_USERS", None)
        auth._SESSIONS.clear()

    def tearDown(self):
        self.env_patch.stop()
        database.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_finance_and_sales_credentials_match_their_roles(self):
        _, finance = auth.login("finance", "Finance@123", "finance")
        _, sales = auth.login("sales", "Sales@123", "sales")

        self.assertEqual((finance["employee_id"], finance["role"]), ("E-002", "finance"))
        self.assertEqual((sales["employee_id"], sales["role"]), ("E-004", "sales"))

    def test_wrong_password_or_selected_role_is_rejected(self):
        with self.assertRaises(HTTPException) as bad_password:
            auth.login("finance", "wrong-password", "finance")
        self.assertEqual(bad_password.exception.status_code, 401)

        with self.assertRaises(HTTPException) as wrong_role:
            auth.login("finance", "Finance@123", "sales")
        self.assertEqual(wrong_role.exception.status_code, 401)

    def test_guest_session_needs_no_employee_credentials(self):
        token = auth.create_demo_session()
        guest = auth.resolve_user(None, session_cookie=token)
        self.assertEqual(guest["role"], "demo")

    def test_role_permissions_separate_sales_finance_and_guest_commands(self):
        self.assertIn("sales", ROLE_PERMISSIONS["get_sales_report"])
        self.assertNotIn("sales", ROLE_PERMISSIONS["get_expense_summary"])
        self.assertNotIn("sales", ROLE_PERMISSIONS["create_purchase_request"])
        self.assertIn("finance", ROLE_PERMISSIONS["get_expense_summary"])
        self.assertNotIn("finance", ROLE_PERMISSIONS["get_sales_report"])
        self.assertIn("demo", ROLE_PERMISSIONS["get_attendance_summary"])
        self.assertNotIn("demo", ROLE_PERMISSIONS["get_expense_summary"])
        self.assertNotIn("demo", ROLE_PERMISSIONS["mark_attendance"])
        self.assertNotIn("demo", ROLE_PERMISSIONS["create_purchase_request"])
        self.assertNotIn("demo", ROLE_PERMISSIONS["update_stock"])

    def test_disallowed_role_commands_are_rejected_before_execution(self):
        forbidden_commands = [
            ("get_sales_report", "finance"),
            ("get_expense_summary", "sales"),
            ("get_expense_summary", "demo"),
            ("mark_attendance", "demo"),
        ]
        for intent, role in forbidden_commands:
            with self.subTest(intent=intent, role=role):
                result = dispatch(intent, {}, role=role)
                self.assertFalse(result["ok"])
                self.assertIn("not permitted", result["error"])

    def test_finance_dashboard_hides_sales_and_sales_report_is_forbidden(self):
        finance_token, _ = auth.login("finance", "Finance@123", "finance")
        summary = dashboard_summary(authorization=None, session_cookie=finance_token)
        self.assertNotIn("sales_this_month", summary)

        with self.assertRaises(HTTPException) as forbidden_report:
            download_sales_report(
                period="this_month",
                format="csv",
                authorization=None,
                session_cookie=finance_token,
            )
        self.assertEqual(forbidden_report.exception.status_code, 403)

    def test_sales_dashboard_includes_sales_and_guest_does_not(self):
        sales_token, _ = auth.login("sales", "Sales@123", "sales")
        sales_summary = dashboard_summary(authorization=None, session_cookie=sales_token)
        self.assertIn("sales_this_month", sales_summary)

        guest_token = auth.create_demo_session()
        guest_summary = dashboard_summary(authorization=None, session_cookie=guest_token)
        self.assertNotIn("sales_this_month", guest_summary)

        with self.assertRaises(HTTPException) as forbidden_report:
            download_sales_report(
                period="this_month",
                format="csv",
                authorization=None,
                session_cookie=guest_token,
            )
        self.assertEqual(forbidden_report.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
