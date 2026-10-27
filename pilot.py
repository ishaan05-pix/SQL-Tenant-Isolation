"""Static preflight runner; does not claim database enforcement results."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from identity import IdentityBindingError, TenantPoolBindings
from oracle import expected_for
from sql_guard import guard_sql


ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(ROOT / "results" / "stage_a_preflight.json"),
        help="JSON output path for static guard decisions and environment status",
    )
    args = parser.parse_args()

    document = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    postgres_client = shutil.which("psql")
    identity_bindings = TenantPoolBindings(
        {"tenant_a": "app_tenant_a", "tenant_b": "app_tenant_b"}
    )
    rows = []
    for case in document["cases"]:
        oracle_result = expected_for(case, document["schema"])
        if "authenticated_tenants" in case:
            tenants = case["authenticated_tenants"]
        else:
            tenants = [case["authenticated_tenant"]]
        arm_results = []
        for tenant in tenants:
            decision = guard_sql(case["sql"], tenant)
            arm_results.append(
                {
                    "authenticated_tenant": tenant,
                    "no_enforcement": {
                        "status": "not_executed",
                        "reason": "postgresql_unavailable",
                    },
                    "ast_guard": {
                        "decision": decision.status,
                        "reason": decision.reason,
                        "rewritten_sql": decision.sql,
                        "tenant_relations_scoped": list(decision.tenant_relations_scoped),
                        "database_execution": "not_executed",
                    },
                    "postgresql_rls": {
                        "status": "blocked_environment" if not postgres_client else "not_configured",
                        "reason": "postgresql_client_or_server_not_available_in_checked_environment",
                    },
                    "identity_binding_preflight": {
                        "status": "configuration_validated",
                        "pool_key": identity_bindings.pool_key(tenant),
                        "request_principal_match": "configuration_only_not_database_verified",
                    },
                }
            )
        mismatch_control = "not_run"
        if case["id"] == "C7":
            try:
                identity_bindings.assert_checkout("tenant_b", "app_tenant_a")
            except IdentityBindingError as error:
                mismatch_control = f"detected:{error}"
        rows.append(
            {
                "case_id": case["id"],
                "name": case["name"],
                "sql": case["sql"],
                "expected": case.get("expected", case.get("expected_by_tenant")),
                "forbidden": case.get("forbidden", case.get("forbidden_contribution")),
                "kind": case["kind"],
                "independent_oracle": {
                    "status": "computed_from_fixture_manifest",
                    "expected": oracle_result,
                },
                "identity_failure_injection": mismatch_control,
                "arm_runs": arm_results,
            }
        )

    result = {
        "experiment": "sql_tenant_isolation_stage_a",
        "result_type": "static_preflight_not_database_experiment",
        "status": "blocked_for_database_execution" if not postgres_client else "database_unconfigured",
        "postgres_client_found": bool(postgres_client),
        "validity_controls": {
            "negative_control_leak": "not_tested_database_execution_blocked",
            "rls_authorized_positive": "not_tested",
            "identity_mismatch_detection": "configuration_mapping_tested_database_binding_not_tested",
            "removed_policy_detection": "not_tested",
        },
        "cases": rows,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(output), "cases": len(rows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
