"""Typer CLI for the multimodal-rag package.

Commands:
* ``serve``          — start the FastAPI server (uvicorn)
* ``ingest``         — load + index a dataset
* ``query``          — query the index from the terminal
* ``download-models``— pre-fetch HuggingFace weights (for local_hf providers)
* ``info``           — print effective configuration
* ``reset``          — wipe the vector store
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from multimodal_rag._version import __version__
from multimodal_rag.config import get_settings

app = typer.Typer(
    name="multimodal-rag",
    help="Multimodal RAG production CLI",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


@app.command()
def info() -> None:
    """Print effective configuration."""
    s = get_settings()
    tbl = Table(title=f"multimodal-rag v{__version__}", show_header=False)
    tbl.add_column("key", style="cyan")
    tbl.add_column("value")
    for k, v in s.model_dump().items():
        # Mask secrets
        if "key" in k.lower() and v:
            v = "***"
        tbl.add_row(k, str(v))
    console.print(tbl)


@app.command()
def serve(
    host: str = typer.Option(None, help="Host to bind (default: settings)"),
    port: int = typer.Option(None, help="Port (default: settings)"),
    workers: int = typer.Option(None, help="uvicorn workers (default: settings)"),
    reload: bool = typer.Option(False, "--reload", help="Auto-reload on file changes"),
) -> None:
    """Start the FastAPI server with uvicorn."""
    import uvicorn

    s = get_settings()
    uvicorn.run(
        "multimodal_rag.app:app",
        host=host or s.app_host,
        port=port or s.app_port,
        workers=workers or s.app_workers,
        reload=reload,
        log_level=s.app_log_level.lower(),
    )


@app.command()
def ingest(
    source: str = typer.Option("sample", help="sample | hf | local"),
    limit: Optional[int] = typer.Option(None, help="Max records to ingest"),
) -> None:
    """Ingest a dataset into the vector store."""
    from multimodal_rag.pipeline import build_rag_pipeline
    from multimodal_rag.data import build_dataset_loader

    pipeline = build_rag_pipeline()
    loader = build_dataset_loader()
    console.print(f"[cyan]Loading dataset[/cyan] source={source} limit={limit}")
    recipes = loader.load(source=source, limit=limit)
    console.print(f"[cyan]Ingesting[/cyan] {len(recipes)} recipes…")
    n = pipeline.ingest(recipes)
    console.print(f"[green]Done.[/green] ingested={n} store={pipeline.store.name}")


@app.command()
def query(
    text: Optional[str] = typer.Option(None, "--text", "-t", help="Text query"),
    image: Optional[str] = typer.Option(None, "--image", "-i", help="Image path or URL"),
    top_k: int = typer.Option(5, help="Top-K results"),
    rerank: bool = typer.Option(True, help="Run reranker"),
    generate: bool = typer.Option(True, help="Run generator"),
    style: str = typer.Option("summary", help="summary | comparison | recipe_card"),
) -> None:
    """Run a RAG query against the indexed dataset."""
    from multimodal_rag.pipeline import build_rag_pipeline
    from PIL import Image as PILImage

    if not text and not image:
        console.print("[red]Provide --text and/or --image[/red]")
        raise typer.Exit(2)

    img = None
    if image:
        img = PILImage.open(image)

    pipeline = build_rag_pipeline()
    result = pipeline.run(
        query_text=text,
        query_image=img,
        top_k=top_k,
        rerank=rerank,
        generate=generate,
        generate_style=style,
    )

    console.print("[bold cyan]Retrieved[/bold cyan]")
    for r in result["retrieved"]:
        console.print(f"  {r.rank}. {r.recipe.title}  (score={r.score:.4f})")

    if result["reranked"]:
        console.print("[bold cyan]Reranked[/bold cyan]")
        for r in result["reranked"]:
            console.print(f"  {r.rank}. {r.recipe.title}  (score={r.score:.4f})")

    if result["summary"]:
        console.print("[bold cyan]Summary[/bold cyan]")
        console.print(result["summary"])

    console.print(f"[dim]timings: {json.dumps(result['timings'], indent=2)}[/dim]")


@app.command()
def download_models() -> None:
    """Pre-fetch HuggingFace model weights (only needed for local_hf providers)."""
    s = get_settings()
    if not any(
        p == "local_hf"
        for p in (s.embedding_provider, s.reranker_provider, s.generator_provider)
    ):
        console.print(
            "[yellow]No local_hf providers enabled — nothing to download.[/yellow]"
        )
        return
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        console.print("[red]huggingface_hub not installed[/red]")
        raise typer.Exit(1)

    for model_id in (s.embedding_model_id, s.reranker_model_id, s.generator_model_id):
        console.print(f"[cyan]Downloading[/cyan] {model_id}…")
        snapshot_download(repo_id=model_id, token=s.hf_token or None)
    console.print("[green]All models cached.[/green]")


@app.command()
def reset() -> None:
    """Delete every record from the vector store."""
    from multimodal_rag.stores import build_vector_store

    store = build_vector_store()
    n = store.delete_all()
    console.print(f"[green]Deleted {n} records from {store.name}.[/green]")


if __name__ == "__main__":
    app()
