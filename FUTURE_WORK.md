# Proposed future work

**Status: proposal only. None of the architecture, application integration, or evaluation below is implemented or validated by this repository.** Do not interpret this document as a deployment plan already in effect.

## Proposed enforcement architecture

1. **Database-enforced row access as the primary control.** Enable and force RLS on every tenant-owned table. Write table-specific policies that bind rows to authenticated tenant identity. Runtime roles should be least-privileged, non-superuser, not table owners, and `NOBYPASSRLS`; schema ownership/migrations should use separate principals. Verify actual role attributes, table ownership, policy definitions, grants, and RLS flags from PostgreSQL catalogs. RLS would need negative tests for role/policy/table misconfiguration, because the presence of a policy in source is not sufficient evidence.
2. **Trusted identity propagation.** Authenticate the user at the server boundary and derive tenant identity there. Do not accept tenant identity from model-generated SQL or prompt text. Bind each request to a tenant-specific database principal or to a carefully designed server-controlled transaction context. A mutable SQL-controlled setting must not be treated as a security boundary. Verify `current_user`, `session_user`, and tenant mapping at execution boundaries.
3. **AST checks as defense in depth.** Keep the parser guard before execution to reject unsupported or conflicting SQL and optionally inject a predicate for the documented subset. Execute only the exact returned SQL. A guard rejection should be reported separately as a security outcome and a utility failure. Database policy remains the row-access boundary if the guard misses a query shape.
4. **Pool and transaction isolation.** Ensure connections cannot cross tenant identity. Test identity transitions A→B→A, successful commit, rollback, statement error, cancellation, timeout, connection return, and reuse. If identity is set per transaction, use transaction-scoped state, roll back on failure, and verify reset/checkout behavior using real pooled connections. Reject checkout on a principal mismatch.
5. **Auditability and resource controls.** Record request/tenant identifiers, policy decisions, guard decisions, executed SQL fingerprint, database principal, duration, row count, and errors without logging secrets or sensitive result contents. Apply database statement timeouts, query-cost or row/byte limits where supported, and per-tenant concurrency/quotas.

## Proposed adversarial evaluation

Preserve the frozen C1–C7 cases. Additive cases, if justified, should be versioned separately and should cover:

- Direct reads with missing, correct, conflicting, tautological, or obfuscated tenant predicates.
- Aliased joins where both sides own tenant rows, including supported `ON`/`USING` shapes and explicit rejection of unsupported outer, natural, or cross joins.
- CTEs, nested subqueries, derived tables, recursive CTEs, shadowing/colliding relation names, and schema-qualified relations.
- Aggregates, grouped aggregates, counts, and differencing/query sequences that could reveal cross-tenant facts.
- Unsupported functions, system/catalog relations, multiple statements, write statements, data-modifying CTEs, `SELECT INTO`, locks, parser errors, and hostile/pathological input sizes.
- Identity transitions and context changes across commit, rollback, error, pool checkout, and reused physical connections.
- Deliberate policy/configuration defects such as missing RLS, missing `FORCE`, owner execution, `BYPASSRLS`, broad grants, and wrong tenant mapping. Each negative test should prove the faulty setup is detected.
- Prompt/model-generated SQL only in a separate generation stage, with frozen outputs and no paid model dependency unless separately approved. A fixed-SQL replay does not measure prompt effectiveness.

## Independent ground truth and metrics

Derive expected rows and aggregate results from a fixture manifest or a separately authored reference query that does not call the guard or reuse its rewrite. Preserve raw query output, errors, principal/database identity, policy state, and exit status before comparing to expected results.

Report, rather than combine into one score:

- Unauthorized-row exposure and forbidden-case leak rate.
- Authorized-task completion and false-block rate.
- Query rejection rate, separated into security-pass and utility-failure accounting.
- Identity-isolation failures and pool reset failures.
- Latency and resource use by arm, with repeated runs and environment details.

Run identical frozen SQL across enforcement arms only when the SQL semantics are comparable. Prompt-generation evaluation must remain separate: compare generated SQL from different prompts, freeze each generated output, then pass each through the same enforcement test matrix.

## LLM data-agent considerations

If this becomes an LLM data-agent system, authorization must cover more than one SQL statement. A future system should authorize each tool invocation server-side, propagate tenant identity to tools, isolate conversation state, enforce per-tenant query and tool budgets, and audit tool decisions. It should also assess cumulative disclosure: individually permitted aggregates can reveal a protected value when combined across turns. Tests should include untrusted database content and prompt injection, but must distinguish those agent threats from SQL row-filtering tests.

These are proposal items only. The current pilot has no agent, authentication provider, server-side tool authorization, pool manager, cost controls, audit pipeline, or multi-query disclosure defense.
