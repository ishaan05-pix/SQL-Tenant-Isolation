# Threat model

## Purpose

Show a limited defense-in-depth pattern for SQL generated or selected by an untrusted model: an application-side SQL AST guard and PostgreSQL row-level security. The demo uses synthetic tenant data only.

## Assets

- Rows labeled `tenant_a` or `tenant_b` in the frozen `orders` and `customers` fixture.
- Correct binding of a request's authenticated tenant to the guard argument and, in the database experiment, to the PostgreSQL login role.

## Trust boundaries and assumptions

- The SQL string is untrusted and may omit a tenant predicate or contain unsupported structure.
- `authenticated_tenant` is trusted only if the caller obtains it from authenticated application state. The guard itself accepts a string and does not authenticate it.
- The caller executes only the exact SQL returned by `guard_sql`; no database execution wrapper is implemented here.
- PostgreSQL runtime principals are assumed to be non-superusers, not table owners, and not granted `BYPASSRLS`. PostgreSQL documents that superusers and `BYPASSRLS` roles bypass RLS, and that table owners normally bypass unless `FORCE ROW LEVEL SECURITY` is enabled. See the [PostgreSQL 18 RLS documentation](https://www.postgresql.org/docs/18/ddl-rowsecurity.html).
- The captured C1 evidence records `sif_tenant_a` as the current and session user. It does not establish general connection-pool or transaction lifecycle safety.
- Expected results are computed from `cases.json` fixture rows in `oracle.py`; the oracle does not parse guard output or call the guard.

## Guarded SQL subset

One PostgreSQL-dialect `SELECT` over the unqualified `orders` and `customers` fixture relations. The checked behavior includes simple predicates, ordering, inner joins, nested SELECT/CTE scopes, and `SUM`. Each supported base relation is tenant-scoped using the caller-provided authenticated tenant. Unsupported relations, qualified relations, multi-statements, non-SELECT roots, data-changing nodes nested in a SELECT, `SELECT INTO`, row locks, unsupported functions, and unsupported join types are rejected.

This describes an implementation subset, not a formally verified grammar or a general assurance that every engine interpretation matches SQLGlot's AST.

## Out of scope

- User authentication, authorization policy design, key management, or trustworthiness of a caller-supplied tenant value.
- Connection pooling, tenant context reset, concurrent transaction behavior, or real application request handling.
- Writes, stored procedures, views, database functions, system catalogs, arbitrary schemas, or non-PostgreSQL dialects.
- Side channels, inference from allowed aggregates, resource exhaustion, query cost, output rendering, or prompt injection.
- Production hardening, complete SQL safety, arbitrary schema security, or general tenant-isolation proof.

## Security claim boundary

The C1 database result is one observed synthetic fixture case. Static unit tests validate only the tested code paths. Neither establishes that the application is secure or that the guard or RLS policy is correct for other SQL statements or environments.
