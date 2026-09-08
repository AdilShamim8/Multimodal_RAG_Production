# Prompt version: v1

# Abstention prompt

Use this when the system determines it cannot answer.

Standard abstention message:

> I don't have enough evidence to answer this confidently.

Variations:
- For NO_DOCUMENTS: "I couldn't find any documents matching your question."
- For CONFLICTING_SOURCES: "I found conflicting information in the sources and cannot give a definitive answer."
- For OUTDATED_SOURCES: "The only sources I found are outdated."
- For UNSUPPORTED query class: "I don't have enough evidence to answer this confidently."
- For PERMISSION_DENIED: "You don't have access to information that would answer this question."

Never reveal WHY evidence is insufficient in a way that leaks information about the corpus.
