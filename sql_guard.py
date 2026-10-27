"""Narrow, fail-closed AST guard for the frozen Gate 4 workload.

This is not a general SQL firewall. It supports single SELECT statements over
the local orders/customers fixture, inner joins, CTEs, and SUM. Database
execution is deliberately separate from this module.
"""

from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError
from sqlglot.optimizer.scope import traverse_scope


TENANT_TABLES = {"orders", "customers"}
ALLOWED_FUNCTIONS = {"SUM"}


@dataclass(frozen=True)
class GuardDecision:
    status: str
    reason: str
    sql: str | None = None
    tenant_relations_scoped: tuple[str, ...] = ()


def _reject(reason: str) -> GuardDecision:
    return GuardDecision(status="rejected", reason=reason)


def _function_name(node: exp.Func) -> str:
    return node.sql_name().upper()


def _explicit_conflict(tree: exp.Expression, tenant: str) -> bool:
    for predicate in tree.find_all(exp.EQ):
        left, right = predicate.this, predicate.expression
        for column, value in ((left, right), (right, left)):
            if (
                isinstance(column, exp.Column)
                and column.name.lower() == "tenant_id"
                and isinstance(value, exp.Literal)
                and value.is_string
                and str(value.this).casefold() != tenant.casefold()
            ):
                return True
    return False


def guard_sql(sql: str, authenticated_tenant: str) -> GuardDecision:
    """Return a rewritten query or a reasoned fail-closed rejection."""
    if authenticated_tenant not in {"tenant_a", "tenant_b"}:
        return _reject("unknown_authenticated_tenant")

    try:
        trees = sqlglot.parse(sql, read="postgres")
    except ParseError:
        return _reject("parse_failure")

    if len(trees) != 1:
        return _reject("multiple_statements")
    tree = trees[0]
    if not isinstance(tree, exp.Select):
        return _reject("non_read_only_or_unsupported_statement")

    # A SELECT root can still contain writes in a data-modifying CTE, request
    # SELECT INTO, or acquire row locks. Reject those nodes across the full AST.
    forbidden_statement_nodes = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Merge,
        exp.Create,
        exp.Drop,
        exp.Alter,
        exp.TruncateTable,
    )
    if any(tree.find(node_type) is not None for node_type in forbidden_statement_nodes):
        return _reject("non_read_only_or_unsupported_statement")
    if tree.find(exp.Into) is not None or tree.find(exp.Lock) is not None:
        return _reject("non_read_only_or_unsupported_statement")

    if _explicit_conflict(tree, authenticated_tenant):
        return _reject("explicit_conflicting_tenant")

    # Keep the tested SQL surface intentionally small. This prevents functions
    # such as set_config or arbitrary UDFs from changing session identity/state.
    for function in tree.find_all(exp.Func):
        # In SQLGlot, logical operators are Func subclasses too, but are not
        # callable SQL functions and are required by the supported predicates.
        if isinstance(function, (exp.And, exp.Or, exp.Not)):
            continue
        if _function_name(function) not in ALLOWED_FUNCTIONS:
            return _reject("unsupported_function")

    # Resolve CTE and derived-table references lexically. A global set of CTE
    # names can otherwise make a same-named physical table look allowlisted.
    tables = [
        node
        for scope in traverse_scope(tree)
        for node, source in scope.selected_sources.values()
        if isinstance(source, exp.Table)
    ]
    relation_names = [table.name.casefold() for table in tables]
    if not tables:
        return _reject("no_supported_relation")
    for name in relation_names:
        if name not in TENANT_TABLES:
            return _reject("unsupported_or_ambiguous_relation")
    for table in tables:
        if table.name.casefold() in TENANT_TABLES and (table.db or table.catalog):
            # This guard is configured for the unqualified fixture relations;
            # accepting another schema with a same-named table would exceed
            # the relation allowlist's verified meaning.
            return _reject("unsupported_or_ambiguous_relation")

    # Moving filters from an outer join's ON clause to WHERE changes meaning;
    # reject outer, natural, and cross joins until a dedicated rewrite exists.
    for join in tree.find_all(exp.Join):
        kind = join.args.get("kind")
        if (
            join.args.get("side")
            or (kind and str(kind).upper() != "INNER")
            or join.args.get("method")
            or not (join.args.get("on") or join.args.get("using"))
        ):
            return _reject("unsupported_join_type")

    scoped: list[str] = []
    for table in tables:
        name = table.name.casefold()
        if name not in TENANT_TABLES:
            continue  # CTE reference; its underlying tenant table is filtered.
        select = table.find_ancestor(exp.Select)
        if select is None:
            return _reject("ambiguous_relation_scope")
        alias = table.alias_or_name
        tenant_column = exp.column("tenant_id", table=alias)
        tenant_predicate = exp.EQ(
            this=tenant_column,
            expression=exp.Literal.string(authenticated_tenant),
        )
        where = select.args.get("where")
        if where is None:
            select.set("where", exp.Where(this=tenant_predicate))
        else:
            select.set("where", exp.Where(this=exp.and_(where.this, tenant_predicate)))
        scoped.append(alias)

    return GuardDecision(
        status="rewritten",
        reason="tenant_scope_injected_for_each_supported_relation",
        sql=tree.sql(dialect="postgres"),
        tenant_relations_scoped=tuple(scoped),
    )
