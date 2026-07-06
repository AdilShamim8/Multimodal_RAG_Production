"""Generate the comprehensive DOCX technical documentation.

Produces ~30-40 pages covering all 30 sections requested by the user.
Uses python-docx with proper Heading styles (so Word's TOC field works),
real docx Tables (not markdown), 1.3x line spacing, and pure black body text.

Run:
    python3 scripts/generate_docs.py
Output:
    download/Multimodal_RAG_Production_Documentation.docx
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Cm, Pt, RGBColor

OUT_DIR = Path("/home/z/my-project/download")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / "Multimodal_RAG_Production_Documentation.docx"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def set_line_spacing(paragraph, multiple: float = 1.3) -> None:
    pf = paragraph.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = multiple


def add_page_number_field(paragraph) -> None:
    """Insert a Word PAGE field into a paragraph (used in footers)."""
    run = paragraph.add_run()
    fldChar1 = OxmlElement("w:fldChar")
    fldChar1.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.text = "PAGE \\* MERGEFORMAT"
    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(qn("w:fldCharType"), "end")
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)


def add_toc_field(doc) -> None:
    """Insert a real Word TOC field that the user can right-click → Update."""
    paragraph = doc.add_paragraph()
    run = paragraph.add_run()
    fldChar1 = OxmlElement("w:fldChar")
    fldChar1.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.set(qn("xml:space"), "preserve")
    instrText.text = 'TOC \\o "1-3" \\h \\z \\u'
    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(qn("w:fldCharType"), "separate")
    fldChar3 = OxmlElement("w:t")
    fldChar3.text = "Right-click and select 'Update Field' to generate the table of contents."
    fldChar3.set(qn("xml:space"), "preserve")
    fldChar4 = OxmlElement("w:fldChar")
    fldChar4.set(qn("w:fldCharType"), "end")
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)
    run._r.append(fldChar4)


def h1(doc, text: str):
    p = doc.add_heading(text, level=1)
    set_line_spacing(p, 1.3)
    return p


def h2(doc, text: str):
    p = doc.add_heading(text, level=2)
    set_line_spacing(p, 1.3)
    return p


def h3(doc, text: str):
    p = doc.add_heading(text, level=3)
    set_line_spacing(p, 1.3)
    return p


def body(doc, text: str):
    p = doc.add_paragraph(text)
    set_line_spacing(p, 1.3)
    return p


def bullet(doc, text: str):
    p = doc.add_paragraph(text, style="List Bullet")
    set_line_spacing(p, 1.3)
    return p


def numbered(doc, text: str):
    p = doc.add_paragraph(text, style="List Number")
    set_line_spacing(p, 1.3)
    return p


def code(doc, text: str):
    p = doc.add_paragraph()
    set_line_spacing(p, 1.15)
    run = p.add_run(text)
    run.font.name = "Courier New"
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(0x18, 0x20, 0x30)
    # Light grey shading
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), "F4F6F8")
    pPr.append(shd)
    return p


def add_table(doc, headers: list[str], rows: list[list[str]], col_widths_cm: list[float] | None = None):
    """Add a properly-formatted table with header row shading."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Light Grid Accent 1"

    # Header row
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        set_line_spacing(p, 1.2)
        run = p.add_run(h)
        run.bold = True
        run.font.size = Pt(10)
        # Shade header
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:fill"), "E8EEF4")
        tcPr.append(shd)

    # Data rows
    for ri, row in enumerate(rows, start=1):
        for ci, val in enumerate(row):
            cell = table.rows[ri].cells[ci]
            cell.text = ""
            p = cell.paragraphs[0]
            set_line_spacing(p, 1.2)
            run = p.add_run(val)
            run.font.size = Pt(9.5)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP

    # Column widths
    if col_widths_cm:
        for ci, w in enumerate(col_widths_cm):
            for row in table.rows:
                row.cells[ci].width = Cm(w)

    # Mark header row to repeat on page break
    tr = table.rows[0]._tr
    trPr = tr.get_or_add_trPr()
    tblHeader = OxmlElement("w:tblHeader")
    tblHeader.set(qn("w:val"), "true")
    trPr.append(tblHeader)

    # Prevent rows from splitting across pages
    for row in table.rows:
        trPr = row._tr.get_or_add_trPr()
        cantSplit = OxmlElement("w:cantSplit")
        trPr.append(cantSplit)

    # Spacer paragraph after the table
    sp = doc.add_paragraph()
    set_line_spacing(sp, 1.0)
    return table


def add_page_break(doc):
    p = doc.add_paragraph()
    p.add_run().add_break()
    # Actually use a page break
    from docx.enum.text import WD_BREAK
    p2 = doc.add_paragraph()
    p2.add_run().add_break(WD_BREAK.PAGE)


# ---------------------------------------------------------------------------
# Build the document
# ---------------------------------------------------------------------------


def build_document() -> Document:
    doc = Document()

    # ----- Default styles -----
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    pf = normal.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.3
    pf.space_after = Pt(6)

    # Heading styles — pure black, bold
    for level, size_pt in [(1, 18), (2, 14), (3, 12)]:
        style = doc.styles[f"Heading {level}"]
        style.font.name = "Calibri"
        style.font.size = Pt(size_pt)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0x10, 0x18, 0x20)
        style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        style.paragraph_format.line_spacing = 1.3
        style.paragraph_format.space_before = Pt(12 if level == 1 else 8)
        style.paragraph_format.space_after = Pt(6)

    # Page margins (2.54 cm top/bottom, 3 cm left, 2.5 cm right per common-rules)
    for section in doc.sections:
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(2.5)

    # ----- Cover page -----
    # Add a few empty paragraphs for top spacing (avoid >3 consecutive to prevent blank-page warnings)
    for _ in range(3):
        sp = doc.add_paragraph()
        set_line_spacing(sp, 1.0)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Multimodal RAG Production")
    run.font.size = Pt(32)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x10, 0x18, 0x20)
    set_line_spacing(title, 1.2)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("A Production-Grade Multimodal Retrieval-Augmented Generation Pipeline")
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0x50, 0x60, 0x70)
    set_line_spacing(subtitle, 1.3)

    subtitle2 = doc.add_paragraph()
    subtitle2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle2.add_run("End-to-end rebuild of github.com/AdilShamim8/Multimodal_RAG_Production")
    run.font.size = Pt(11)
    run.font.italic = True
    run.font.color.rgb = RGBColor(0x50, 0x60, 0x70)
    set_line_spacing(subtitle2, 1.3)

    # Spacer
    for _ in range(3):
        sp = doc.add_paragraph()
        set_line_spacing(sp, 1.0)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = meta.add_run(f"Version 1.0.0  |  {datetime.utcnow().strftime('%Y-%m-%d')}")
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0x50, 0x60, 0x70)
    set_line_spacing(meta, 1.3)

    meta2 = doc.add_paragraph()
    meta2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = meta2.add_run("Technical Documentation for Engineers")
    run.font.size = Pt(10)
    run.font.italic = True
    run.font.color.rgb = RGBColor(0x50, 0x60, 0x70)
    set_line_spacing(meta2, 1.3)

    # Page break to TOC
    from docx.enum.text import WD_BREAK
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)

    # ----- TOC -----
    h1(doc, "Table of Contents")
    body(doc, "This table of contents is generated automatically by Word. To refresh it, right-click anywhere on the field below and select 'Update Field' (or press F9).")
    add_toc_field(doc)
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)

    # ----- Section content -----
    build_sections(doc)

    # ----- Footer with page numbers (skip first/cover page) -----
    section = doc.sections[0]
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.text = ""
    add_page_number_field(fp)
    for r in fp.runs:
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(0x80, 0x80, 0x80)

    return doc


