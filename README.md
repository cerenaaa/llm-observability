# LLM Observability

[![CI](https://github.com/cerenaaa/llm-observability/actions/workflows/ci.yml/badge.svg)](https://github.com/cerenaaa/llm-observability/actions)

Production observability stack for LLM applications: request tracing, token cost tracking, latency profiling, prompt/response logging, and anomaly alerting.

## Why this matters

LLMs are black boxes in production. Without observability you can't answer:
- Which prompts are slow or expensive?
- When did output quality degrade?
- Which users trigger the most retries?
- Is cost per request trending up?

## Components

| Module | Purpose |
|---|---|
| `tracer.py` | Decorator-based request tracing with span IDs |
| `cost_tracker.py` | Token cost estimation across models and providers |
| `logger.py` | Structured prompt/response logging with PII redaction |
| `metrics.py` | Latency histograms, error rates, cost aggregations |
| `alerts.py` | Rule-based alerting: cost spikes, latency p95, error rate |

## Quickstart

```bash
pip install -r requirements.txt
python demo.py
```

## Example output

```
[TRACE abc123] POST /generate | model=claude-sonnet-4-20250514 | tokens=847 | cost=$0.0021 | latency=1.24s | status=ok
[ALERT] p95 latency exceeded threshold: 3.2s > 2.0s (window: last 100 requests)
[COST] Daily spend: $4.82 | Projected monthly: $144.60 | Budget: $200
```
