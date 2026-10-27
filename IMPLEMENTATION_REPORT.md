# Implementation and evidence report

**Updated:** 2026-10-27  
**Scope:** conservative portfolio-demo hardening and evidence inventory.

> **Current status:** The initial sections below preserve earlier snapshots. Later addenda document subsequent work. The current read-only PostgreSQL suite covers C2, C3, C4, and C6; C1 remains a separate historical record, while C5 and C7 remain untested against PostgreSQL. There are 12 static unit tests and four opt-in database integration tests. GitHub Actions runs only the static suite. See the README and the two newer result JSON files for the present evidence summary.

> The prior conversation refers to an implementation report, but no `IMPLEMENTATION_REPORT.md` was present in the inspected checkout. This is a new status report; it does not replace or rewrite a historical file. Existing `results/` records are retained.

## Initial implementation snapshot (historical)

### Implemented in this checkout

- A narrow SQLGlot AST guard for the frozen PostgreSQL query subset in `sql_guard.py`.
- Full-tree rejection for data-changing statement nodes inside a `SELECT`, plus explicit rejection for `SELECT INTO` and row locks.
- Rejection of schema-qualified `orders` and `customers`, because the verified tenant relation allowlist is limited to the unqualified fixture relations.
- Regression tests for those rejection conditions in `tests/test_sql_guard.py`.
- An independent fixture-based expected-result computation in `oracle.py`; it does not invoke or parse the guard.
- Static tenant-to-principal mapping validation in `identity.py`; this is not a database connection or pool test.

### PostgreSQL evidence already recorded

The existing record [`results/c1_database_evidence.json`](results/c1_database_evidence.json) records one frozen C1 run set as `sif_tenant_a`:

| Arm | Database | Observed C1 rows | Exit status |
|---|---|---|---:|
| Baseline, no tenant enforcement | `sql_isolation_pilot_fixture_baseline` | `o_a1`, `o_a2`, `o_b1` | 0 |
| AST-guarded SQL on baseline | `sql_isolation_pilot_fixture_baseline` | `o_a1`, `o_a2` | 0 |
| Unchanged SQL under RLS | `sql_isolation_pilot_fixture` | `o_a1`, `o_a2` | 0 |

The record includes the frozen input, exact SQL returned by the guard, identity preflights, captured command output, and oracle comparison. These observations were not rerun during this update. C2–C7 remain untested against PostgreSQL. This single-case fixture result is not a general security guarantee, production validation, or novelty claim.

## Static tests run for this update

Successful command, from the project root:

```powershell
$py = '<path to a Python 3.10+ executable>'
$env:PYTHONPATH = (Join-Path (Get-Location) '.vendor')
$env:PYTHONDONTWRITEBYTECODE = '1'
& $py -m unittest discover -s tests -v
```

The successful local run used a bundled Python runtime; its user-profile path is omitted from this report.

**Observed:** 10 tests ran in 0.029 seconds; all passed. They test Python parsing/rewriting/rejection decisions, fixture-oracle outputs, and static principal mapping. They do not execute SQL on PostgreSQL.

An initial attempt to invoke `python -m unittest ...` through the Windows App Execution Alias failed to start `python.exe`; no tests ran in that invocation. The bundled runtime command above succeeded.

## Not run in this update

- `pilot.py` was not run because its default output overwrites the existing historical `results/stage_a_preflight.json`.
- No PostgreSQL query was run; the recorded C1 evidence was not refreshed.
- No dependency installation, database mutation, role/policy change, or external service call was made.

## Untested and unverified

- Frozen cases C2–C7 against PostgreSQL, including joins, CTEs, aggregate leakage, explicit conflict behavior under RLS, and connection reuse.
- Real application authentication, query execution wrapper, connection pooling, tenant lifecycle, rollback/reset behavior, and concurrent requests.
- General SQLGlot/PostgreSQL equivalence, other schemas, views, functions, writes, query cost, side channels, and arbitrary query shapes.
- A general security guarantee or research novelty claim.

## Reproduction

From the project directory, run the successful PowerShell unit-test command above. The optional static preflight can be run as `python pilot.py --output results/local_preflight.json` in an environment with the dependency available; choose a fresh output path to preserve existing records. That command is static and is not a database experiment.

## Final audit addendum (2026-10-27)

- Review found that a CTE name could make a same-named physical relation appear allowlisted. The guard now validates resolved physical table sources with SQLGlot scope traversal; regression tests cover self-name and forward-name collisions.
- Review found explicit `INNER JOIN` was rejected despite the documented subset, while `NATURAL JOIN` and comma cross joins were accepted. The guard now accepts supported inner joins with `ON` or `USING` and rejects those unsupported shapes.
- The final static suite ran 12 tests and passed. It remained a Python-only test; no PostgreSQL query was run.
- The README test command assumes `python` resolves to a usable Python 3 executable. In this environment the Windows App Execution Alias could not start, so the suite was run with the bundled interpreter. No dependencies were installed.
- No C1 evidence, frozen case, fixture, or database object was changed or rerun.

## Read-only PostgreSQL integration addendum (2026-10-27)

The earlier audit addendum above records the state at that time. Since then, the opt-in read-only suite was run for frozen C2 and C4; the historical C1 record and fixture/database configuration were not modified.

- Preflight connected as `sif_tenant_a` to both `sql_isolation_pilot_fixture_baseline` and `sql_isolation_pilot_fixture`; `current_user` and `session_user` were both `sif_tenant_a`, and `transaction_read_only` was `on`.
- C2 baseline returned `o_a1/Ada`, `o_a2/Ari`, and forbidden `o_b1/Bea`. The exact guard rewrite and unchanged RLS query each returned only `o_a1/Ada` and `o_a2/Ari`.
- C4 baseline returned `10500`; the exact guard rewrite and unchanged RLS query each returned `1500`.
- Both tests passed with exit status 0. The role was observed as non-superuser, non-`BYPASSRLS`, non-owner; baseline tables had RLS disabled, and both RLS tables had RLS enabled and forced.
- Detailed results are in [`results/c2_c4_database_evidence.json`](results/c2_c4_database_evidence.json). No separate raw psql stdout transcript was preserved; the test captured parsed rows, identity, metadata, exit status, and stderr.
- C3 and C5–C7 remain untested against PostgreSQL. These C2/C4 observations do not prove general security or production readiness.

## Additional read-only PostgreSQL integration addendum (2026-10-27)

- The opt-in suite was run again after adding frozen C3 and C6. All four included tests (C2, C3, C4, C6) passed with suite exit status 0.
- C3 baseline returned `o_a1`, `o_a2`, `o_b1`; the exact AST rewrite and unchanged RLS query returned `o_a1`, `o_a2`.
- C6 baseline returned forbidden `o_b1`. The guard rejected the SQL with `explicit_conflicting_tenant`; no guarded SQL was executed. Unchanged SQL under RLS returned no rows.
- C2 and C4 passed again with the previously recorded outcomes. Detailed C3/C6 observations are in [`results/c3_c6_database_evidence.json`](results/c3_c6_database_evidence.json).
- C5 and C7 remain untested against PostgreSQL. No general security or production-readiness conclusion follows.
