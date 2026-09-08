"""Tracing — OpenTelemetry setup and the `traced_operation` context manager."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

_provider: TracerProvider | None = None


def setup_otel(*, service_name: str, endpoint: str | None) -> None:
    """Call once at app startup."""
    global _provider
    if not endpoint:
        return  # tracing disabled
    if _provider is not None:
        return
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)
    _provider = provider


@contextmanager
def traced_operation(name: str, **attributes: Any) -> Iterator[trace.Span]:
    """Context manager that creates a span and sets attributes on it.

    Usage:
        async with traced_operation("rag.query", trace_id=trace_id, user_id=user.id) as span:
            ...
            span.set_attributes({"result.count": 5})
    """
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(name) as span:
        for k, v in attributes.items():
            try:
                span.set_attribute(k, v)
            except Exception:
                pass  # attribute serialization can fail for complex types
        yield span
