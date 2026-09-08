"""Metrics — re-export from app's Prometheus setup."""
from __future__ import annotations

from apps.api.app.observability.metrics import (
    record_query, record_cost, record_failure, record_tool_call,
    RAG_QUERY_TOTAL, RAG_QUERY_LATENCY, RAG_COST_USD, RAG_FAILURES,
)

__all__ = [
    "record_query", "record_cost", "record_failure", "record_tool_call",
    "RAG_QUERY_TOTAL", "RAG_QUERY_LATENCY", "RAG_COST_USD", "RAG_FAILURES",
]
