# Research background

**Purpose.** This note uses two user-specified papers to situate a small SQL tenant-isolation engineering demo. It does not reproduce either paper or claim a research contribution.

## Practical problem

An LLM-assisted analytics system may create SQL that is syntactically valid but omits tenant scope. If the database session can read several tenants, an unscoped query can expose another tenant’s rows. A predicate-rewriting guard and database row-level security (RLS) are distinct control points: the guard can reject or transform a query before execution; RLS filters rows at the database boundary when policies and execution identity are correctly configured.

This pilot narrows that problem to a synthetic two-tenant fixture and frozen SQL cases C1–C7. Its only recorded PostgreSQL comparison is C1. The project has no LLM, application authentication service, or runtime pool implementation.

## Paper 1: data-agent attack surface

**Kuncan Wang, Ziting Wang, Peizhuo Lv, Haoyang Li, Guoliang Li, Gao Cong, and Wei Dong.** “Data Agents Under Attack: Vulnerabilities in LLM-Driven Analytical Systems.” arXiv preprint arXiv:2606.08661, submitted 7 June 2026. [arXiv abstract](https://arxiv.org/abs/2606.08661) · [paper HTML](https://arxiv.org/html/2606.08661v1).

The authors present a layered vulnerability framework with eight risks spanning interpretation, execution, and policy; a taxonomy of three adversary goals, seven tactics, and fourteen techniques; and schema-grounded attack payload generation. They report evaluation across six systems: four open-source data agents and two commercial analytics systems. Relevant issues include uncontrolled query cost, over-privileged database connections, policy forgetting under context pressure, and disclosure composed across individually permitted aggregate queries. These are claims and findings reported by that paper, not results measured by this repository.

**How it informed this pilot.** The paper motivates treating tenant identity and database access as a security boundary rather than relying on a model prompt. Its over-privileged-connection concern is relevant to the pilot’s authenticated-tenant input and PostgreSQL role assumptions. Frozen C4 is a single aggregate case and C7 is intended to probe A→B→A identity reuse; neither validates multi-query disclosure or live pool lifecycle in PostgreSQL here.

**What differs.** The paper studies data-agent attack surfaces, adversarial content/prompts, multi-tool workflows, resource use, and six systems. This pilot has no agent, model, payload-generation pipeline, or broad attack evaluation. It compares one fixed SQL query’s baseline, AST-rewritten, and RLS outcomes on a synthetic fixture.

## Paper 2: multitenant retrieval and tool use

**Francisco Javier Arceo and Varsha Prasad Narsing.** “Securing the Agent: Vendor-Neutral, Multitenant Enterprise Retrieval and Tool Use.” ACM Conference on AI and Agentic Systems (ACM CAIS ’26), 2026; arXiv:2605.05287, submitted 6 May 2026. [arXiv abstract and publication details](https://arxiv.org/abs/2605.05287) · [paper HTML](https://arxiv.org/html/2605.05287v1) · [ACM DOI](https://doi.org/10.1145/3786335.3813145).

The paper describes a layered isolation architecture for multitenant RAG and agents: policy-aware ingestion, retrieval-time ABAC gating/filtering, shared inference, and server-side orchestration for tool authorization and state isolation. It reports an implementation using OGX (Open GenAI Stack) and a synthetic testbed evaluation. The paper reports zero cross-tenant leakage in its gated configurations and discusses latency, throughput, retrieval-quality, and scaling trade-offs. Those are the paper’s reported results under its stated assumptions and setup; they are not evidence about this SQL pilot. The paper’s title is *Securing the Agent: Vendor-Neutral, Multitenant Enterprise Retrieval and Tool Use*; OGX is its related framework/implementation, not the paper title.

**How it informed this pilot.** Its separation of relevance/generation from authorization supports the general design principle that tenant authorization must be enforced by a trusted component. The pilot applies that principle to relational SQL with query rewriting and PostgreSQL RLS, rather than vector retrieval or server-side agent orchestration.

**What differs.** This repository has no document ingestion, vector index, ABAC policy engine, shared inference service, server-side agent orchestration, or retrieval evaluation. Its C1 execution is a tiny direct SQL experiment, not a reproduction of OGX or the paper’s synthetic retrieval benchmark.

## Implemented mechanisms versus cited concepts

| Mechanism or idea | Status in this project |
|---|---|
| SQLGlot parsing and relation-scoped tenant predicate rewriting | Implemented in `sql_guard.py`; covered only by static unit tests plus the recorded C1 guarded SQL execution. |
| Fixture-based expected-result oracle | Implemented in `oracle.py`; computes expected values from `cases.json` independently of the guard and database policy. |
| PostgreSQL RLS | Configured and exercised for the historical C1 fixture record only. No RLS setup/execution harness is part of the Python implementation. |
| Tenant principal mapping | A pure static helper in `identity.py`; not an authentication system or connection pool. |
| Frozen C1–C7 | Definitions in `cases.json`; only C1 has recorded PostgreSQL observations. |
| Prompt injection, generated attacks, LLM SQL generation, ABAC retrieval, vector search, server-side orchestration, audit telemetry, cost/resource controls, cumulative disclosure controls | Discussed in the cited papers or proposed future directions; not implemented or validated here. |

## Research positioning

The papers informed the motivation and choice of security boundaries, but this project is a literature-informed engineering evaluation of one small SQL path. It does not reproduce either paper’s systems, data, methods, or metrics. The reviewed literature and related guardrail documentation already cover tenant authorization, database enforcement, and agent isolation at a broader level. A one-query pilot cannot establish a literature gap, generalize an empirical finding, or support novelty claims.
