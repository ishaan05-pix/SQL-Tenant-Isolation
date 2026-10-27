from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sql_guard import guard_sql  # noqa: E402
from identity import IdentityBindingError, TenantPoolBindings  # noqa: E402
from oracle import expected_for  # noqa: E402


CASES = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))["cases"]


class SqlGuardTests(unittest.TestCase):
    def test_frozen_authorized_cases_are_rewritten(self):
        for case in CASES:
            if case["kind"] != "authorized":
                continue
            with self.subTest(case=case["id"]):
                decision = guard_sql(case["sql"], "tenant_a")
                self.assertEqual(decision.status, "rewritten")
                self.assertTrue(decision.sql)
                self.assertIn("tenant_a", decision.sql)

    def test_join_scopes_each_tenant_relation(self):
        decision = guard_sql(CASES[1]["sql"], "tenant_a")
        self.assertEqual(decision.status, "rewritten")
        self.assertEqual(set(decision.tenant_relations_scoped), {"o", "c"})

    def test_explicit_inner_join_is_supported_and_other_join_shapes_rejected(self):
        accepted = guard_sql(
            "SELECT o.order_id FROM orders o INNER JOIN customers c "
            "ON c.customer_id = o.customer_id",
            "tenant_a",
        )
        self.assertEqual(accepted.status, "rewritten")
        self.assertEqual(set(accepted.tenant_relations_scoped), {"o", "c"})

        unsupported = [
            "SELECT o.order_id FROM orders o LEFT JOIN customers c ON c.customer_id = o.customer_id",
            "SELECT o.order_id FROM orders o CROSS JOIN customers c",
            "SELECT o.order_id FROM orders o NATURAL JOIN customers c",
            "SELECT order_id FROM orders, customers",
        ]
        for sql in unsupported:
            with self.subTest(sql=sql):
                decision = guard_sql(sql, "tenant_a")
                self.assertEqual(decision.status, "rejected")
                self.assertEqual(decision.reason, "unsupported_join_type")

    def test_cte_scopes_underlying_relation(self):
        decision = guard_sql(CASES[2]["sql"], "tenant_a")
        self.assertEqual(decision.status, "rewritten")
        self.assertEqual(decision.tenant_relations_scoped, ("orders",))

    def test_explicit_conflict_has_distinct_rejection_reason(self):
        decision = guard_sql(CASES[5]["sql"], "tenant_a")
        self.assertEqual(decision.status, "rejected")
        self.assertEqual(decision.reason, "explicit_conflicting_tenant")

    def test_fail_closed_statement_and_relation_checks(self):
        checks = {
            "SELECT 1; SELECT 2;": "multiple_statements",
            "DELETE FROM orders;": "non_read_only_or_unsupported_statement",
            "SELECT * FROM payments;": "unsupported_or_ambiguous_relation",
            "SELECT set_config('app.tenant_id', 'tenant_b', true) FROM orders;": "unsupported_function",
        }
        for sql, reason in checks.items():
            with self.subTest(sql=sql):
                decision = guard_sql(sql, "tenant_a")
                self.assertEqual(decision.status, "rejected")
                self.assertEqual(decision.reason, reason)

    def test_nested_writes_select_into_and_locks_are_rejected(self):
        checks = {
            "WITH removed AS (DELETE FROM orders RETURNING order_id) SELECT order_id FROM orders;": "non_read_only_or_unsupported_statement",
            "SELECT order_id INTO report_orders FROM orders;": "non_read_only_or_unsupported_statement",
            "SELECT order_id FROM orders FOR UPDATE;": "non_read_only_or_unsupported_statement",
        }
        for sql, reason in checks.items():
            with self.subTest(sql=sql):
                decision = guard_sql(sql, "tenant_a")
                self.assertEqual(decision.status, "rejected")
                self.assertEqual(decision.reason, reason)

    def test_schema_qualified_fixture_relation_is_rejected(self):
        decision = guard_sql("SELECT order_id FROM secret.orders;", "tenant_a")
        self.assertEqual(decision.status, "rejected")
        self.assertEqual(decision.reason, "unsupported_or_ambiguous_relation")

    def test_cte_name_does_not_allow_same_named_physical_relation(self):
        checks = [
            "WITH payments AS (SELECT order_id FROM payments) SELECT order_id FROM payments;",
            "WITH first_cte AS (SELECT order_id FROM later_cte), later_cte AS (SELECT order_id FROM orders) SELECT order_id FROM first_cte;",
        ]
        for sql in checks:
            with self.subTest(sql=sql):
                decision = guard_sql(sql, "tenant_a")
                self.assertEqual(decision.status, "rejected")
                self.assertEqual(decision.reason, "unsupported_or_ambiguous_relation")

    def test_explicit_conflict_is_not_unsupported_or_parse_failure(self):
        decision = guard_sql(CASES[5]["sql"], "tenant_a")
        self.assertNotIn(decision.reason, {"parse_failure", "unsupported_function", "unsupported_or_ambiguous_relation"})

    def test_independent_oracle_matches_declared_expected_results(self):
        fixture_doc = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
        for case in CASES:
            with self.subTest(case=case["id"]):
                result = expected_for(case, fixture_doc["schema"])
                if case["id"] == "C4":
                    self.assertEqual(result["authorized"], case["expected"])
                    self.assertEqual(result["forbidden_contribution"], case["forbidden_contribution"])
                    self.assertEqual(result["unscoped"], case["unscoped_result"])
                elif case["id"] == "C6":
                    self.assertEqual(result["authorized"], case["expected"])
                elif case["id"] == "C7":
                    self.assertEqual(result, case["expected_by_tenant"])
                else:
                    self.assertEqual(result["authorized"], case["expected"])

    def test_principal_mapping_rejects_mismatched_tenant(self):
        bindings = TenantPoolBindings({"tenant_a": "app_tenant_a", "tenant_b": "app_tenant_b"})
        bindings.assert_checkout("tenant_a", "app_tenant_a")
        bindings.assert_checkout("tenant_b", "app_tenant_b")
        with self.assertRaisesRegex(IdentityBindingError, "request_database_principal_mismatch"):
            bindings.assert_checkout("tenant_b", "app_tenant_a")


if __name__ == "__main__":
    unittest.main()
