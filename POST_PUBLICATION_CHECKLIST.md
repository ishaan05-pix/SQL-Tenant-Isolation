# Post-publication checklist

**State inspected:** 2026-10-27. The repository is public at [ishaan05-pix/SQL-Tenant-Isolation](https://github.com/ishaan05-pix/SQL-Tenant-Isolation). The local `main` branch tracks `origin/main`; the tree was clean at the time of this checklist snapshot. The project remains unlicensed at the owner’s direction.

## Published contents and evidence status

The repository includes the following material:

- Source: `sql_guard.py`, `oracle.py`, `identity.py`, `pilot.py`.
- Frozen workload and dependency declaration: `cases.json`, `requirements.txt`.
- Tests: `tests/test_sql_guard.py` and `tests/test_postgres_readonly.py`.
- CI: `.github/workflows/static-tests.yml` runs the 12-test static suite on Python 3.10 and 3.12; it does not connect to PostgreSQL or run the four integration tests.
- Documentation: `README.md`, `DEMO_WALKTHROUGH.md`, `RESEARCH_BACKGROUND.md`, `FUTURE_WORK.md`, `THREAT_MODEL.md`, `COMPETITOR_REVIEW.md`, `PROJECT_DECISION.md`, `IMPLEMENTATION_REPORT.md`, `FINAL_AUDIT.md`, and this checklist.
- Results: `results/c1_database_evidence.json` (historical C1), `results/c2_c4_database_evidence.json`, `results/c3_c6_database_evidence.json`, and `results/stage_a_preflight.json` (older static snapshot). Preserve the existing C1 and preflight records.
- Vendored dependency: `.vendor/` (154 files, about 4.32 MiB), including `.vendor/sqlglot-26.16.4.dist-info/licenses/LICENSE`. Preserve SQLGlot’s third-party MIT license. `requirements.txt` pins SQLGlot 26.16.4 for normal installation.
- `.gitignore`.

Do not include local `.venv/`, Python bytecode/cache directories, credentials/password files, local `.env` files, or an unreviewed generated `results/local_preflight.json`. The `.gitignore` covers the expected local environment and bytecode paths without ignoring either existing result record.

## License decision

The owner has chosen to leave the project unlicensed for now. Do not infer a project license from SQLGlot’s MIT license or from the cited papers’ licenses. A public repository without a project license grants no general reuse rights. Preserve SQLGlot’s MIT copyright/license text when distributing `.vendor`.

## Current evidence and follow-up

- C1 remains in its original historical record. Its old statement that only C1 had been executed describes that record’s time scope.
- C2, C3, C4, and C6 have separate read-only PostgreSQL observation files. C5 and C7 remain untested against PostgreSQL.
- The 12 static tests are separate from the four PostgreSQL integration tests. GitHub Actions runs only the static tests.
- These selected cases do not establish a general security guarantee, production readiness, or research novelty.
- `results/stage_a_preflight.json` is an earlier static snapshot. Its blocked/preflight status predates the PostgreSQL observations and has not been rewritten.
- Before making future public changes, review the diff and rerun the safe static suite. Any database revalidation remains an explicit local opt-in and is not part of CI.

## License and distribution

The owner chose to leave the project unlicensed. A public repository without a project license grants no general reuse rights. Preserve SQLGlot’s MIT license in `.vendor`; it does not license this project’s original code or documentation.
