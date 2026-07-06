"""Tests for multimodal_rag.config."""

from multimodal_rag.config import Settings, get_settings


def test_settings_defaults():
    s = Settings()  # type: ignore[call-arg]
    assert s.app_name == "multimodal-rag"
    assert s.embedding_provider in ("mock", "local_hf", "openai")
    assert s.vector_store in ("chroma", "qdrant", "faiss")
    assert s.embeddings_dim > 0


def test_get_settings_cached():
    a = get_settings()
    b = get_settings()
    assert a is b


def test_cors_origins_list_wildcard():
    s = Settings(cors_origins="*", app_env="dev")  # type: ignore[call-arg]
    assert s.cors_origins_list == ["*"]


def test_cors_origins_list_multiple():
    s = Settings(cors_origins="http://a.com, http://b.com", app_env="dev")  # type: ignore[call-arg]
    assert s.cors_origins_list == ["http://a.com", "http://b.com"]


def test_is_prod():
    s = Settings(app_env="prod", cors_origins="*")  # type: ignore[call-arg]
    assert s.is_prod is True
