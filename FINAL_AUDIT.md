# Final quality and reproducibility audit

**Date:** 2026-10-27  
**Scope:** static code, tests, documentation, and stored evidence only. No PostgreSQL connection or query was made during this audit.

> **Historical snapshot:** This audit describes the repository before local Git initialization and before the later C2, C3, C4, and C6 PostgreSQL checks. The current test/evidence status is recorded in `README.md`, the latest dated addenda in `IMPLEMENTATION_REPORT.md`, and `results/c2_c4_database_evidence.json` plus `results/c3_c6_database_evidence.json`. The findings below are retained as they were at the time of this audit.

## Test commands and outcomes

The README command was attempted from the project directory with `.vendor` on `PYTHONPATH`:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) '.vendor')
$env:PYTHONDONTWRITEBYTECODE = '1'
python -m unittest discover -s tests -v
```

**Exit status: 1; no tests ran.** In this environment, `python` resolves to an inaccessible Windows App Execution Alias.

The equivalent command using the available bundled Python 3.12.14 runtime completed:

```powershell
$py = '<path to an available Python 3.10+ executable>'
$env:PYTHONPATH = (Join-Path (Get-Location) '.vendor')
$env:PYTHONDONTWRITEBYTECODE = '1'
& $py -m unittest discover -s tests -v
```

**Exit status: 0; 12 tests ran and passed in 0.030 seconds.** The runtime path is intentionally omitted because it is a local user-profile path. Tests are static Python checks for parsing/rewrite/rejection, oracle outputs, and the pure identity mapping helper. They do not execute database SQL.

The documented `pilot.py --help` command completed with exit status 0. The full preflight was not run because it writes a JSON output and its default target is the existing historical `results/stage_a_preflight.json`.

## Security review

### High — CTE-name relation allowlist bypass, corrected

Before correction, the guard built a global set of CTE names and accepted any table occurrence with one of those names. The reproducible input

```sql
WITH payments AS (SELECT order_id FROM payments)
SELECT order_id FROM payments;
```

was returned as `rewritten` with `tenant_relations_scoped=()`. A same-named physical relation inside the CTE definition could therefore evade the `orders`/`customers` relation allowlist and receive no tenant predicate if that relation existed and was readable. A forward CTE-name collision had the same classification problem.

The guard now uses SQLGlot scope resolution and validates physical table sources, so CTE references are distinguished from underlying relations. Regression coverage checks both self-name and forward-name collisions; both now reject as `unsupported_or_ambiguous_relation`. No database execution was used to establish this static parser result.

### Medium — join-subset mismatch, corrected

The guard rejected explicit `INNER JOIN` even though the README described inner joins as supported, because SQLGlot records `kind="INNER"`. Conversely, it accepted `NATURAL JOIN` and comma-style cross joins, which were outside the documented subset. The guard now permits inner joins with `ON` or `USING`, and rejects outer, natural, cross, and comma-style joins. Regression tests cover these decisions.

### Reviewed controls

- Nested `INSERT`, `UPDATE`, `DELETE`, `MERGE`, DDL, and `TRUNCATE` nodes are checked across the AST; `SELECT INTO` and row locks are explicitly rejected.
- Multiple statements and non-SELECT roots reject. Unknown physical relations, schema-qualified fixture relations, and unsupported functions reject.
- Alias predicates are generated against the alias; each physical relation in the tested inner join is scoped. CTE and derived-table references are resolved through SQLGlot scopes, and the underlying fixture table is scoped.
- Outer joins reject because moving tenant restrictions to `WHERE` can change their semantics.
- The independent oracle reads fixture rows and does not call the guard. `identity.py` validates only a static mapping; it does not test a real pool or database principal lifecycle.

These are checks over the tested subset, not an exhaustive SQL security review. The guard accepts `SELECT *` over allowlisted relations and does not enforce column-level minimization, query-cost limits, or an execution timeout. Unqualified relation names rely on the caller's database resolution environment and trusted `search_path`; the guard has no execution wrapper to pin that environment. These are residual limitations, not claims that the C1 result exercises them.

## Documentation and evidence consistency

- The README correctly separates static unit tests from the stored PostgreSQL C1 observation and says C2–C7 remain untested.
- `IMPLEMENTATION_REPORT.md` preserves its earlier 10-test snapshot and now has an audit addendum recording the 12-test result and two corrections. The prior user-profile runtime path was replaced with a generic executable placeholder.
- The C1 evidence record contains three role-identified successful runs: baseline rows `o_a1`, `o_a2`, `o_b1`; guarded baseline rows `o_a1`, `o_a2`; RLS rows `o_a1`, `o_a2`. The stored expected/observed comparisons agree. This audit did not rerun or independently authenticate those historical executions.
- `results/stage_a_preflight.json` is an earlier static snapshot that says database execution was blocked. It predates the C1 PostgreSQL record; it must not be read as current database status.
- The competitor review labels third-party implementation/test behavior as README/documentation claims where code pages were unavailable. The portfolio-demo decision and threat model avoid a novelty or general-security claim.
- All three project JSON files (`cases.json` and both files in `results/`) parsed successfully without being rewritten.

## Reproducibility and privacy

- `requirements.txt` pins only `sqlglot==26.16.4`; `.vendor` currently contains SQLGlot and allows the suite to run without installation. A fresh delivery must include `.vendor` or install the pinned requirement in an isolated Python 3.10+ environment. This directory is not a Git repository, so this audit cannot establish whether `.vendor` is tracked or will be present in a clean clone.
- The README's `python` command fails in this Windows environment because the app execution alias cannot start. Use a working Python executable and set `PYTHONPATH` to `.vendor`. No package was installed.
- `pilot.py` defaults to overwriting the historical static preflight JSON; use a new output path if running it. Its `psql` discovery only checks `PATH` and is not a database connectivity test.
- A local credential-pattern scan found no likely hard-coded secret values outside the vendored dependency. A user-profile path in the implementation report was removed. The C1 evidence still records the PostgreSQL client under `Program Files` as historical execution metadata; that is machine-specific but contains no user-profile or credential value.
- Git status/diff was unavailable because the project had not yet been initialized as a Git repository. The inspected change set at that audit point was limited to `sql_guard.py`, `tests/test_sql_guard.py`, `IMPLEMENTATION_REPORT.md`, and this report.

## Changes made

- Updated relation validation to distinguish physical relations from CTE references, closing the reproduced CTE-name allowlist bypass.
- Corrected join handling to match the stated supported subset and added regression tests for explicit inner, outer, natural, cross, and comma joins.
- Appended the test and correction results to `IMPLEMENTATION_REPORT.md`, preserving its earlier status snapshot while omitting the machine-specific user-profile path.
- Added this audit report. Frozen cases, oracle, identity helper, C1 evidence, and both existing JSON records were not modified.

## Residual risks and untested behavior

- No PostgreSQL queries were run in this audit. The only stored database evidence is the prior C1 case; C2–C7, connection pooling, tenant reset, and policy misconfiguration remain untested.
- SQLGlot parsing and rewriting are not proven equivalent to PostgreSQL for all syntax. Malformed/pathological SQL, alternate schemas/search paths, views, functions, column-level data access, aggregates beyond the frozen SUM case, resource exhaustion, and side channels remain outside the tests.
- There is no application authentication or query execution layer that guarantees the tenant argument is trusted or that only the returned SQL is executed.
- The source tree lacks Git metadata, so a clean-checkout/diff audit and dependency-vendoring status cannot be confirmed here.

## Recommendation

**Ready with caveats** as a small portfolio demo of the tested static guard paths and the previously recorded single-case C1 PostgreSQL observation. Do not present it as a general SQL security control, production-ready system, benchmark, or novel research result.

## Reviewer commands

From the project directory in PowerShell, with `$py` set to a working Python 3.10+ executable:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) '.vendor')
$env:PYTHONDONTWRITEBYTECODE = '1'
& $py -m unittest discover -s tests -v
```

Optional isolated dependency setup if `.vendor` is absent (not run during this audit):

```powershell
& $py -m pip install -r requirements.txt
```

Optional static preflight, using a new output filename (not run during this audit):

```powershell
& $py pilot.py --output results/local_preflight.json
```

The preflight writes a static JSON report; it does not execute PostgreSQL queries.
