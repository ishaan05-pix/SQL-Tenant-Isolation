"""Opt-in, read-only PostgreSQL checks for frozen C2 (join) and C4 (SUM).

These tests require the two already-provisioned fixture databases and local
password-file authentication. They never create or change database objects.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".vendor"))
sys.path.insert(0, str(ROOT))

from oracle import expected_for  # noqa: E402
from sql_guard import guard_sql  # noqa: E402


CASES_DOC = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
CASES = {case["id"]: case for case in CASES_DOC["cases"]}
FIXTURE = CASES_DOC["schema"]
OPTED_IN = os.environ.get("SIF_RUN_POSTGRES_TESTS") == "1"


def _psql_path() -> str | None:
    configured = os.environ.get("SIF_PSQL")
    if configured:
        return configured if Path(configured).is_file() else None
    return shutil.which("psql")


@unittest.skipUnless(
    OPTED_IN,
    "set SIF_RUN_POSTGRES_TESTS=1 to run read-only checks against existing fixtures",
)
class PostgresReadonlyIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.psql = _psql_path()
        if not cls.psql:
            raise unittest.SkipTest("psql not found; set SIF_PSQL to its executable path")
        cls.host = os.environ.get("SIF_PGHOST", "localhost")
        cls.port = os.environ.get("SIF_PGPORT", "5432")
        cls.user = os.environ.get("SIF_PGUSER", "sif_tenant_a")
        if cls.user != "sif_tenant_a":
            raise RuntimeError("these frozen cases and expectations require sif_tenant_a")

    def _run(self, database: str, sql: str) -> dict[str, object]:
        # All SQL runs in one explicit read-only transaction. -w forbids a
        # password prompt; libpq may use its normal local password file.
        query_statement = sql.rstrip()
        if not query_statement.endswith(";"):
            query_statement += ";"
        wrapped = (
            "BEGIN READ ONLY;\n"
            "SELECT '__SIF_ID__', current_user, session_user, current_database(), "
            "current_setting('transaction_read_only');\n"
            "SELECT '__SIF_META__', c.relname, r.rolsuper, r.rolbypassrls, "
            "r.rolcreatedb, r.rolcreaterole, r.rolinherit, "
            "pg_get_userbyid(c.relowner), c.relrowsecurity, c.relforcerowsecurity "
            "FROM pg_roles AS r CROSS JOIN pg_class AS c "
            "WHERE r.rolname = current_user "
            "AND c.oid IN ('public.orders'::regclass, 'public.customers'::regclass) "
            "ORDER BY c.relname;\n"
            f"{query_statement}\n"
            "ROLLBACK;"
        )
        command = [
            self.psql,
            "-X",
            "-w",
            "-qAt",
            "-F",
            "\t",
            "-v",
            "ON_ERROR_STOP=1",
            "-h",
            self.host,
            "-p",
            self.port,
            "-U",
            self.user,
            "-d",
            database,
            "-c",
            wrapped,
        ]
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            self.fail(
                f"psql failed for {database}, exit={completed.returncode}; "
                f"stderr={completed.stderr.strip()!r}; stdout={completed.stdout.strip()!r}"
            )
        lines = [line for line in completed.stdout.splitlines() if line]
        identity = None
        metadata: list[list[str]] = []
        rows: list[list[str]] = []
        for line in lines:
            fields = line.split("\t")
            if fields[0] == "__SIF_ID__":
                identity = fields[1:]
            elif fields[0] == "__SIF_META__":
                metadata.append(fields[1:])
            else:
                rows.append(fields)
        self.assertEqual(identity, [self.user, self.user, database, "on"])
        self.assertEqual(len(metadata), 2, f"expected metadata for both fixture tables: {metadata!r}")
        for table, is_super, bypass, createdb, createrole, inherit, owner, rls, forced in metadata:
            self.assertEqual((is_super, bypass, createdb, createrole, inherit), ("f", "f", "f", "f", "f"))
            self.assertEqual(owner, "sif_fixture_owner")
            if database.endswith("_baseline"):
                self.assertEqual((rls, forced), ("f", "f"), f"baseline RLS state for {table}")
            else:
                self.assertEqual((rls, forced), ("t", "t"), f"RLS state for {table}")
        return {
            "database": database,
            "identity": identity,
            "metadata": metadata,
            "rows": rows,
            "sql": sql,
            "psql_exit": completed.returncode,
            "stderr": completed.stderr,
        }

    def _assert_case_arms(self, case_id: str, unscoped_rows: list[list[str]]) -> None:
        case = CASES[case_id]
        frozen_sql = case["sql"]
        decision = guard_sql(frozen_sql, case["authenticated_tenant"])
        self.assertEqual(decision.status, "rewritten", decision.reason)
        self.assertIsNotNone(decision.sql)

        expected = expected_for(case, FIXTURE)["authorized"]
        expected_rows = [[str(value) for value in row] if isinstance(row, list) else [str(row)]
                         for row in expected] if isinstance(expected, list) else [[str(expected)]]

        observed = {
            "baseline_unmodified": self._run("sql_isolation_pilot_fixture_baseline", frozen_sql),
            "baseline_ast_rewritten": self._run("sql_isolation_pilot_fixture_baseline", decision.sql),
            "rls_unmodified": self._run("sql_isolation_pilot_fixture", frozen_sql),
        }
        self.assertEqual(observed["baseline_unmodified"]["rows"], unscoped_rows)
        self.assertEqual(observed["baseline_ast_rewritten"]["rows"], expected_rows)
        self.assertEqual(observed["rls_unmodified"]["rows"], expected_rows)
        print(json.dumps({
            "case": case_id,
            "frozen_sql": frozen_sql,
            "guard_decision": decision.status,
            "guard_sql": decision.sql,
            "expected_authorized_rows": expected_rows,
            "observed": observed,
        }, sort_keys=True))

    def test_c2_join_baseline_guard_and_rls(self) -> None:
        self._assert_case_arms(
            "C2",
            [["o_a1", "Ada"], ["o_a2", "Ari"], ["o_b1", "Bea"]],
        )

    def test_c4_aggregate_baseline_guard_and_rls(self) -> None:
        self._assert_case_arms("C4", [["10500"]])

    def test_c3_cte_baseline_guard_and_rls(self) -> None:
        self._assert_case_arms("C3", [["o_a1"], ["o_a2"], ["o_b1"]])

    def test_c6_conflicting_tenant_rejected_and_blocked_by_rls(self) -> None:
        case = CASES["C6"]
        decision = guard_sql(case["sql"], case["authenticated_tenant"])
        self.assertEqual(decision.status, "rejected")
        self.assertEqual(decision.reason, "explicit_conflicting_tenant")

        baseline = self._run("sql_isolation_pilot_fixture_baseline", case["sql"])
        rls = self._run("sql_isolation_pilot_fixture", case["sql"])
        self.assertEqual(baseline["rows"], [["o_b1"]])
        self.assertEqual(rls["rows"], case["expected"])
        print(json.dumps({
            "case": "C6",
            "frozen_sql": case["sql"],
            "guard_decision": decision.status,
            "guard_reason": decision.reason,
            "guarded_sql_executed": False,
            "expected_authorized_rows": case["expected"],
            "expected_forbidden_rows": case["forbidden"],
            "observed": {
                "baseline_unmodified": baseline,
                "rls_unmodified": rls,
            },
        }, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
