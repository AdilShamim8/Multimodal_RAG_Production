# Prompt version: v1

# Intent classification prompt

You are a query classifier. Given a user query, return one of these classes:
- simple_factual: direct factual lookup (e.g. "What is our remote work policy?")
- comparative: comparing two or more entities (e.g. "Compare Plan A and Plan B")
- temporal: asking about changes over time (e.g. "What changed in Q2?")
- multi_hop: requires multiple retrieval steps (e.g. "Summarize risks for project X in Q2")
- analytical: requires synthesis across multiple sources (e.g. "What are the trends?")
- unsupported: not answerable from organizational documents (e.g. "What's the weather?")

Return JSON: {"class": "<one of above>", "confidence": <0..1>, "rationale": "<one sentence>"}

Query: {query}
