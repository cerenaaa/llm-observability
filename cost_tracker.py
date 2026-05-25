"""
Token cost estimator and budget tracker across models and providers.
Prices as of 2025 — update PRICING dict as models change.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, date


# Prices in USD per 1M tokens
PRICING = {
    "claude-opus-4-20250514":    {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-20250514":  {"input":  3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input":  0.80,  "output":  4.00},
    "gpt-4o":                    {"input":  5.00, "output": 15.00},
    "gpt-4o-mini":               {"input":  0.15, "output":  0.60},
    "gemini-1.5-pro":            {"input":  3.50, "output": 10.50},
}


@dataclass
class CostEvent:
    timestamp: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    operation: str = ""


class CostTracker:
    def __init__(self, daily_budget_usd: float = 10.0):
        self.daily_budget = daily_budget_usd
        self.events: list[CostEvent] = []

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = PRICING.get(model, {"input": 3.0, "output": 15.0})
        return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000

    def record(self, model: str, input_tokens: int, output_tokens: int, operation: str = ""):
        cost = self.estimate_cost(model, input_tokens, output_tokens)
        self.events.append(CostEvent(
            timestamp=datetime.utcnow().isoformat(),
            model=model, input_tokens=input_tokens,
            output_tokens=output_tokens, cost_usd=cost, operation=operation,
        ))
        return cost

    def daily_spend(self, target_date: date = None) -> float:
        target = (target_date or date.today()).isoformat()
        return sum(e.cost_usd for e in self.events if e.timestamp.startswith(target))

    def by_model(self) -> dict:
        totals: dict[str, dict] = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost_usd": 0.0})
        for e in self.events:
            totals[e.model]["calls"] += 1
            totals[e.model]["tokens"] += e.input_tokens + e.output_tokens
            totals[e.model]["cost_usd"] += e.cost_usd
        return {k: {**v, "cost_usd": round(v["cost_usd"], 6)} for k, v in totals.items()}

    def budget_status(self) -> dict:
        daily = self.daily_spend()
        projected_monthly = daily * 30
        return {
            "daily_spend_usd": round(daily, 4),
            "daily_budget_usd": self.daily_budget,
            "budget_pct_used": round(daily / self.daily_budget * 100, 1),
            "projected_monthly_usd": round(projected_monthly, 2),
            "over_budget": daily > self.daily_budget,
        }

    def report(self) -> str:
        status = self.budget_status()
        lines = [
            f"[COST] Daily spend: ${status['daily_spend_usd']:.4f} / ${status['daily_budget_usd']} budget ({status['budget_pct_used']}%)",
            f"[COST] Projected monthly: ${status['projected_monthly_usd']:.2f}",
        ]
        if status["over_budget"]:
            lines.append("[ALERT] ⚠ Daily budget exceeded!")
        for model, stats in self.by_model().items():
            lines.append(f"  {model}: {stats['calls']} calls | {stats['tokens']:,} tokens | ${stats['cost_usd']:.4f}")
        return "\n".join(lines)
