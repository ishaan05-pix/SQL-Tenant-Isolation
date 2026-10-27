"""Independent expected-result oracle over the frozen fixture manifest.

The oracle does not parse SQL and never calls the AST guard or a DB policy.
It computes the expected values for the named workload cases from fixture rows.
"""

from __future__ import annotations

from typing import Any


def expected_for(case: dict[str, Any], fixture: dict[str, Any]) -> dict[str, Any]:
    tenant = case.get("authenticated_tenant")
    if case["id"] == "C7":
        return {
            "tenant_a": _open_order_ids(fixture, "tenant_a"),
            "tenant_b": _open_order_ids(fixture, "tenant_b"),
        }
    if case["id"] == "C6":
        return {"authorized": [], "forbidden": ["o_b1"]}
    if case["id"] == "C2":
        customers = {row["customer_id"]: row for row in fixture["customers"]}
        rows = [
            [order["order_id"], customers[order["customer_id"]]["name"]]
            for order in fixture["orders"]
            if order["tenant_id"] == tenant
            and order["status"] == "open"
            and order["customer_id"] in customers
            and customers[order["customer_id"]]["tenant_id"] == tenant
        ]
        return {"authorized": sorted(rows), "forbidden": [["o_b1", "Bea"]]}
    if case["id"] in {"C1", "C3", "C5"}:
        return {
            "authorized": _open_order_ids(fixture, tenant),
            "forbidden": _open_order_ids(fixture, "tenant_b" if tenant == "tenant_a" else "tenant_a"),
        }
    if case["id"] == "C4":
        sums = {
            name: sum(
                row["amount_cents"]
                for row in fixture["orders"]
                if row["tenant_id"] == name and row["status"] == "open"
            )
            for name in {"tenant_a", "tenant_b"}
        }
        return {
            "authorized": sums[tenant],
            "forbidden_contribution": sums["tenant_b" if tenant == "tenant_a" else "tenant_a"],
            "unscoped": sum(sums.values()),
        }
    raise ValueError(f"No independent oracle defined for {case['id']}")


def _open_order_ids(fixture: dict[str, Any], tenant: str) -> list[str]:
    return sorted(
        row["order_id"]
        for row in fixture["orders"]
        if row["tenant_id"] == tenant and row["status"] == "open"
    )
