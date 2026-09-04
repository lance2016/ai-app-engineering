"""OpenTelemetry tracing with GenAI semantic-convention attribute names.

``setup_tracing`` installs a TracerProvider once per process. With
``OTEL_EXPORTER_OTLP_ENDPOINT`` set, spans go to any OTLP/HTTP collector
(Phoenix listens on :6006/v1/traces); without it, spans are kept in memory so
tests and the chaos script can read them back. Span names follow
``"{operation} {target}"``: ``invoke_agent aiapp``, ``chat fake``, ``execute_tool search_docs``.
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import Span, Status, StatusCode

SERVICE_NAME = "aiapp"
# Attribute names: OpenTelemetry GenAI semantic conventions (stable subset) plus aiapp.* for what the conventions do not cover.
A_OPERATION = "gen_ai.operation.name"
A_PROVIDER = "gen_ai.provider.name"
A_REQUEST_MODEL = "gen_ai.request.model"
A_INPUT_TOKENS = "gen_ai.usage.input_tokens"
A_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"
A_FINISH_REASONS = "gen_ai.response.finish_reasons"
A_TOOL_NAME = "gen_ai.tool.name"
A_TOOL_CALL_ID = "gen_ai.tool.call.id"
A_CONVERSATION_ID = "gen_ai.conversation.id"
A_AGENT_NAME = "gen_ai.agent.name"
A_TENANT = "aiapp.tenant_id"
A_THREAD = "aiapp.thread_id"
A_PROMPT_VERSION = "aiapp.prompt_version"
A_REQUEST_ID = "aiapp.request_id"
A_ROUTE = "aiapp.tool.route"
A_ATTEMPTS = "aiapp.tool.attempts"
A_STOP_REASON = "aiapp.stop_reason"
A_COST_USD = "aiapp.cost_usd"
A_FALLBACK = "aiapp.fallback"

_memory_exporter: InMemorySpanExporter | None = None
_configured = False


def setup_tracing(endpoint: str | None = None, *, service_name: str = SERVICE_NAME, in_memory: bool | None = None) -> None:
    """Idempotent. OTLP/HTTP when an endpoint is given (or OTEL_EXPORTER_OTLP_ENDPOINT is set), in-memory otherwise."""
    global _memory_exporter, _configured
    if _configured:
        return
    endpoint = endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    if endpoint and not in_memory:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces")))
    else:
        _memory_exporter = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(_memory_exporter))
    trace.set_tracer_provider(provider)
    _configured = True


def tracer() -> trace.Tracer:
    return trace.get_tracer("aiapp", "0.5.0")


def recorded_spans() -> list[ReadableSpan]:
    """Spans captured by the in-memory exporter (tests, chaos script). Empty when exporting over OTLP."""
    return list(_memory_exporter.get_finished_spans()) if _memory_exporter else []


def clear_recorded_spans() -> None:
    if _memory_exporter:
        _memory_exporter.clear()


def flush() -> None:
    provider = trace.get_tracer_provider()
    if hasattr(provider, "force_flush"):
        provider.force_flush()


@contextmanager
def span(name: str, **attributes: Any) -> Iterator[Span]:
    """A span whose status is set explicitly: an exception is recorded *and* marks the span ERROR (lesson 18)."""
    with tracer().start_as_current_span(name) as s:
        for key, value in attributes.items():
            if value is not None:
                s.set_attribute(key, value)
        try:
            yield s
        except Exception as exc:
            s.record_exception(exc)
            s.set_status(Status(StatusCode.ERROR, str(exc)))
            raise
        else:
            if s.status.status_code == StatusCode.UNSET:
                s.set_status(Status(StatusCode.OK))


def mark_error(s: Span, message: str, error_type: str | None = None) -> None:
    s.set_status(Status(StatusCode.ERROR, message))
    if error_type:
        s.set_attribute("error.type", error_type)


def current_trace_id() -> str | None:
    ctx = trace.get_current_span().get_span_context()
    return f"{ctx.trace_id:032x}" if ctx and ctx.is_valid else None
