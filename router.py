"""Model routing: pick the cheapest provider that is good enough for the task
and fast enough for the latency budget."""
from .providers import Provider

HARD_WORDS = ("analyze", "compare", "plan", "multi-step", "explain why", "prove", "design")


def complexity(prompt: str, n_tools: int = 0) -> int:
    """Return a tier from 1 (easy) to 3 (hard) from cheap signals."""
    score = 0
    if len(prompt) > 400:
        score += 1
    if any(w in prompt.lower() for w in HARD_WORDS):
        score += 1
    if n_tools >= 3:
        score += 1
    return min(3, 1 + score)


class Router:
    def __init__(self, providers: list[Provider]):
        if not providers:
            raise ValueError("need at least one provider")
        self.providers = providers

    def choose(self, prompt: str, n_tools: int = 0, latency_budget_ms: int | None = None):
        """Return (provider, reason). Cheapest provider whose tier >= needed tier
        and whose latency fits the budget. Falls back to the strongest provider."""
        need = complexity(prompt, n_tools)
        ok = [p for p in self.providers if p.tier >= need]
        if latency_budget_ms is not None:
            fast = [p for p in ok if p.latency_ms <= latency_budget_ms]
            ok = fast or ok          # a missed budget beats no answer
        if not ok:
            best = max(self.providers, key=lambda p: p.tier)
            return best, f"need tier {need}, fell back to strongest ({best.name})"
        pick = min(ok, key=lambda p: (p.cost_per_1k, p.latency_ms))
        return pick, f"need tier {need}, cheapest fit is {pick.name}"
