# First-public-release checklist

**State inspected:** 2026-10-27. The local repository is on `main` with a clean working tree and local commits. No remote is configured, and nothing has been pushed or published. The project remains unlicensed at the owner’s direction.

## Current repository contents

The local commits include the following material. Review the complete staged/committed tree again before publishing:

- Source: `sql_guard.py`, `oracle.py`, `identity.py`, `pilot.py`.
- Frozen workload and dependency declaration: `cases.json`, `requirements.txt`.
- Tests: `tests/test_sql_guard.py` and `tests/test_postgres_readonly.py`.
- CI: `.github/workflows/static-tests.yml` runs the 12-test static suite on Python 3.10 and 3.12; it does not connect to PostgreSQL.
- Documentation: `README.md`, `DEMO_WALKTHROUGH.md`, `RESEARCH_BACKGROUND.md`, `FUTURE_WORK.md`, `THREAT_MODEL.md`, `COMPETITOR_REVIEW.md`, `PROJECT_DECISION.md`, `IMPLEMENTATION_REPORT.md`, `FINAL_AUDIT.md`, and this checklist.
- Results: `results/c1_database_evidence.json` (historical C1), `results/c2_c4_database_evidence.json`, `results/c3_c6_database_evidence.json`, and `results/stage_a_preflight.json` (older static snapshot). Preserve the existing C1 and preflight records.
- Vendored dependency: `.vendor/` (154 files, about 4.32 MiB), including `.vendor/sqlglot-26.16.4.dist-info/licenses/LICENSE`. Preserve SQLGlot’s third-party MIT license. `requirements.txt` pins SQLGlot 26.16.4 for normal installation.
- `.gitignore`.

Do not include local `.venv/`, Python bytecode/cache directories, credentials/password files, local `.env` files, or an unreviewed generated `results/local_preflight.json`. The `.gitignore` covers the expected local environment and bytecode paths without ignoring either existing result record.

## License decision

The owner has chosen to leave the project unlicensed for now. Do not infer a project license from SQLGlot’s MIT license or from the cited papers’ licenses. A public repository without a project license grants no general reuse rights. Preserve SQLGlot’s MIT copyright/license text when distributing `.vendor`.

## Before publishing

1. Review every staged file and `.gitignore`; verify that `.vendor` inclusion is intentional and its license is present.
2. Run the documented static tests from a clean virtual environment or confirm the pinned dependency installation path. Do not treat those tests as PostgreSQL results.
3. Recheck public-facing files for credentials, private machine paths, and unsupported claims. Keep C1 labeled historical; describe C2, C3, C4, and C6 as bounded read-only observations; identify C5 and C7 as untested against PostgreSQL.
4. Confirm that leaving the project unlicensed is intentional for the selected audience and repository visibility. Do not copy a dependency or paper license as the project license.
5. Choose a remote repository and its visibility. Obtain explicit approval before creating a public GitHub repository or pushing any commit.

This checklist does not configure a remote or push the project.
