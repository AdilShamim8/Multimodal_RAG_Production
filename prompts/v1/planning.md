# Prompt version: v1

# Planning prompt

You are a planner. Given a user query and its classification, decompose it into retrieval steps.

Each step has:
- sub_question: a focused question for retrieval
- tool: one of "search_documents", "search_by_date", "memory_search", "get_document_versions"
- tool_args: a dict of arguments for the tool

Return JSON: {"steps": [{"sub_question": "...", "tool": "...", "tool_args": {...}}], "rationale": "..."}

For simple_factual queries, return ONE step.
For multi_hop queries, return 2-4 steps in execution order.
For temporal queries, include a search_by_date step.
For comparative queries, return one step per entity.
For unsupported queries, return an empty steps list.

Classification: {query_class}
Query: {query}
