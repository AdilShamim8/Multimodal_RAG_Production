# `data/` directory

This directory holds runtime data and is **never** committed to git
(see `.gitignore`).

## Contents

| Path                          | Purpose                                         |
|-------------------------------|-------------------------------------------------|
| `sample_recipes.json`         | Bundled 200-recipe sample (committed in `src/multimodal_rag/data/`) |
| `chroma/`                     | ChromaDB persistence (auto-created on first ingest) |
| `faiss/index.faiss`           | FAISS on-disk index                             |
| `images/`                     | Downloaded recipe images (HF source)            |
| `embeddings.safetensors`      | Cached embeddings (for HF source, optional)     |
| `prometheus/`                 | Prometheus multiprocess directory               |

## Regenerating the sample dataset

```bash
python scripts/build_sample_dataset.py
cp data/sample_recipes.json src/multimodal_rag/data/sample_recipes.json
```

## Pulling the full HuggingFace dataset

```bash
multimodal-rag ingest --source hf --limit 10096
```

Requires network access to `huggingface.co` and ~2 GB free disk.
