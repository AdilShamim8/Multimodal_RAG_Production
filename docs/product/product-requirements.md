# Product Requirements

## Problem

Organizations accumulate knowledge in constantly changing documents — HR policies, project plans, technical specs, incident reports, financial summaries. Employees waste significant time searching for answers that exist somewhere in the corpus. When they do find documents, they may be looking at outdated versions, or at documents they're not authorized to see.

Existing tools (Slack search, Google Drive search, Notion search) are keyword-only, miss semantic intent, don't enforce RBAC at the retrieval layer, and don't ground their answers in citations.

## Target users

- **Employees** — ask questions about HR policies, benefits, internal processes.
- **Managers** — ask about project status, budgets, team performance, incidents.
- **Administrators** — ingest new documents, run evaluations, view traces, manage users.
- (Future) **Students** — ask about course catalog, requirements, schedules.
- (Future) **Researchers** — ask about prior work, internal research notes.

## User stories

1. As an employee, I want to ask "What is our remote work policy?" and get a direct answer with a citation to the HR handbook.
2. As an employee, I want the system to abstain when I ask something outside the corpus ("What's the weather?") rather than hallucinate.
3. As a manager, I want to ask "What changed in Project X during Q2?" and get a synthesized answer referencing multiple documents.
4. As an employee, I want the system to use the CURRENT version of a policy, not the 2020 version, and to tell me when versions conflict.
5. As an employee, I want to click a citation and see the source document snippet so I can verify the claim.
6. As an employee, I want the system to remember my preferences (bullet points, concise answers) across conversations.
7. As an administrator, I want to ingest new documents and have them searchable within minutes.
8. As an administrator, I want to see system health, recent queries, and evaluation results in a dashboard.
9. As an employee, I want to be sure that asking about manager-only information returns nothing, not a leak.
10. As a user, I want to know when the system is uncertain — confidence indicators help me decide whether to trust the answer.

## Non-goals

This system does NOT attempt to:
- Replace Slack / email / project management tools.
- Provide real-time collaboration.
- Handle multimodal input (images, audio) — text only for v1.
- Auto-generate documents — it answers questions, it doesn't write reports.
- Replace human judgment for high-stakes decisions (legal, medical, financial).
- Support multiple natural languages in v1 (English only; BGE-m3 is multilingual but our prompts are English).

## Functional requirements

| ID    | Requirement                                                                       | Acceptance criteria                                                                                          |
| ----- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| FR-1  | User can ask a natural-language question and receive a grounded answer           | Answer is supported by retrieved evidence; citations included                                                |
| FR-2  | Every factual claim in an answer has a citation                                  | Citation maps to a chunk that supports the claim (verified by LLM-judge)                                     |
| FR-3  | System abstains when evidence is insufficient                                    | For "negative_unsupported" queries, returns "I don't have enough evidence..."                                |
| FR-4  | System respects document versions                                                | Currently-effective version preferred; expired versions penalized; conflicts reported explicitly             |
| FR-5  | System enforces RBAC at retrieval                                                | Employee cannot retrieve manager-only chunks; cross-user memory leakage blocked                              |
| FR-6  | System persists user preferences in long-term memory                             | Preferences survive across conversations; user can list/edit/delete memories                                 |
| FR-7  | System defends against prompt injection                                          | 10 known attack patterns blocked                                                                             |
| FR-8  | Administrator can ingest new documents                                           | PDF/MD/HTML/DOCX supported; ingestion completes within 60s for a 100-page document                          |
| FR-9  | Administrator can run evaluations                                                | `make eval` produces JSON + markdown reports; quality gate enforced in CI                                    |
| FR-10 | Every request is traceable end-to-end                                            | Trace ID returned in response; full span tree visible in Langfuse                                            |

## Non-functional requirements

| Concern            | Target                                            |
| ------------------ | ------------------------------------------------- |
| Latency (p95)      | < 5s for simple queries, < 15s for multi-hop      |
| Reliability        | 99.5% monthly uptime                              |
| Scalability        | 100k documents, 100 concurrent users per tenant   |
| Security           | Zero unauthorized data leaks in security tests    |
| Maintainability    | All code linted, typed, tested; ADRs for decisions|
| Observability      | 100% of requests traced; metrics in Prometheus    |
| Cost               | < $0.001 per query (GPT-4o-mini + local models)   |
| Availability       | Single-region HA; multi-region in v2              |
| Evaluation quality | Faithfulness ≥ 0.85; hallucination rate ≤ 0.10   |
