# Project decision: portfolio demo

**Decision date:** 2026-10-27  
**Decision:** Do not continue this as a research project on current evidence. Keep it as a small portfolio demonstration of a narrow AST tenant predicate rewrite alongside PostgreSQL RLS.

## Why

The only live database result in the repository is frozen C1. It shows that, for one fixture query and one authenticated role, an unprotected baseline exposed `o_b1`, while the rewritten SQL and unchanged SQL under RLS returned `o_a1` and `o_a2`.

The reviewed primary documentation and competitor descriptions already cover tenant predicates in SQL guardrails and recommend RLS as a separate row-visibility layer. No reviewed source or result establishes a concrete, nontrivial unanswered behavior. The absence of a particular test from an inaccessible test suite is not evidence that the behavior is unaddressed.

This project can credibly show:

- A small SQLGlot transformation over the frozen synthetic workload.
- Static rejection of several unsupported or unsafe query forms.
- An independently computed expected result from fixture rows.
- One captured PostgreSQL C1 comparison with baseline, rewritten SQL, and RLS observations.

It cannot establish generalized SQL rewriting correctness, tenant isolation across arbitrary queries, pool lifecycle safety, production suitability, comparative performance, or research novelty.

## Stop conditions

- If a supported SQL form can execute a write or escape the supported relation set, keep that form rejected until a narrowly scoped regression test proves the correction.
- If the available test suite fails, do not present the affected implementation path as validated.
- If future database checks require changing existing fixture resources or privileges, stop for explicit approval.
- If the demo cannot reproduce its static tests without overwriting historical evidence or exposing credentials, limit delivery to the documented evidence and do not claim reproducibility beyond what was run.
- Abandon the security-demo framing if the product is expanded beyond the tested subset without corresponding tests and a trusted execution boundary.

## Revisit only with a concrete question

Research continuation would require a clearly bounded behavior not adequately addressed by reviewed sources, a falsifiable comparison, and safe testability. This gate found no such candidate. C1 should remain a portfolio example, not be used to imply a literature gap.
