"""Lightweight tracing hook the agent loop can call.

This is implemented (not a TODO) so you can record traces on Saturday without
standing up a vendor platform. In production you would export the same events
to OpenTelemetry / Azure AI Foundry tracing / LangSmith-style tooling.

Usage inside the loop:

    tracer = JsonlTracer(path)
    with tracer.span("run", user=user_message) as span:
        span.event("llm_request", model=..., n_messages=...)
        span.event("tool_call", name=..., arguments=...)
        span.event("tool_result", name=..., payload=...)
        span.event("final", text=...)
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Span:
    tracer: Tracer
    name: str
    trace_id: str
    started_at: float = field(default_factory=time.perf_counter)
    attributes: dict[str, Any] = field(default_factory=dict)

    def event(self, name: str, **payload: Any) -> None:
        self.tracer.record(
            {
                "type": "event",
                "trace_id": self.trace_id,
                "span": self.name,
                "event": name,
                "ts": _now(),
                **payload,
            }
        )


class Tracer:
    def record(self, event: dict[str, Any]) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    @contextmanager
    def span(self, name: str, **attributes: Any) -> Iterator[Span]:
        trace_id = attributes.pop("trace_id", None) or uuid.uuid4().hex
        span = Span(tracer=self, name=name, trace_id=trace_id, attributes=attributes)
        self.record(
            {
                "type": "span_start",
                "trace_id": trace_id,
                "span": name,
                "ts": _now(),
                "attributes": attributes,
            }
        )
        try:
            yield span
        finally:
            duration_ms = int((time.perf_counter() - span.started_at) * 1000)
            self.record(
                {
                    "type": "span_end",
                    "trace_id": trace_id,
                    "span": name,
                    "ts": _now(),
                    "duration_ms": duration_ms,
                }
            )


class NullTracer(Tracer):
    def record(self, event: dict[str, Any]) -> None:
        return


class StderrTracer(Tracer):
    def record(self, event: dict[str, Any]) -> None:
        print(json.dumps(event, default=str), flush=True)


class JsonlTracer(Tracer):
    """Append-only JSONL trace file, one event per line."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, default=str) + "\n")