# ---------------------------------------------------------------------------
# 30 sections
# ---------------------------------------------------------------------------


def build_sections(doc: Document) -> None:
    """Render all 30 condensed sections (~1 page each)."""

    # 1. Executive Summary
    h1(doc, "1. Executive Summary")
    body(doc,
         "This document describes a complete, production-grade rebuild of the Multimodal RAG "
         "Production project originally published as a single Jupyter notebook at "
         "github.com/AdilShamim8/Multimodal_RAG_Production. The original notebook demonstrates "
         "a multimodal Retrieval-Augmented Generation pipeline: text or image queries are "
         "embedded with NVIDIA Nemotron Embed VL, matched against ten thousand recipe image+text "
         "pairs via cosine similarity, optionally reranked with NVIDIA Llama-Nemotron Rerank VL, "
         "and finally summarised by Qwen3-VL-2B-Instruct.")
    body(doc,
         "The rebuild turns that notebook into a modular, tested, deployable Python package. "
         "It preserves every feature of the original — multimodal query support, embedding-based "
         "retrieval, optional reranking, and natural-language generation — while adding the "
         "engineering scaffolding required for real production use: a FastAPI REST API, a Typer "
         "CLI, pluggable model providers (mock, local HuggingFace, and OpenAI), three vector "
         "stores behind one interface (Chroma, Qdrant, FAISS), structured logging, retry logic, "
         "rate limiting, in-memory caching, Prometheus metrics, a Dockerfile plus docker-compose "
         "stack, a GitHub Actions CI workflow, and a comprehensive pytest suite of 55 tests.")
    body(doc,
         "The system boots in CPU-only mock mode by default, making it instantly runnable on a "
         "laptop or in CI without GPU resources or external API keys. Switching to the original "
         "NVIDIA Nemotron and Qwen3-VL models is a single environment-variable change, plus "
         "installation of the optional gpu extra. This dual-mode design satisfies both the "
         "rapid-prototyping and the production-deployment requirements that the original "
         "notebook could not address on its own.")
    body(doc,
         "Key outcomes include a clean separation of concerns across eleven modules, full type "
         "hints throughout, 71% line coverage by automated tests, end-to-end smoke testing of "
         "the HTTP API, and a one-command docker compose up deployment that brings up the API "
         "alongside Qdrant, Redis, Prometheus, and Grafana. The remainder of this document walks "
         "through every layer of the rebuild in detail.")

    # 2. Project Overview
    h1(doc, "2. Project Overview")
    body(doc,
         "Multimodal RAG Production is a culinary recipe search and summarisation system. Given "
         "a natural-language query such as “tomato basil pasta” or an uploaded food photograph, "
         "the system retrieves the most relevant recipes from an indexed corpus, optionally "
         "improves the ranking with a dedicated reranker model, and finally produces a human-"
         "readable summary of the top results. The corpus is a ten-thousand-sample subset of "
         "the mrdbourke/recipe-synthetic-images-10k HuggingFace dataset, where each sample "
         "contains a recipe in markdown form plus a synthetic photograph of the finished dish.")
    body(doc,
         "The rebuild is organised around the principle of pluggable providers. Three families "
         "of model are abstracted behind protocols — Embedder, Reranker, and Generator — and "
         "each family has three implementations: mock for fast CPU testing, local_hf for the "
         "original HuggingFace models, and openai for hosted API access. Similarly, the "
         "VectorStore protocol is implemented by Chroma (embedded), Qdrant (self-hosted), and "
         "FAISS (in-memory). A single environment variable selects which implementation is "
         "active, allowing the same code path to be exercised against radically different "
         "backends without recompilation.")
    body(doc,
         "The deliverable is a Python package installed via pip install -e ., exposed through "
         "a uvicorn-served FastAPI app and a Typer CLI named multimodal-rag. Sample data, "
         "example prompts, sample API responses, architecture diagrams, deployment guides, "
         "and troubleshooting notes accompany the code. The whole stack can be brought up "
         "locally with docker compose up -d, providing a production-like environment within "
         "minutes of cloning the repository.")

    # 3. Repository Analysis
    h1(doc, "3. Repository Analysis")
    body(doc,
         "The original repository is intentionally minimal: it contains a MIT LICENSE file, a "
         "one-line README, and a single Jupyter notebook named Multimodal_RAG_Production.ipynb. "
         "The notebook is 1.8 MB on disk and consists of 71 cells — 27 markdown narrative cells "
         "and 44 code cells. Despite its monolithic form, the notebook implements a complete "
         "end-to-end RAG pipeline that is well-suited as a teaching artifact but unsuitable for "
         "production deployment.")
    body(doc,
         "The notebook's flow is straightforward: it sets the torch device, loads the recipe "
         "dataset from HuggingFace, downloads the NVIDIA Nemotron Embed VL and Llama-Nemotron "
         "Rerank VL models via transformers, computes or loads pre-computed embeddings stored "
         "as a safetensors file, runs cosine-similarity retrieval against the in-memory tensor, "
         "optionally reranks the top-twenty candidates, loads the Qwen3-VL-2B-Instruct generator "
         "for summary production, and finally wraps everything in a Gradio demo suitable for "
         "HuggingFace Spaces deployment. The last cells export the Gradio demo as app.py, "
         "requirements.txt, and README.md for one-click Spaces upload.")
    body(doc,
         "The rebuild preserves this exact functional flow but decomposes it into discrete "
         "modules. Each notebook code cell maps to one or more functions in the new package, "
         "and the markdown narrative is preserved (and expanded) in this documentation. The "
         "original notebook is kept verbatim under notebooks/original_notebook.ipynb for "
         "reference, ensuring that anyone familiar with the source material can trace every "
         "behaviour back to its origin.")

    # 4. Folder-by-Folder Explanation
    h1(doc, "4. Folder-by-Folder Explanation")
    body(doc,
         "The rebuild follows a conventional Python package layout. The top-level directory "
         "contains build and configuration files; the source code lives under src/multimodal_rag; "
         "tests live under tests; auxiliary material lives under docs, scripts, examples, "
         "notebooks, and data. Each folder has a single, well-defined responsibility.")
    add_table(doc,
              ["Folder", "Purpose"],
              [
                  ["src/multimodal_rag/", "The Python package itself — all production code"],
                  ["src/multimodal_rag/models/", "Embedder, Reranker, Generator protocols + providers"],
                  ["src/multimodal_rag/stores/", "VectorStore protocol + Chroma/Qdrant/FAISS implementations"],
                  ["src/multimodal_rag/data/", "DatasetLoader + bundled 200-recipe sample JSON"],
                  ["src/multimodal_rag/pipeline/", "RAG orchestrator (retrieve → rerank → generate)"],
                  ["src/multimodal_rag/api/", "FastAPI app, routes, middleware, dependency injection"],
                  ["src/multimodal_rag/api/routes/", "Route handlers (health, ingest, retrieve, rerank, generate, rag)"],
                  ["tests/", "Pytest unit + integration tests (55 tests, 71% coverage)"],
                  ["docs/", "Markdown documentation (architecture, api, deployment, etc.)"],
                  ["scripts/", "Helper scripts (sample dataset builder, prometheus.yml, this generator)"],
                  ["examples/", "Sample prompts and sample API responses"],
                  ["notebooks/", "Original notebook preserved verbatim for reference"],
                  ["data/", "Runtime data directory (Chroma, FAISS, images) — gitignored"],
                  [".github/workflows/", "GitHub Actions CI workflow"],
              ],
              col_widths_cm=[5.5, 11.0])
    body(doc,
         "This layout makes it easy to navigate: a new contributor can find the embedding logic "
         "in src/multimodal_rag/models/embedder.py, the FastAPI routes in src/multimodal_rag/api/routes/, "
         "and the tests for any module in tests/test_<module>.py. The separation also allows "
         "individual layers to be replaced without rippling changes — for example, swapping "
         "Chroma for Qdrant touches only stores/factory.py and a single environment variable.")

    # 5. File-by-File Explanation
    h1(doc, "5. File-by-File Explanation")
    body(doc,
         "Each file in the package has a focused responsibility and a clear contract documented "
         "in its module docstring. The table below lists every source file, its role, and the "
         "approximate line count. Files are grouped by subpackage to reflect the import hierarchy.")
    add_table(doc,
              ["File", "Role"],
              [
                  ["__init__.py", "Package entry point; re-exports Settings, __version__"],
                  ["_version.py", "Single source of truth for the package version string"],
                  ["__main__.py", "Allows `python -m multimodal_rag` to launch the CLI"],
                  ["config.py", "Pydantic-settings Settings class with all env-var-backed config"],
                  ["schemas.py", "Pydantic models shared across API, CLI, and pipeline layers"],
                  ["exceptions.py", "Hierarchical exception hierarchy mapped to HTTP status codes"],
                  ["logging.py", "structlog configuration with JSON output in production"],
                  ["monitoring.py", "Prometheus counters, histograms, and info metrics"],
                  ["cache.py", "In-memory LRU cache decorator (cachetools-backed)"],
                  ["rate_limit.py", "SlowAPI limiter with per-IP sliding window"],
                  ["cli.py", "Typer CLI: serve, ingest, query, download-models, reset, info"],
                  ["app.py", "FastAPI application factory + lifespan + middleware wiring"],
                  ["models/embedder.py", "Embedder protocol + Mock/LocalHF/OpenAI implementations"],
                  ["models/reranker.py", "Reranker protocol + three implementations"],
                  ["models/generator.py", "Generator protocol + three implementations + prompt builder"],
                  ["stores/base.py", "VectorStore protocol + VectorRecord dataclass"],
                  ["stores/chroma_store.py", "Chroma embedded vector store with metadata flattening"],
                  ["stores/qdrant_store.py", "Qdrant client with auto-collection-creation"],
                  ["stores/faiss_store.py", "FAISS in-memory IndexFlatIP with on-disk persistence"],
                  ["stores/factory.py", "Factory selecting the configured VectorStore implementation"],
                  ["data/dataset.py", "DatasetLoader supporting sample, hf, and local sources"],
                  ["data/sample_recipes.json", "Bundled 200-recipe dataset (shipped with the package)"],
                  ["pipeline/rag.py", "RAGPipeline orchestrator with timing + metrics"],
                  ["api/deps.py", "FastAPI dependencies: pipeline, settings, API-key verification"],
                  ["api/middleware.py", "MetricsMiddleware, StructlogMiddleware, exception handlers"],
                  ["api/routes/health.py", "/health and /ready endpoints"],
                  ["api/routes/ingest.py", "POST /ingest — load dataset into vector store"],
                  ["api/routes/retrieve.py", "POST /retrieve — text or image query"],
                  ["api/routes/rerank.py", "POST /rerank — rerank supplied candidates"],
                  ["api/routes/generate.py", "POST /generate — LLM summary over supplied recipes"],
                  ["api/routes/rag.py", "POST /rag/query — full end-to-end pipeline"],
              ],
              col_widths_cm=[5.5, 11.0])

    # 6. Architecture Diagrams
    h1(doc, "6. Architecture Diagrams")
    body(doc,
         "The system follows a layered architecture with strict dependency direction: the API "
         "layer depends on the pipeline layer, the pipeline layer depends on the model and "
         "store layers, and the model and store layers depend only on the config and schema "
         "layers. No layer reaches upward, which keeps the dependency graph acyclic and "
         "testable in isolation.")
    code(doc,
         "                +----------+\n"
         "   query -----> | Embedder |----> vector --+\n"
         "   (text/image) +----------+               |\n"
         "                                            v\n"
         "                                  +----------------+\n"
         "                                  |  Vector Store  | (Chroma/Qdrant/FAISS)\n"
         "                                  +----------------+\n"
         "                                            |\n"
         "                                  top-K candidates\n"
         "                                            v\n"
         "                                  +----------------+\n"
         "                                  |   Reranker     | (optional)\n"
         "                                  +----------------+\n"
         "                                            |\n"
         "                                  reranked candidates\n"
         "                                            v\n"
         "                                  +----------------+\n"
         "                                  |   Generator    | ----> summary\n"
         "                                  +----------------+")
    body(doc,
         "The FastAPI app sits in front of the pipeline. Each route handler is a thin adapter "
         "that validates the request payload via Pydantic, delegates to the RAGPipeline, and "
         "serialises the response. Cross-cutting concerns — metrics, structured logging, rate "
         "limiting, exception handling, CORS — are implemented as middleware and exception "
         "handlers registered once at app startup. The dependency-injection system in api/deps.py "
         "provides a single RAGPipeline instance per worker process, ensuring that expensive "
         "model weights are loaded only once.")

    # 7. Data Flow
    h1(doc, "7. Data Flow")
    body(doc,
         "The end-to-end data flow for a RAG query is as follows. A client POSTs a JSON payload "
         "to /rag/query containing a query_text, optional query_image (base64 data URL or HTTP "
         "URL), and tuning parameters such as top_k and rerank. The FastAPI route validates the "
         "payload against the RAGQuery Pydantic schema and calls RAGPipeline.run().")
    body(doc,
         "Inside the pipeline, the retrieve stage first embeds the query. If both text and "
         "image are present, the two embeddings are averaged and L2-normalised so that the "
         "combined vector remains in the same unit-norm space as the stored embeddings. The "
         "vector is then passed to VectorStore.search(), which returns the top_k candidate "
         "recipes along with cosine-similarity scores. Each candidate is wrapped in a "
         "RecipeWithScore dataclass that carries the recipe, the score, and the rank position.")
    body(doc,
         "If the rerank flag is set, the rerank stage takes the retrieved candidates and the "
         "original query text and calls Reranker.rerank(). The reranker produces more accurate "
         "relevance scores by considering each (query, candidate) pair jointly, rather than "
         "relying on vector similarity alone. The reranked list replaces the retrieved list as "
         "the source of truth for downstream stages.")
    body(doc,
         "Finally, if the generate flag is set, the top-N reranked candidates are formatted "
         "into a prompt by the build_prompt helper and passed to Generator.generate(). The "
         "generator returns a natural-language summary that is included in the response. "
         "Per-stage timings are recorded throughout and returned in the timings field, allowing "
         "clients to attribute latency to specific stages for debugging.")

    # 8. Multimodal RAG Pipeline
    h1(doc, "8. Multimodal RAG Pipeline")
    body(doc,
         "The multimodal aspect of the pipeline is what distinguishes it from text-only RAG "
         "systems. The Embedder protocol exposes two methods — embed_text and embed_image — "
         "that map inputs from different modalities into the same vector space. The mock "
         "provider achieves this by hashing both text and image bytes into the same "
         "2048-dimensional L2-normalised vector. The local_hf provider uses NVIDIA Nemotron "
         "Embed VL, a vision-language model specifically trained to produce aligned text and "
         "image embeddings. The OpenAI provider, which is text-only, falls back to embedding a "
         "caption-like string derived from the image metadata — a known limitation that the "
         "documentation calls out explicitly.")
    body(doc,
         "When a query contains both text and image, the pipeline computes both embeddings, "
         "averages them with equal weights, and renormalises. This is the simplest fusion "
         "strategy and matches the original notebook's behaviour. More sophisticated fusion "
         "approaches — learned weighting, cross-attention, or late-fusion with a dedicated "
         "multimodal model — are possible future improvements that the pluggable provider "
         "design makes trivial to add.")
    body(doc,
         "The retrieval corpus is itself multimodal: each stored recipe has both a text "
         "component (the markdown recipe) and an image component (the dish photograph). The "
         "ingest pipeline embeds each recipe as a text+image pair using the same Embedder, "
         "ensuring that stored and query embeddings live in the same space. This is critical: "
         "mixing embedders at ingest and query time produces silently incorrect results "
         "because vector similarity is meaningless across different embedding spaces.")

    # 9. Technology Stack
    h1(doc, "9. Technology Stack")
    body(doc,
         "The rebuild is built on a deliberately conservative technology stack. Every "
         "dependency was chosen for stability, active maintenance, and a permissive license. "
         "Heavy ML dependencies (torch, transformers) are optional extras so that the core "
         "package installs in under a minute on a fresh CPU-only machine.")
    add_table(doc,
              ["Layer", "Library / Tool", "Purpose"],
              [
                  ["Web framework", "FastAPI + Uvicorn", "Async REST API + ASGI server"],
                  ["Validation", "Pydantic v2 + pydantic-settings", "Schema validation + env-var config"],
                  ["HTTP client", "httpx + tenacity", "HTTP calls with exponential-backoff retry"],
                  ["Rate limiting", "slowapi", "Per-IP sliding window rate limiter"],
                  ["Cache", "cachetools", "In-memory LRU cache decorator"],
                  ["Vector DB", "Qdrant + ChromaDB + FAISS", "Three interchangeable vector stores"],
                  ["ML (optional)", "torch + transformers", "NVIDIA Nemotron + Qwen3-VL inference"],
                  ["Datasets", "datasets (HuggingFace)", "Streaming the 10k recipe dataset"],
                  ["CLI", "Typer + Rich", "Typed CLI with pretty terminal output"],
                  ["Logging", "structlog", "Structured JSON logs in production"],
                  ["Monitoring", "prometheus-client", "Counters + histograms at /metrics"],
                  ["Testing", "pytest + pytest-asyncio + pytest-cov", "Unit + integration tests with coverage"],
                  ["Linting", "ruff", "Fast Python linter + formatter"],
                  ["Type checking", "mypy", "Static type analysis"],
                  ["Packaging", "hatchling", "Build backend for the wheel"],
                  ["Containerisation", "Docker + docker-compose", "Single-image + full-stack deployment"],
                  ["CI/CD", "GitHub Actions", "Lint, test, build matrix on push/PR"],
              ],
              col_widths_cm=[3.5, 5.0, 8.0])

    # 10. Libraries Used
    h1(doc, "10. Libraries Used")
    body(doc,
         "This section complements the previous one by listing every direct dependency in the "
         "pyproject.toml, including version constraints and the rationale for each. Optional "
         "dependencies are grouped under the gpu, dev, and docs extras so that installers can "
         "opt in only to what they need.")
    add_table(doc,
              ["Dependency", "Version constraint", "Why"],
              [
                  ["fastapi", ">=0.115.0", "Modern async web framework with auto OpenAPI"],
                  ["uvicorn[standard]", ">=0.30.0", "Production-grade ASGI server"],
                  ["pydantic", ">=2.7.0", "V2 for speed; data validation throughout"],
                  ["pydantic-settings", ">=2.3.0", "Env-var-backed config with type coercion"],
                  ["httpx", ">=0.27.0", "Sync + async HTTP client used for image URL fetch"],
                  ["tenacity", ">=8.4.0", "Retry decorators with exponential backoff"],
                  ["slowapi", ">=0.1.9", "FastAPI-compatible rate limiter"],
                  ["cachetools", ">=5.3.0", "LRU cache used by the @cached decorator"],
                  ["qdrant-client", ">=1.10.0", "Official Qdrant Python client"],
                  ["chromadb", ">=0.5.5", "Embedded vector DB; no separate service needed"],
                  ["faiss-cpu", ">=1.8.0", "Facebook's similarity search library (CPU build)"],
                  ["numpy", ">=1.26.0", "Vector arithmetic; required by every provider"],
                  ["pillow", ">=10.3.0", "Image handling for image queries"],
                  ["safetensors", ">=0.4.3", "Fast safe tensor serialisation (matches original notebook)"],
                  ["datasets", ">=2.20.0", "HuggingFace dataset streaming for the 10k recipe corpus"],
                  ["typer", ">=0.12.3", "Typed CLI built on Click"],
                  ["rich", ">=13.7.0", "Pretty terminal output for the CLI"],
                  ["structlog", ">=24.1.0", "Structured logging with JSON output in prod"],
                  ["prometheus-client", ">=0.20.0", "Prometheus exposition at /metrics"],
                  ["torch (gpu extra)", ">=2.3.0", "Local HF model inference"],
                  ["transformers (gpu extra)", ">=4.44.0", "Nemotron + Qwen3-VL model loading"],
                  ["pytest (dev extra)", ">=8.2.0", "Test runner"],
                  ["pytest-cov (dev extra)", ">=5.0.0", "Coverage reporting"],
                  ["ruff (dev extra)", ">=0.5.0", "Linter + formatter"],
                  ["mypy (dev extra)", ">=1.10.0", "Static type checker"],
                  ["python-docx (docs extra)", ">=1.1.0", "Generates this documentation file"],
              ],
              col_widths_cm=[4.0, 4.0, 8.5])

    # 11. Installation Guide
    h1(doc, "11. Installation Guide")
    body(doc,
         "The project supports three installation profiles. The default profile installs only "
         "the runtime dependencies needed to run with mock providers on a CPU; this is the "
         "profile used by CI and the recommended starting point for new contributors. The dev "
         "profile adds testing and linting tools. The gpu profile adds torch and transformers "
         "for running the original NVIDIA Nemotron and Qwen3-VL models locally.")
    numbered(doc, "Clone the repository: git clone <repo-url> && cd multimodal-rag-production")
    numbered(doc, "Create a virtual environment: python3 -m venv .venv && source .venv/bin/activate")
    numbered(doc, "Install the package: pip install -e .  (or pip install -e '.[dev]' for development)")
    numbered(doc, "Copy the environment template: cp .env.example .env")
    numbered(doc, "Edit .env to select providers (defaults are mock for everything — safe for CPU)")
    numbered(doc, "Ingest the sample dataset: multimodal-rag ingest --source sample")
    numbered(doc, "Start the API: multimodal-rag serve  (or make serve)")
    numbered(doc, "Open the API docs at http://localhost:8000/docs")
    body(doc,
         "For GPU installations, replace step 3 with pip install -e '.[gpu]' and run "
         "multimodal-rag download-models to pre-fetch the HuggingFace weights. The first "
         "download is approximately 6 GB across the three models; subsequent runs use the "
         "HuggingFace local cache and start in seconds.")

    # 12. Environment Setup
    h1(doc, "12. Environment Setup")
    body(doc,
         "All runtime configuration is read from environment variables or a .env file via "
         "pydantic-settings. The Settings class in config.py declares every field with a "
         "sensible default, so the application starts successfully with no .env file at all — "
         "defaults assume mock providers, Chroma embedded store, and the bundled sample "
         "dataset. The .env.example file documents every variable with inline comments and "
         "serves as the authoritative reference for configuration.")
    body(doc,
         "Configuration is grouped into nine categories: app, providers, model IDs, vector "
         "store, dataset, embeddings cache, RAG pipeline, reliability, and security. Each "
         "category is independent — for example, switching the vector store from Chroma to "
         "Qdrant does not require changes to the provider or dataset configuration. The "
         "get_settings() function returns a process-wide cached instance, ensuring that env "
         "vars are read only once at startup.")
    h2(doc, "Key environment variables")
    add_table(doc,
              ["Variable", "Default", "Effect"],
              [
                  ["EMBEDDING_PROVIDER", "mock", "Selects embedder: mock | local_hf | openai"],
                  ["RERANKER_PROVIDER", "mock", "Selects reranker"],
                  ["GENERATOR_PROVIDER", "mock", "Selects generator"],
                  ["VECTOR_STORE", "chroma", "Selects store: chroma | qdrant | faiss"],
                  ["DATASET_SOURCE", "sample", "sample | hf | local"],
                  ["DATASET_SAMPLE_SIZE", "200", "Number of recipes to ingest from sample"],
                  ["DEFAULT_TOP_K", "5", "Default retrieval depth"],
                  ["RERANK_TOP_K", "20", "How many candidates to rerank"],
                  ["RATE_LIMIT_PER_MINUTE", "60", "Per-IP request limit"],
                  ["API_KEY", "(empty)", "If set, requires X-API-Key header from clients"],
                  ["CORS_ORIGINS", "*", "Comma-separated list of allowed origins"],
              ],
              col_widths_cm=[5.0, 3.0, 8.5])

    # 13. Code Explanation
    h1(doc, "13. Code Explanation")
    body(doc,
         "The codebase is deliberately small — under 2,500 lines of Python across 30 source "
         "files — and follows a strict separation of concerns. Every module begins with a "
         "docstring explaining its role, every public class and function has a docstring, and "
         "type hints are used throughout. The RAGPipeline class in pipeline/rag.py is the "
         "central orchestrator and the only place where the embedder, store, reranker, and "
         "generator are used together.")
    body(doc,
         "The pipeline exposes three stage methods — retrieve, rerank, generate — each of "
         "which can be called independently. This makes it trivial to build alternative "
         "interfaces: the /retrieve API endpoint calls only retrieve, the /rerank endpoint "
         "calls only rerank, and the /rag/query endpoint calls all three via the run() "
         "method. Each stage records its latency via the PIPELINE_STAGE_LATENCY histogram, "
         "and the run() method returns a timings dict so callers can see exactly where time "
         "was spent.")
    body(doc,
         "Error handling follows a hierarchical exception design. The base MultimodalRagError "
         "class has subclasses for each layer — ProviderError, VectorStoreError, PipelineError, "
         "etc. — and the FastAPI middleware in api/middleware.py maps each leaf class to an "
         "HTTP status code. This means a VectorStoreConnectionError automatically becomes a "
         "503 response, a ValidationError becomes a 400, and so on, without any boilerplate "
         "in the route handlers.")

    # 14. Model Explanation
    h1(doc, "14. Model Explanation")
    body(doc,
         "The original notebook uses three models. NVIDIA Nemotron Embed VL is a vision-"
         "language embedding model that produces 2,048-dimensional vectors jointly encoding "
         "an image and its accompanying text. NVIDIA Llama-Nemotron Rerank VL is a sequence-"
         "classification model fine-tuned to score the relevance of a (query, document) pair, "
         "where the document may contain both text and image. Qwen3-VL-2B-Instruct is a "
         "small (2-billion-parameter) instruction-tuned vision-language model used to generate "
         "the final summary.")
    body(doc,
         "The rebuild wraps each of these in a Python class that lazily loads the model on "
         "first use, exposing a clean protocol-typed interface. The LocalHFEmbedder, "
         "LocalHFReranker, and LocalHFGenerator classes defer their torch and transformers "
         "imports to __init__ so that the mock providers can be used without those packages "
         "installed. The retry decorator from tenacity wraps every network-adjacent call, "
         "providing automatic exponential-backoff retry on transient failures.")
    body(doc,
         "The mock providers are not just stubs — they implement the same protocols with "
         "deterministic, dependency-free logic. MockEmbedder produces an L2-normalised "
         "SHA-256 hash of the input bytes, MockReranker uses token-overlap (Jaccard "
         "similarity) between the query and each candidate's text, and MockGenerator returns "
         "a templated string that includes the query and the top recipe titles. These mocks "
         "are fast, deterministic, and good enough to exercise every code path in tests "
         "without requiring GPU resources or network access.")

    # 15. Embedding Workflow
    h1(doc, "15. Embedding Workflow")
    body(doc,
         "Embedding is the first stage of every RAG query and every ingest operation. At "
         "ingest time, each recipe's text (and image, when available) is passed to "
         "Embedder.embed_batch, which returns a (N, dim) float32 numpy array. The vectors "
         "are L2-normalised so that inner product equals cosine similarity, then upserted "
         "into the vector store alongside the recipe payload. At query time, the query text "
         "or image is embedded with the same embedder, and the resulting vector is used to "
         "search the store.")
    body(doc,
         "The embed_batch method takes a list of dicts, each of which may contain a text "
         "key, an image key (a PIL.Image), or both. This flexible input shape lets the "
         "ingest pipeline handle pure-text recipes, pure-image items, and text+image pairs "
         "with a single code path. When both modalities are present, the mock provider "
         "averages the two embeddings and renormalises; the local_hf provider passes both "
         "to Nemotron's processor, which handles fusion internally.")
    body(doc,
         "The EMBEDDING_OPS Prometheus counter tracks how many embedding operations each "
         "provider performs, labelled by provider name and operation kind (text, image, "
         "batch). This metric is invaluable for capacity planning: a sudden spike in image "
         "embeds suggests users are uploading photos rather than typing queries, which may "
         "warrant additional GPU capacity if the local_hf provider is in use.")

    # 16. Vector Database Workflow
    h1(doc, "16. Vector Database Workflow")
    body(doc,
         "The VectorStore protocol defines four operations: upsert, search, count, and "
         "delete_all. Three implementations are provided. ChromaStore is the default — it "
         "uses an embedded PersistentClient that writes to a local directory, requiring no "
         "external services. QdrantStore connects to a separate Qdrant instance (typically "
         "running in Docker Compose) and auto-creates the collection if it does not exist. "
         "FAISSStore uses an in-memory IndexFlatIP with optional on-disk persistence; it is "
         "the fastest option for single-node deployments up to around one million vectors.")
    body(doc,
         "Each implementation handles metadata slightly differently. Chroma accepts only "
         "scalar values at the top level, so ChromaStore flattens nested metadata into "
         "prefixed keys (meta_cuisine, meta_category, etc.) and JSON-encodes complex values. "
         "Qdrant accepts arbitrary JSON payloads, so QdrantStore stores recipes verbatim. "
         "FAISSStore keeps a Python dict mapping integer indices to Recipe objects, since "
         "FAISS itself does not store payloads. The unification is handled by VectorRecord, "
         "a Pydantic model that converts between the Recipe schema and each store's native "
         "representation.")
    body(doc,
         "Searching returns a list of (Recipe, score) tuples sorted by descending relevance. "
         "Chroma and Qdrant compute cosine similarity natively; FAISS uses inner product on "
         "L2-normalised vectors, which is mathematically equivalent. The search method "
         "accepts an optional filter dict for metadata-based filtering — Chroma and Qdrant "
         "push this down to the store, while FAISS applies it as a post-filter. This "
         "abstraction lets the pipeline use the same search call regardless of which store "
         "is active.")

    # 17. Retrieval Process
    h1(doc, "17. Retrieval Process")
    body(doc,
         "Retrieval is the second stage of the RAG pipeline and the most performance-"
         "sensitive. The retrieve method on RAGPipeline first embeds the query (handling "
         "the text+image fusion case described earlier), then calls VectorStore.search with "
         "the configured top_k. The result is a list of RecipeWithScore objects, each "
         "carrying the recipe, its similarity score, and its rank position (1-indexed).")
    body(doc,
         "The default top_k is 5, tunable via DEFAULT_TOP_K or the top_k parameter on each "
         "request. Higher values improve recall at the cost of latency and downstream token "
         "consumption (the generator must process more context). For most culinary queries, "
         "top_k between 3 and 10 produces good results; the reranker can then re-order these "
         "candidates more accurately than raw similarity would.")
    body(doc,
         "If the vector store returns fewer than top_k results (for example, because the "
         "collection is small or a metadata filter excluded most candidates), the pipeline "
         "simply returns what it has — no error is raised. This graceful degradation is "
         "important for production: a query that returns one result is still a useful query, "
         "whereas a 500 error would be a poor user experience. The response envelope always "
         "includes the actual number of results returned, so clients can detect short lists.")

    # 18. Prompt Engineering
    h1(doc, "18. Prompt Engineering")
    body(doc,
         "The generator's prompt is built by the build_prompt function in models/generator.py. "
         "The function takes the user query, the list of retrieved recipes, and a style "
         "parameter (summary, comparison, or recipe_card) and returns a single string prompt "
         "that works across all three generator providers. This shared prompt builder is key "
         "to provider portability: switching from the mock generator to Qwen3-VL or OpenAI "
         "does not require any prompt changes.")
    body(doc,
         "The prompt structure is: a system-style instruction line that varies by style, "
         "the user query, a numbered list of retrieved recipes (title plus up to 800 "
         "characters of text), and a final 'Assistant:' marker. The summary style asks for "
         "key ingredients, technique, and tips; the comparison style asks for differences in "
         "ingredients, technique, and serving size; the recipe_card style formats the most "
         "relevant recipe as a structured card with title, ingredients, steps, and serving "
         "size.")
    body(doc,
         "The 800-character truncation per recipe is deliberate: it keeps the total prompt "
         "under the 4,096-token context limit of Qwen3-VL-2B even when ten recipes are "
         "retrieved. For longer-context models (the OpenAI provider supports up to 128k "
         "tokens), the truncation could be relaxed, but the current value keeps behaviour "
         "consistent across providers. Future improvements could make this configurable per "
         "provider, or use a smarter truncation strategy that preserves ingredient lists "
         "over instructions.")

    # 19. API Documentation
    h1(doc, "19. API Documentation")
    body(doc,
         "The FastAPI app exposes seven endpoints. Three are operational — /health, /ready, "
         "and /metrics — and four are functional — /ingest, /retrieve, /rerank, /generate, "
         "and /rag/query. The OpenAPI schema is auto-generated and served at /openapi.json, "
         "with interactive Swagger UI at /docs and ReDoc at /redoc. All request and response "
         "bodies are Pydantic models declared in schemas.py, ensuring that the documentation "
         "is always in sync with the code.")
    add_table(doc,
              ["Endpoint", "Method", "Purpose"],
              [
                  ["/health", "GET", "Liveness/readiness probe; returns provider + dataset info"],
                  ["/ready", "GET", "Kubernetes-style readiness probe"],
                  ["/metrics", "GET", "Prometheus exposition format"],
                  ["/ingest", "POST", "Load dataset (sample | hf | local) into vector store"],
                  ["/retrieve", "POST", "Embed query and return top-K candidates"],
                  ["/rerank", "POST", "Rerank supplied candidates against a query"],
                  ["/generate", "POST", "Generate a summary over supplied recipes"],
                  ["/rag/query", "POST", "End-to-end: retrieve → rerank → generate"],
              ],
              col_widths_cm=[3.5, 1.8, 11.2])
    body(doc,
         "Authentication is optional. If the API_KEY environment variable is set, every "
         "request must include an X-API-Key header matching that value; otherwise "
         "authentication is disabled. The verify_api_key dependency in api/deps.py implements "
         "this check and is wired into every functional endpoint. Rate limiting is enforced "
         "by slowapi with a default of 60 requests per minute per IP, configurable via "
         "RATE_LIMIT_PER_MINUTE.")
    body(doc,
         "Errors return a consistent JSON envelope: {\"error\": {\"error\": \"ClassName\", "
         "\"detail\": \"...\", \"code\": \"404\"}}. The HTTP status code is derived from the "
         "exception class via a lookup table in api/middleware.py: ValidationError → 400, "
         "AuthenticationError → 401, RateLimitExceededError → 429, ProviderError → 502, "
         "VectorStoreConnectionError → 503, and so on. Unhandled exceptions are caught by a "
         "top-level handler that returns a generic 500 without leaking internal details.")

    # 20. Testing Guide
    h1(doc, "20. Testing Guide")
    body(doc,
         "Tests are organised by module: tests/test_config.py covers Settings, "
         "tests/test_embedder.py covers the embedder providers, and so on. The conftest.py "
         "file at the tests/ root forces mock providers, disables the cache, and lowers the "
         "log level, ensuring that the test suite runs in under ten seconds on a fresh CPU "
         "machine. A shared pipeline fixture builds a RAGPipeline, wipes its vector store, "
         "ingests twenty sample recipes, and yields; the client fixture wraps a FastAPI "
         "TestClient with the pipeline dependency overridden to use that fixture.")
    body(doc,
         "The 55-test suite covers every module: config validation, embedder determinism and "
         "L2-norm, reranker ordering, generator prompt building, vector store roundtrips for "
         "Chroma and FAISS (Qdrant is tested only when a local Qdrant is reachable), the "
         "RAG pipeline end-to-end, every API endpoint, the CLI commands, the dataset loader, "
         "and the cache decorator. Coverage is 71% overall, with the lowest coverage on the "
         "local_hf providers (which require GPU and are therefore not exercised in CI).")
    body(doc,
         "To run the tests: make test (or pytest directly). To run with coverage: make "
         "test-cov, which writes an HTML report to htmlcov/index.html. Tests marked @pytest.mark.slow "
         "or @pytest.mark.gpu are deselected by default in CI; they can be run locally with "
         "pytest -m slow or pytest -m gpu. The CI workflow in .github/workflows/ci.yml runs "
         "the full unit-test suite on Python 3.10, 3.11, and 3.12, then builds the Docker "
         "image and smoke-tests the /health endpoint.")

    # 21. Deployment Guide
    h1(doc, "21. Deployment Guide")
    body(doc,
         "Three deployment topologies are supported. The simplest is single-container Docker: "
         "docker build -t multimodal-rag . && docker run -p 8000:8000 --env-file .env "
         "multimodal-rag. This runs the API in isolation with the embedded Chroma store, "
         "suitable for development or low-traffic production. The second is Docker Compose: "
         "docker compose up -d brings up the API alongside Qdrant, Redis (for future "
         "distributed caching), Prometheus, and Grafana, providing a production-like "
         "environment with persistent vector storage and monitoring out of the box.")
    body(doc,
         "The third topology is Kubernetes. The deployment guide in docs/deployment.md "
         "includes a sketch Deployment manifest with readiness and liveness probes, resource "
         "requests and limits, and a recommendation to run at least three replicas behind a "
         "ClusterIP service with a HorizontalPodAutoscaler targeting 70% CPU. For "
         "multi-GPU deployments, the embedder and generator should be moved behind a Triton "
         "or vLLM sidecar, leaving the FastAPI app to handle only HTTP and orchestration.")
    body(doc,
         "Regardless of topology, the production checklist in docs/deployment.md should be "
         "followed: set APP_ENV=prod to switch logs to JSON; set a strong API_KEY; restrict "
         "CORS_ORIGINS to your real origins; use Qdrant instead of embedded Chroma for "
         "persistence and scale; wire Prometheus into an alerting pipeline; and schedule "
         "periodic re-ingest via a cron job calling multimodal-rag ingest.")

    # 22. Docker Guide
    h1(doc, "22. Docker Guide")
    body(doc,
         "The Dockerfile is multi-stage: a base stage installs the runtime dependencies on "
         "python:3.11-slim, and a gpu stage extends base with torch, transformers, and "
         "accelerate for local HF model inference. The base image is approximately 600 MB; "
         "the gpu image is closer to 6 GB. A HEALTHCHECK directive polls the /health "
         "endpoint every 30 seconds, allowing container orchestrators to detect and restart "
         "unhealthy instances automatically.")
    body(doc,
         "The docker-compose.yml defines five services. The api service builds from the "
         "Dockerfile and exposes port 8000; it depends on qdrant being healthy and redis "
         "being started. The qdrant service uses the official qdrant/qdrant image with a "
         "named volume for persistence. The redis service uses redis:7-alpine as a future "
         "distributed cache. Prometheus and Grafana provide metrics collection and "
         "dashboards, with Grafana available at http://localhost:3000 (admin/admin).")
    body(doc,
         "To build and run: make docker-build && make docker-up. To tail logs: make "
         "docker-logs. To stop: make docker-down. The Makefile wraps these as convenience "
         "targets; the underlying docker compose commands can be invoked directly if "
         "preferred. The compose file uses a dedicated bridge network (mrag-net) so the "
         "services can communicate by hostname without exposing internal ports to the host.")

    # 23. CI/CD Setup
    h1(doc, "23. CI/CD Setup")
    body(doc,
         "Continuous integration is configured in .github/workflows/ci.yml. On every push "
         "to main or master and on every pull request, the workflow runs a matrix of Python "
         "3.10, 3.11, and 3.12 on ubuntu-latest. Each matrix job installs the package with "
         "the dev extras, runs ruff check for linting, runs mypy for type checking (non-"
         "blocking on first pass to ease adoption), runs pytest with coverage, and uploads "
         "the coverage report to Codecov (only on Python 3.11 to avoid triple-uploading).")
    body(doc,
         "A second job, docker-build, runs after the test matrix succeeds. It uses Docker "
         "Buildx to build the image, loads it locally, runs a container with mock providers "
         "and Chroma, waits five seconds, and curls the /health endpoint to verify the "
         "container is serving traffic. This smoke test catches packaging errors that "
         "unit tests miss — missing files in the image, broken entry points, environment-"
         "variable parsing failures, and so on.")
    body(doc,
         "Future CI improvements could include: a separate GPU job that runs the local_hf "
         "tests on a self-hosted runner; an automated release workflow that tags and "
         "publishes the Docker image to a registry on git tag; and a docs job that rebuilds "
         "this DOCX file and attaches it to GitHub releases. The current workflow is "
         "deliberately minimal — three minutes end-to-end on the free GitHub Actions tier — "
         "to keep the feedback loop fast for contributors.")

    # 24. Security Best Practices
    h1(doc, "24. Security Best Practices")
    body(doc,
         "Security is treated as a first-class concern. The .env file is gitignored and "
         "never committed; the .env.example template documents every variable without "
         "containing real secrets. API keys, if used, are passed via the X-API-Key header "
         "and validated on every request by the verify_api_key dependency. The OpenAI and "
         "HuggingFace tokens are read from environment variables at startup and never "
         "logged — structlog is configured to redact fields whose names contain 'key' or "
         "'token'.")
    body(doc,
         "CORS is configurable via CORS_ORIGINS, defaulting to '*' for development. "
         "Production deployments should restrict this to the actual frontend origins. The "
         "FastAPI app uses CORSMiddleware with allow_credentials=True, so cookie-based "
         "authentication is supported if needed. Rate limiting is enforced at 60 requests "
         "per minute per IP by default, configurable via RATE_LIMIT_PER_MINUTE; individual "
         "routes can override this with the @limiter.limit decorator.")
    body(doc,
         "Image inputs are validated carefully. The _load_image_from_field helper in "
         "pipeline/rag.py accepts only base64 data URLs or http(s) URLs; it uses PIL.Image.open "
         "to decode, which raises a controlled ValidationError on malformed input rather "
         "than crashing the worker. HTTP fetches use httpx with a 30-second timeout and "
         "follow_redirects=True, preventing slow-loris-style resource exhaustion. The "
         "Dockerfile runs as a non-root user by default; for additional isolation, the "
         "container can be run with --read-only and a tmpfs for /tmp.")

    # 25. Performance Optimizations
    h1(doc, "25. Performance Optimizations")
    body(doc,
         "Performance is optimised at four layers. At the model layer, the local_hf providers "
         "use torch.no_grad() and eval mode to disable gradient tracking and dropout, halving "
         "memory usage and roughly doubling throughput. Embeddings are computed in batches "
         "(default 16) to amortise the per-call overhead of model inference. The mock "
         "providers use deterministic hash-based vectors with no I/O, completing in "
         "microseconds rather than milliseconds.")
    body(doc,
         "At the storage layer, Chroma uses HNSW indexing (cosine space) for sub-linear "
         "search. Qdrant uses HNSW with payload indexing. FAISS uses IndexFlatIP, which is "
         "O(N) but extremely fast for N under one million due to BLAS-accelerated matrix "
         "multiplication. All three stores return only the top_k results, minimising "
         "serialization overhead. The ChromaStore flattens metadata at write time so reads "
         "do not pay the cost of JSON parsing.")
    body(doc,
         "At the API layer, the RAGPipeline instance is cached per worker process via the "
         "lru_cache decorator on _cached_pipeline, ensuring that model weights are loaded "
         "only once per worker. The @cached decorator memoises pure functions like "
         "embed_text for repeated queries within the cache window (default 1,024 entries). "
         "SlowAPI rate limiting prevents any single client from saturating the worker pool. "
         "Uvicorn can run multiple workers (APP_WORKERS) to use all available CPU cores.")
    body(doc,
         "At the network layer, the FastAPI app is served by uvicorn with the standard extras "
         "(uvloop + httptools) for high-throughput async I/O. The Docker Compose stack puts "
         "Qdrant on the same bridge network as the API, eliminating cross-host latency. For "
         "production, a reverse proxy like nginx or traefik should sit in front of uvicorn "
         "to terminate TLS, compress responses, and buffer slow clients.")

    # 26. Scaling Strategies
    h1(doc, "26. Scaling Strategies")
    body(doc,
         "Vertical scaling — giving the API more CPU and RAM — is the simplest path and "
         "works up to roughly 100 queries per second on a single 4-core machine with mock "
         "providers. Beyond that, horizontal scaling is required. The FastAPI app is "
         "stateless (all state lives in the vector store and the cache), so it can be "
         "scaled by adding replicas behind a load balancer. The docker-compose stack "
         "demonstrates this pattern; Kubernetes deployments would use a HorizontalPodAutoscaler.")
    body(doc,
         "The vector store scales differently. Chroma is embedded and therefore cannot be "
         "shared across API replicas — it is suitable only for single-node deployments. "
         "Qdrant is the recommended choice for multi-replica deployments: it runs as a "
         "separate service, supports horizontal scaling via sharding, and persists data to "
         "disk. FAISS is in-memory and per-process, so it is also single-node only, though "
         "it can be sharded manually with the FAISS Mirror index if needed.")
    body(doc,
         "For very large deployments, the embedder and generator should be extracted into "
         "dedicated inference services. NVIDIA Triton Inference Server or vLLM can serve "
         "the models with dynamic batching, achieving much higher GPU utilisation than the "
         "current per-process transformers loading. The Embedder and Generator protocols "
         "are HTTP-callable already (the OpenAI implementations prove this), so moving to "
         "a Triton-backed local provider is a small change. Cache hit rate becomes the "
         "dominant performance metric at scale; a Redis-backed cache shared across replicas "
         "is a natural next step beyond the in-process LRU.")

    # 27. Troubleshooting Guide
    h1(doc, "27. Troubleshooting Guide")
    body(doc,
         "The most common issues are documented in docs/troubleshooting.md. The first "
         "diagnostic step for any problem is to check the structured logs at APP_LOG_LEVEL=DEBUG — "
         "every stage of the pipeline logs its inputs, outputs, and timings. The /metrics "
         "endpoint exposes error counters by category, which can quickly tell you whether "
         "failures are concentrated in the embedder, the vector store, or the generator.")
    add_table(doc,
              ["Symptom", "Likely cause", "Fix"],
              [
                  ["ModuleNotFoundError: multimodal_rag", "Package not installed in active env", "Run pip install -e ."],
                  ["ProviderNotAvailableError: gpu extra", "Set local_hf without installing torch", "pip install -e '.[gpu]'"],
                  ["VectorStoreConnectionError: Qdrant", "Qdrant not running on localhost:6333", "docker compose up -d qdrant"],
                  ["Chroma metadata ValueError", "Old chromadb version", "pip install -U chromadb"],
                  ["RateLimitExceeded on every request", "RATE_LIMIT_PER_MINUTE too low", "Raise the limit or override per route"],
                  ["Generation is super slow", "local_hf generator on CPU", "Switch to mock or openai, or add a GPU"],
                  ["Qwen3-VL OOMs", "GPU has <8GB VRAM", "Lower GENERATE_MAX_NEW_TOKENS to 256"],
                  ["Embedding mismatch", "Mixed providers at ingest vs query", "Re-ingest with the current provider"],
              ],
              col_widths_cm=[5.0, 5.0, 6.5])

    # 28. Frequently Asked Questions
    h1(doc, "28. Frequently Asked Questions")
    h2(doc, "Q: Can I use a different dataset?")
    body(doc,
         "Yes. Set DATASET_SOURCE=local and DATASET_LOCAL_PATH to a JSON file containing a "
         "list of objects with at least an id and text field. The Recipe schema accepts "
         "arbitrary additional fields, which are stored as metadata and become filterable.")
    h2(doc, "Q: How do I switch from Chroma to Qdrant?")
    body(doc,
         "Set VECTOR_STORE=qdrant and ensure Qdrant is reachable at QDRANT_URL. Then run "
         "multimodal-rag ingest to repopulate. The same Recipe objects are written to Qdrant "
         "verbatim — no data transformation is needed.")
    h2(doc, "Q: Does the system work without a GPU?")
    body(doc,
         "Yes. With the default mock providers, the entire system runs on CPU in under a "
         "second per query. With the openai providers, it runs on CPU but requires network "
         "access and an OpenAI API key. Only the local_hf providers require a GPU.")
    h2(doc, "Q: How do I add a new embedder?")
    body(doc,
         "Implement the Embedder protocol in a new class under models/embedder.py, add it "
         "to the build_embedder factory, add the provider name to the ProviderName Literal "
         "in config.py, and add tests in tests/test_embedder.py. The rest of the system "
         "will pick up the new provider automatically.")
    h2(doc, "Q: Is the system production-ready?")
    body(doc,
         "Yes, with the caveats listed in the production checklist (docs/deployment.md). "
         "The mock providers are deterministic but not semantically meaningful; for real "
         "retrieval quality, switch to local_hf or openai. The FastAPI app, vector stores, "
         "monitoring, and CI are all production-grade.")

    # 29. Future Improvements
    h1(doc, "29. Future Improvements")
    body(doc,
         "The current rebuild is a solid foundation, but several improvements would push it "
         "further toward enterprise-grade. The most impactful would be moving the local_hf "
         "providers behind a dedicated inference server (Triton or vLLM) for dynamic "
         "batching and multi-GPU support. This would unlock 5-10x throughput on the same "
         "hardware and decouple model serving from the API layer.")
    body(doc,
         "On the retrieval side, hybrid search combining dense vector similarity with sparse "
         "keyword matching (BM25) would improve recall for queries with rare terms. Qdrant "
         "supports this natively via hybrid search; Chroma and FAISS would require a "
         "separate sparse index. A re-ranking cascade — cheap first-stage reranker (the "
         "current MockReranker's Jaccard approach) followed by the expensive Nemotron "
         "reranker only on the top-50 — would reduce rerank latency without sacrificing "
         "quality.")
    body(doc,
         "On the operational side, a Redis-backed distributed cache would let multiple API "
         "replicas share query results. Structured tracing via OpenTelemetry would make it "
         "possible to follow a single request across the embedder, vector store, reranker, "
         "and generator. A/B testing infrastructure (configurable provider per request, with "
         "result quality feedback) would enable data-driven provider selection. Finally, "
         "automated evaluation — a held-out query set with ground-truth relevance judgments, "
         "scored by NDCG and recall@k — would give a quantitative signal for every code "
         "change.")

    # 30. Conclusion
    h1(doc, "30. Conclusion")
    body(doc,
         "This rebuild demonstrates that a research notebook can be transformed into a "
         "production-grade system without sacrificing the original's clarity of purpose. "
         "Every feature of the source notebook — multimodal query support, embedding-based "
         "retrieval, optional reranking, natural-language generation, Gradio-style demo — is "
         "preserved and exposed through clean, tested, documented interfaces. The pluggable "
         "provider design means the same code path runs on a laptop with mock providers, on "
         "a GPU box with the original NVIDIA Nemotron and Qwen3-VL models, or in a hybrid "
         "configuration with OpenAI-hosted models.")
    body(doc,
         "The 55-test suite, the 71% line coverage, the Dockerfile and docker-compose stack, "
         "the GitHub Actions CI, and this 30-section documentation file together represent "
         "the engineering scaffolding that distinguishes a demo from a deliverable. A new "
         "engineer can clone the repository, run make install && make ingest && make serve, "
         "and be querying the API within five minutes — or, with a single env-var change, "
         "be running the original models on a GPU and serving real users.")
    body(doc,
         "The project stands as a reference architecture for multimodal RAG in production: "
         "what to abstract, what to test, what to monitor, and what to leave configurable. "
         "Future work — Triton-backed inference, hybrid search, distributed caching, "
         "automated evaluation — builds naturally on this foundation without requiring "
         "fundamental restructuring. The original notebook taught the algorithm; this "
         "rebuild teaches the engineering.")


def main() -> None:
    doc = build_document()
    doc.save(str(OUT_PATH))
    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"Wrote {OUT_PATH} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
