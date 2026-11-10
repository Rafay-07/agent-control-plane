"""Model providers. Real providers would wrap an HTTP API; the mock ones let
the whole system run and be tested offline."""
from dataclasses import dataclass, field


@dataclass
class Response:
    text: str = ""
    tool_call: dict | None = None      # {"name": str, "args": dict}
    tokens_in: int = 0
    tokens_out: int = 0


def count_tokens(text: str) -> int:
    # Rough estimate: 1 token ~ 4 characters. Good enough for cost tracking.
    return max(1, len(text) // 4)


@dataclass
class Provider:
    name: str
    tier: int                 # 1 = small/cheap, 3 = strongest
    cost_per_1k: float        # dollars per 1,000 tokens
    latency_ms: int           # typical latency
    script: list = field(default_factory=list)   # canned Responses (tests)

    def complete(self, messages: list[dict], tools: list[str]) -> Response:
        raise NotImplementedError


class MockProvider(Provider):
    """Rule-based stand-in for an LLM. If a tool name or keyword appears in the
    last user message it asks for that tool; after a tool result it answers
    using the result text. Deterministic, so tests and evals are repeatable."""

    KEYWORDS = {
        "refund": "create_ticket",      # checked first: "refund order A1" is a ticket
        "ticket": "create_ticket",
        "order": "lookup_order",
        "weather": "get_weather",
        "sum": "calculate",
        "calculate": "calculate",
    }

    def complete(self, messages, tools):
        if self.script:
            r = self.script.pop(0)
            r.tokens_in = r.tokens_in or count_tokens(str(messages))
            r.tokens_out = r.tokens_out or count_tokens(r.text or str(r.tool_call))
            return r
        last = messages[-1]
        tin = count_tokens(str(messages))
        if last["role"] == "tool":
            text = f"Result: {last['content']}"
            return Response(text=text, tokens_in=tin, tokens_out=count_tokens(text))
        low = last["content"].lower()
        for word, tool in self.KEYWORDS.items():
            if word in low and tool in tools:
                args = self._extract_args(tool, last["content"])
                call = {"name": tool, "args": args}
                return Response(tool_call=call, tokens_in=tin, tokens_out=count_tokens(str(call)))
        text = "I can help with orders, tickets, weather and arithmetic."
        return Response(text=text, tokens_in=tin, tokens_out=count_tokens(text))

    @staticmethod
    def _extract_args(tool, content):
        words = content.replace("?", " ").replace(",", " ").split()
        if tool == "lookup_order":
            ids = [w for w in words if w.startswith("A") and w[1:].isdigit()]
            return {"order_id": ids[0] if ids else ""}
        if tool == "calculate":
            nums = [float(w) for w in words if w.replace(".", "", 1).isdigit()]
            return {"numbers": nums}
        if tool == "get_weather":
            return {"city": words[-1]}
        return {"summary": content[:80]}
