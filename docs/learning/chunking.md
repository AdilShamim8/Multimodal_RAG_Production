# Chunking

## Concept

Chunking is the process of splitting a document into smaller pieces (chunks) for embedding and retrieval. We embed chunks (not whole documents) because:
1. Embedding models work best on text of ~500 tokens.
2. Retrieval returns chunks, not documents — chunks fit in the LLM context.
3. Citations point to specific chunks (with page + section).

## Why it exists

Whole-document embedding loses local structure. A 50-page document embedded as one vector cannot answer "What is the parental leave policy?" because the embedding captures the document's overall topic, not the specific section.

Chunking breaks the document into embeddable pieces, each with its own vector. Retrieval returns the most relevant chunks, which the LLM uses as evidence.

## Strategies (all implemented in `src/ingestion/chunking.py`)

### Strategy A: Fixed-token chunks

Split text into chunks of N tokens (default 512), with M tokens of overlap (default 64).

- Pros: simple, deterministic.
- Cons: may split mid-sentence; loses section boundaries.

### Strategy B: Sliding window

Slide a window of N tokens with a stride of S tokens.

- Pros: every token appears in multiple chunks (reduces boundary information loss).
- Cons: more chunks = more storage and retrieval cost.

### Strategy C: Semantic

Split at points where adjacent sentences are semantically dissimilar (using sentence embeddings).

- Pros: chunks are topically coherent.
- Cons: requires an extra embedding pass; slower ingestion.

### Strategy D: Structure-aware (default)

Split on markdown headings first, then fall back to fixed-token within a section.

- Pros: preserves section boundaries; chunks are coherent.
- Cons: requires heading detection (works for markdown; needs layout-aware parsing for PDF).

## How to choose

Run the chunking experiment (Phase 5):

```bash
python -m evals.run_chunking --strategies fixed,sliding,semantic,structure-aware
```

Compare Recall@K and answer quality. Pick the winner. Document the decision in `evals/reports/chunking_comparison.md`.

For our corpus (markdown + PDF with clear section structure), **structure-aware** won.

## Where it appears in the code

- `src/ingestion/chunking.py` — all 4 strategies
- `src/ingestion/indexer.py` — calls the chunker, embeds each chunk, inserts to DB

## Trade-offs

### Chunk size

- Too small (128 tokens): loses context; the chunk may not contain enough info to answer.
- Too large (2048 tokens): dilutes relevance signal; fewer chunks fit in LLM context.

Sweet spot: 400–800 tokens for prose.

### Overlap

- No overlap: information at boundaries is lost.
- Too much overlap: storage bloat; same content retrieved multiple times.

Sweet spot: 10–15% of chunk size (e.g., 64 token overlap on a 512-token chunk).

## Failure modes

- **Splitting mid-sentence** — chunk ends or starts with a partial sentence. Mitigated by structure-aware chunking.
- **Losing page numbers** — chunk has no `page` attribute, citations can't reference a page. Mitigated by capturing `page` during parsing.
- **Code blocks split** — code becomes unreadable. Mitigated by structure-aware chunking that preserves code blocks.

## Further reading

- LangChain, "Text Splitters" documentation (concepts, even if you don't use the library)
- Anthropic, "Contextual Retrieval" (2024) — chunking + context
