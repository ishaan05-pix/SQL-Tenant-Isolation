# Competitor and source review

**Reviewed:** 2026-10-27. This is a documentation and source-page review, not an independent evaluation of the third-party projects.

> **Project-evidence time scope:** The pilot-status statements in this review describe the earlier C1-only evidence state. Later same-date read-only PostgreSQL observations for C2, C3, C4, and C6 are recorded separately in the result files and do not change the competitor-source findings or establish a research gap. C5 and C7 remain untested against PostgreSQL.

## Approaches compared

| Approach | What the inspected source supports | Limits of this review |
|---|---|---|
| This pilot's AST rewrite | `sql_guard.py` parses one PostgreSQL statement with SQLGlot, limits relations/functions, detects a simple explicit tenant conflict, and injects tenant predicates into supported relation scopes. Its C1 SQL was actually executed in three PostgreSQL arms; see `results/c1_database_evidence.json`. | Only C1 has PostgreSQL execution evidence. The guard is not a general SQL firewall. The local test suite does not execute database SQL. |
| `darrshangovender/sql-guardrails` | The [project README](https://github.com/darrshangovender/sql-guardrails) describes SQLGlot parsing, single-statement/read-only checks, full-tree rejection of writes (including data-modifying CTEs), table/function allowlists, optional EXPLAIN limits, and a read-only executor. Its limitations table explicitly says cross-tenant reads are not its goal and recommends RLS for row visibility. | The README and repository file listing were accessible. Individual implementation and test files could not be fetched in this review, so these capabilities are **README claims**, not independently source-verified or executed here. |
| `nickusevich/sql-guardrail` | The [README](https://github.com/nickusevich/sql-guardrail) describes a policy verifier with per-table/column allowlists and a tenant `require_predicate` whose value comes from trusted request context, not the LLM. It says it does not rewrite SQL and recommends combining it with a read-only role, RLS, and statement timeouts. Its [policy reference](https://github.com/nickusevich/sql-guardrail/blob/main/docs/POLICY.md) describes data-modifying CTE, lock, and `SELECT INTO` rejection as policy behavior. | These are README and documentation claims. The implementation and test tree were listed but their pages were unavailable to the browser during this review. No package was installed or executed. |
| PostgreSQL RLS | The [PostgreSQL 18 manual, §5.9](https://www.postgresql.org/docs/18/ddl-rowsecurity.html) states that RLS policies filter normal row access, default-deny applies when RLS is enabled with no policy, superusers and `BYPASSRLS` roles bypass RLS, and table owners normally bypass unless `FORCE ROW LEVEL SECURITY` is set. | The manual is authoritative for documented behavior, but it does not by itself establish this pilot's live configuration. The C1 record is the evidence for its one observed RLS query. |
| Application tenant identity | AWS guidance describes both a principal-per-tenant policy and a runtime tenant context, preferring the latter for pooled SaaS connections and assigning the application responsibility for setting trusted context. See [AWS RLS recommendations](https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-managed-postgresql/rls.html). The `sql-guardrail` README likewise says tenant input must come from the authenticated session. | This pilot's `identity.py` only validates a Python mapping. It does not implement authentication, a PostgreSQL pool, transaction context, or reset behavior. The guidance is architectural documentation, not a test of this implementation. |

## Candidate gap and counter-evidence

The initial candidate was whether an AST guard can rewrite an unscoped query to return tenant-local rows while PostgreSQL RLS independently filters the same unchanged SQL. C1 demonstrates that behavior for one query and fixture: the baseline exposed the other tenant's row, while the guard and RLS arms returned the two expected tenant-A rows.

That result is useful as a demonstration, but it is not a supported research gap. The reviewed guardrail READMEs explicitly address tenant predicates and/or recommend RLS as a separate enforcement layer. The PostgreSQL manual describes the native control. An individual untested SQL construct, by itself, would not establish that the literature or available tools lack coverage. No comparative source-level or empirical result here establishes an unanswered, nontrivial question.

## Evidence labels

- **VERIFIED locally:** the current guard and tests were inspected; the local unit suite was run after its focused hardening changes; the C1 evidence JSON records three successful PostgreSQL executions and their captured outputs.
- **VERIFIED from primary documentation:** PostgreSQL's documented owner, `FORCE`, superuser, and `BYPASSRLS` behavior; AWS's documented tenant-context patterns.
- **README/documentation claim:** capabilities of the two external SQL guard projects. Their implementation/test bodies were not available for inspection in this review.
- **UNKNOWN:** relative security, performance, or correctness across general SQL workloads; behavior of C2–C7 on PostgreSQL; correctness of third-party implementation claims beyond the inspected documentation.

## Decision

Use portfolio-demo scope. The single C1 result confirms a known example of layered enforcement; the reviewed documentation already covers the general combination, and this pilot has not tested a specific unresolved behavior. See `PROJECT_DECISION.md` for the gate and stop conditions.

## Literature references addendum (2026-10-27)

Two additional user-specified papers were checked against their arXiv records and full-text pages:

- Kuncan Wang, Ziting Wang, Peizhuo Lv, Haoyang Li, Guoliang Li, Gao Cong, and Wei Dong, [“Data Agents Under Attack: Vulnerabilities in LLM-Driven Analytical Systems”](https://arxiv.org/abs/2606.08661), arXiv:2606.08661, 2026. The paper reports an eight-risk framework across interpretation, execution, and policy layers; 14 attack techniques; and evaluation on six systems. It discusses over-privileged DB connections, expensive queries, policy forgetting, and compositional leakage. It concerns full data-agent workflows, not this fixed-SQL pilot.
- Francisco Javier Arceo and Varsha Prasad Narsing, [“Securing the Agent: Vendor-Neutral, Multitenant Enterprise Retrieval and Tool Use”](https://arxiv.org/abs/2605.05287), ACM CAIS ’26, 2026, DOI [10.1145/3786335.3813145](https://doi.org/10.1145/3786335.3813145). The paper proposes and evaluates layered multitenant retrieval authorization and server-side orchestration; it reports an OGX implementation. The title is not “OGX”; OGX is the framework/implementation discussed in the paper. It does not evaluate this repository’s SQL AST rewrite or PostgreSQL C1 case.

These sources strengthen the general motivation for trusted identity, database-side authorization, and session-level risk, but they do not establish that this pilot addresses a novel problem. In particular, C4 is one aggregate query, not a compositional disclosure test, and C7 has no live pool test. The portfolio-demo decision above is unchanged. See `RESEARCH_BACKGROUND.md` for the distinction between each paper’s claims and this project’s implementation.
