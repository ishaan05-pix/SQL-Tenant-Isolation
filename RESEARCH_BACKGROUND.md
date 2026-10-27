# Research background

**Purpose.** This note uses two user-specified papers to situate a small SQL tenant-isolation engineering demo. It does not reproduce either paper or claim a research contribution.

## Practical problem

An LLM-assisted analytics system may create SQL that is syntactically valid but omits tenant scope. If the database session can read several tenants, an unscoped query can expose another tenant’s rows. A predicate-rewriting guard and database row-level security (RLS) are distinct control points: the guard can reject or transform a query before execution; RLS filters rows at the database boundary when policies and execution identity are correctly configured.

This pilot narrows that problem to a synthetic two-tenant fixture and frozen SQL cases C1–C7. C1 has its original historical database record. Separate read-only PostgreSQL observations are recorded for C2, C3, C4, and C6. C5 and C7 remain untested against PostgreSQL. These selected fixture observations do not establish a general security guarantee. The project has no LLM, application authentication service, or runtime pool implementation.

The C1 record predates the later case runs and correctly says that only C1 was executed in that record. `results/stage_a_preflight.json` is an earlier static snapshot whose execution status predates the database observations. The later C2/C4 and C3/C6 evidence files record separate read-only runs; none of these records replaces another.

The test evidence has two distinct parts: 12 static Python unit tests and four opt-in PostgreSQL integration tests for C2, C3, C4, and C6. GitHub Actions runs only the static tests; it does not access PostgreSQL.

## Paper 1: data-agent attack surface

**Kuncan Wang, Ziting Wang, Peizhuo Lv, Haoyang Li, Guoliang Li, Gao Cong, and Wei Dong.** “Data Agents Under Attack: Vulnerabilities in LLM-Driven Analytical Systems.” arXiv preprint arXiv:2606.08661, submitted 7 June 2026. [arXiv abstract](https://arxiv.org/abs/2606.08661) · [paper HTML](https://arxiv.org/html/2606.08661v1).

The authors present a layered vulnerability framework with eight risks spanning interpretation, execution, and policy; a taxonomy of three adversary goals, seven tactics, and fourteen techniques; and schema-grounded attack payload generation. They report evaluation across six systems: four open-source data agents and two commercial analytics systems. Relevant issues include uncontrolled query cost, over-privileged database connections, policy forgetting under context pressure, and disclosure composed across individually permitted aggregate queries. These are claims and findings reported by that paper, not results measured by this repository.

**How it informed this pilot.** The paper motivates treating tenant identity and database access as a security boundary rather than relying on a model prompt. Its over-privileged-connection concern is relevant to the pilot’s authenticated-tenant input and PostgreSQL role assumptions. Frozen C4 is a single aggregate case and C7 is intended to probe A→B→A identity reuse; neither validates multi-query disclosure or live pool lifecycle in PostgreSQL here.

**What differs.** The paper studies data-agent attack surfaces, adversarial content/prompts, multi-tool workflows, resource use, and six systems. This pilot has no agent, model, payload-generation pipeline, or broad attack evaluation. It compares baseline, AST-rewritten, and RLS outcomes for selected frozen SQL cases on a synthetic fixture.

## Paper 2: multitenant retrieval and tool use

**Francisco Javier Arceo and Varsha Prasad Narsing.** “Securing the Agent: Vendor-Neutral, Multitenant Enterprise Retrieval and Tool Use.” ACM Conference on AI and Agentic Systems (ACM CAIS ’26), 2026; arXiv:2605.05287, submitted 6 May 2026. [arXiv abstract and publication details](https://arxiv.org/abs/2605.05287) · [paper HTML](https://arxiv.org/html/2605.05287v1) · [ACM DOI](https://doi.org/10.1145/3786335.3813145).

The paper describes a layered isolation architecture for multitenant RAG and agents: policy-aware ingestion, retrieval-time ABAC gating/filtering, shared inference, and server-side orchestration for tool authorization and state isolation. It reports an implementation using OGX (Open GenAI Stack) and a synthetic testbed evaluation. The paper reports zero cross-tenant leakage in its gated configurations and discusses latency, throughput, retrieval-quality, and scaling trade-offs. Those are the paper’s reported results under its stated assumptions and setup; they are not evidence about this SQL pilot. The paper’s title is *Securing the Agent: Vendor-Neutral, Multitenant Enterprise Retrieval and Tool Use*; OGX is its related framework/implementation, not the paper title.

**How it informed this pilot.** Its separation of relevance/generation from authorization supports the general design principle that tenant authorization must be enforced by a trusted component. The pilot applies that principle to relational SQL with query rewriting and PostgreSQL RLS, rather than vector retrieval or server-side agent orchestration.

**What differs.** This repository has no document ingestion, vector index, ABAC policy engine, shared inference service, server-side agent orchestration, or retrieval evaluation. Its selected C1/C2/C3/C4/C6 SQL observations are small direct fixture tests, not a reproduction of OGX or the paper’s synthetic retrieval benchmark.

## Implemented mechanisms versus cited concepts

| Mechanism or idea | Status in this project |
|---|---|
| SQLGlot parsing and relation-scoped tenant predicate rewriting | Implemented in `sql_guard.py`; covered by 12 static tests, guarded SQL execution for C1/C2/C3/C4, and rejection without execution for C6. |
| Fixture-based expected-result oracle | Implemented in `oracle.py`; computes expected values from `cases.json` independently of the guard and database policy. |
| PostgreSQL RLS | Configured in the existing fixtures and observed for C1, C2, C3, C4, and C6. The opt-in Python test executes read-only SQL against pre-provisioned databases; it does not provision or configure RLS. |
| Tenant principal mapping | A pure static helper in `identity.py`; not an authentication system or connection pool. |
| Frozen C1–C7 | Definitions in `cases.json`; C1 has a historical record, while C2/C3/C4/C6 have separate read-only PostgreSQL observations. C5 and C7 remain untested against PostgreSQL. |
| Prompt injection, generated attacks, LLM SQL generation, ABAC retrieval, vector search, server-side orchestration, audit telemetry, cost/resource controls, cumulative disclosure controls | Discussed in the cited papers or proposed future directions; not implemented or validated here. |

## Research positioning

The papers informed the motivation and choice of security boundaries, but this project is a literature-informed engineering evaluation of a small set of SQL paths. It does not reproduce either paper’s systems, data, methods, or metrics. The reviewed literature and related guardrail documentation already cover tenant authorization, database enforcement, and agent isolation at a broader level. These bounded fixture observations cannot establish a literature gap, a general security guarantee, or a generalizable empirical result, and do not support novelty claims.
