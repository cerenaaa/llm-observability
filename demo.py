"""
LLM observability demo — runs without an API key to show cost + alert logic.
"""
import random
from cost_tracker import CostTracker, PRICING
from alerts import build_default_engine

def simulate_requests(n: int = 50, seed: int = 42):
    random.seed(seed)
    tracker = CostTracker(daily_budget_usd=0.10)  # low budget to trigger alert
    latencies = []
    errors = 0
    models = list(PRICING.keys())[:3]

    for i in range(n):
        model = random.choice(models)
        in_tok = random.randint(200, 1500)
        out_tok = random.randint(50, 500)
        latency = random.lognormvariate(6.5, 0.6)  # ms
        is_error = random.random() < 0.04
        tracker.record(model, in_tok, out_tok, operation="chat")
        latencies.append(latency)
        if is_error:
            errors += 1

    print(tracker.report())

    latencies_sorted = sorted(latencies)
    p95 = latencies_sorted[int(len(latencies) * 0.95)]
    metrics = {
        "latency_p95_ms": p95,
        "error_rate": errors / n,
        "daily_cost_usd": tracker.daily_spend(),
    }

    print(f"\n[METRICS] p95={p95:.0f}ms | error_rate={errors/n:.1%} | requests={n}")
    engine = build_default_engine()
    alerts = engine.evaluate(metrics)
    if not alerts:
        print("[OK] No alerts fired")

if __name__ == "__main__":
    simulate_requests(50)
