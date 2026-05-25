"""
Rule-based alerting for LLM production metrics.
Triggers on cost spikes, latency regressions, and error rate thresholds.
"""
from __future__ import annotations
import statistics
from dataclasses import dataclass
from typing import Callable


@dataclass
class Alert:
    severity: str   # "warning" | "critical"
    metric: str
    message: str
    value: float
    threshold: float


class AlertEngine:
    def __init__(self):
        self.rules: list[tuple[str, Callable]] = []
        self.fired: list[Alert] = []

    def add_rule(self, name: str, fn: Callable):
        self.rules.append((name, fn))

    def evaluate(self, metrics: dict) -> list[Alert]:
        alerts = []
        for name, fn in self.rules:
            result = fn(metrics)
            if result:
                alerts.append(result)
                print(f"[ALERT] {result.severity.upper()} — {result.message}")
        self.fired.extend(alerts)
        return alerts


def build_default_engine(
    latency_p95_threshold_ms: float = 2000,
    error_rate_threshold: float = 0.05,
    daily_cost_threshold_usd: float = 10.0,
) -> AlertEngine:
    engine = AlertEngine()

    def latency_rule(m: dict):
        p95 = m.get("latency_p95_ms", 0)
        if p95 > latency_p95_threshold_ms:
            return Alert("warning", "latency_p95",
                         f"p95 latency {p95:.0f}ms > {latency_p95_threshold_ms:.0f}ms threshold",
                         p95, latency_p95_threshold_ms)

    def error_rate_rule(m: dict):
        rate = m.get("error_rate", 0)
        if rate > error_rate_threshold:
            return Alert("critical", "error_rate",
                         f"Error rate {rate:.1%} > {error_rate_threshold:.1%} threshold",
                         rate, error_rate_threshold)

    def cost_rule(m: dict):
        cost = m.get("daily_cost_usd", 0)
        if cost > daily_cost_threshold_usd:
            return Alert("warning", "daily_cost",
                         f"Daily cost ${cost:.2f} exceeded ${daily_cost_threshold_usd:.2f} budget",
                         cost, daily_cost_threshold_usd)

    engine.add_rule("latency_p95", latency_rule)
    engine.add_rule("error_rate", error_rate_rule)
    engine.add_rule("daily_cost", cost_rule)
    return engine
