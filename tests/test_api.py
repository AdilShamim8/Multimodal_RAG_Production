"""API integration tests."""

from __future__ import annotations

import base64
import io


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ("ok", "degraded")
    assert "version" in data
    assert "providers" in data


def test_root_redirects_to_docs(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307)


def test_openapi_schema(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    assert "/health" in paths
    assert "/rag/query" in paths


def test_retrieve_text(client):
    r = client.post("/retrieve", json={"query_text": "tomato", "top_k": 3})
    assert r.status_code == 200
    data = r.json()
    assert data["query_kind"] == "text"
    assert len(data["results"]) == 3


def test_retrieve_image(client):
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (32, 32), color=(255, 0, 0)).save(buf, format="PNG")
    data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    r = client.post("/retrieve", json={"query_image": data_url, "top_k": 2})
    assert r.status_code == 200
    assert r.json()["query_kind"] == "image"


def test_retrieve_requires_query(client):
    r = client.post("/retrieve", json={})
    assert r.status_code == 400


def test_rerank(client):
    # First retrieve to get candidates
    r = client.post("/retrieve", json={"query_text": "tomato", "top_k": 3})
    candidates = r.json()["results"]
    # Rerank expects Recipe objects (not RecipeWithScore)
    recipe_payload = [{"id": c["recipe"]["id"], "title": c["recipe"]["title"],
                       "text": c["recipe"]["text"]} for c in candidates]
    r = client.post("/rerank", json={"query_text": "tomato", "candidates": recipe_payload, "top_k": 2})
    assert r.status_code == 200
    assert len(r.json()["results"]) <= 2


def test_generate(client):
    r = client.post("/generate", json={
        "query": "tomato basil",
        "recipes": [
            {"id": "r1", "title": "Pasta", "text": "tomato garlic basil"},
            {"id": "r2", "title": "Salad", "text": "tomato mozzarella"},
        ],
        "style": "summary",
    })
    assert r.status_code == 200
    assert "text" in r.json()


def test_rag_query_full(client):
    r = client.post("/rag/query", json={
        "query_text": "tomato",
        "top_k": 3,
        "rerank": True,
        "rerank_top_k": 5,
        "generate": True,
        "generate_style": "summary",
    })
    assert r.status_code == 200
    data = r.json()
    assert "retrieved" in data
    assert "timings" in data
    assert "providers" in data


def test_metrics(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "multimodal_rag_requests_total" in r.text
