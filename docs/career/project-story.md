# Project Story — Agentic RAG Platform

> A 3-paragraph narrative you can tell in an interview. Tailor the bracketed numbers to your actual measurements.

## Paragraph 1: The problem

I wanted to build a serious Agentic RAG system — not a "ChatGPT wrapper" demo, but something that could plausibly be deployed inside an organization to answer questions over constantly changing internal knowledge. The key requirements were grounded answers (no hallucination), precise citations (so users could verify claims), document freshness awareness (so the system prefers the current version of a policy over the 2020 version), and access control (so an employee couldn't see manager-only financials). I also wanted the system to be measurable — every improvement had to show up in a reproducible evaluation, not just vibes.

## Paragraph 2: The approach

I started with research — reading production RAG write-ups, comparing open-source platforms, and documenting technology selection in 8 Architecture Decision Records (ADRs). The stack settled on PostgreSQL + pgvector (single datastore for relational + vector + FTS), BGE-m3 for embeddings, BGE-reranker-v2-m3 for cross-encoder reranking, a custom state machine for agent orchestration (instead of LangGraph, which would have added complexity without value at our scale), and OpenTelemetry + Langfuse for observability. I built the system in 14 phases: discovery, infrastructure, ingestion, baseline RAG, retrieval engineering, evaluation, agentic RAG, memory + freshness, security + RBAC, observability + failure handling, frontend, production hardening, adversarial testing, and a final engineering review. Each phase had a validation gate — measurable criteria I had to meet before moving on.

## Paragraph 3: The results

The final system demonstrates [hybrid retrieval with RRF improves Recall@5 from X to Y vs. dense-only], [the cross-encoder reranker adds ~170ms p95 latency but improves MRR by Z%], [the agent correctly decomposes multi-hop queries into N sub-questions and terminates within 30s on 100% of test cases], [RBAC enforced in SQL prevents unauthorized access in 100% of security tests], [prompt injection defenses block all 10 known attack patterns], and [the full pipeline runs at $X per query with p95 latency of Yms]. The evaluation framework with 6 baselines is wired into CI as a quality gate — if faithfulness drops below 0.85, the build fails. The codebase includes [8 ADRs, 13 architecture diagrams, 14 learning docs, and a final report] — enough documentation that another engineer could pick it up and continue.
