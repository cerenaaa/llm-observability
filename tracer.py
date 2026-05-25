"""
Decorator-based LLM request tracer.
Captures span ID, model, token counts, latency, and status for every LLM call.
"""
from __future__ import annotations
import uuid
import time
import functools
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Callable, Optional


@dataclass
class Span:
    span_id: str
    trace_id: str
    operation: str
    model: str
    start_time: float
    end_time: Optional[float] = None
    input_tokens: int = 0
    output_tokens: int = 0
    status: str = "running"
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @property
    def latency_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def finish(self, input_tokens: int = 0, output_tokens: int = 0, error: str = None):
        self.end_time = time.perf_counter()
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.status = "error" if error else "ok"
        self.error = error

    def to_log_line(self) -> str:
        return (f"[TRACE {self.span_id[:8]}] {self.operation} | "
                f"model={self.model} | tokens={self.total_tokens} | "
                f"latency={self.latency_ms/1000:.2f}s | status={self.status}"
                + (f" | error={self.error}" if self.error else ""))


class LLMTracer:
    def __init__(self, trace_id: str = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.spans: list[Span] = []

    def start_span(self, operation: str, model: str, **metadata) -> Span:
        span = Span(
            span_id=str(uuid.uuid4()),
            trace_id=self.trace_id,
            operation=operation,
            model=model,
            start_time=time.perf_counter(),
            metadata=metadata,
        )
        self.spans.append(span)
        return span

    def summary(self) -> dict:
        completed = [s for s in self.spans if s.end_time]
        return {
            "trace_id": self.trace_id,
            "total_spans": len(self.spans),
            "total_tokens": sum(s.total_tokens for s in completed),
            "total_latency_ms": sum(s.latency_ms for s in completed),
            "errors": sum(1 for s in completed if s.status == "error"),
        }


def trace(operation: str = "llm_call", model: str = "unknown"):
    """Decorator that automatically traces a function returning an Anthropic response."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = LLMTracer()
            span = tracer.start_span(operation, model)
            try:
                result = func(*args, **kwargs)
                input_tok = getattr(result, "usage", None)
                in_t = input_tok.input_tokens if input_tok else 0
                out_t = input_tok.output_tokens if input_tok else 0
                span.finish(input_tokens=in_t, output_tokens=out_t)
                print(span.to_log_line())
                return result
            except Exception as e:
                span.finish(error=str(e))
                print(span.to_log_line())
                raise
        return wrapper
    return decorator
