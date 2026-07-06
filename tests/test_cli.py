"""Tests for the Typer CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from multimodal_rag.cli import app

runner = CliRunner()


def test_info_command():
    r = runner.invoke(app, ["info"])
    assert r.exit_code == 0
    assert "multimodal-rag" in r.stdout
    assert "embedding_provider" in r.stdout


def test_help():
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0
    assert "ingest" in r.stdout
    assert "serve" in r.stdout
    assert "query" in r.stdout


def test_query_requires_arg():
    r = runner.invoke(app, ["query"])
    assert r.exit_code != 0
