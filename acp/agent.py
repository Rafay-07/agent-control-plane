"""The agent loop: guardrails -> route -> model -> tool -> memory, with a step limit."""
from . import guardrails
from .memory import Memory
from .router import Router
from .tools import ToolError, ToolRegistry
from .tracing import Tracer

MAX_STEPS = 5


class Agent:
    def __init__(self, router: Router, tools: ToolRegistry, memory: Memory | None = None,
                 tracer: Tracer | None = None):
        self.router, self.tools = router, tools
        self.memory = memory or Memory()
        self.tracer = tracer or Tracer()

    def run(self, thread, user_text, role="user", latency_budget_ms=None):
        try:
            guardrails.check_input(user_text)
        except guardrails.Blocked as e:
            self.tracer.log("blocked", reason=str(e))
            return f"Blocked: {e}"
        self.memory.add_message(thread, "user", guardrails.redact(user_text))
        allowed = self.tools.names_for(role)
        for step in range(MAX_STEPS):
            messages = self.memory.history(thread)
            provider, why = self.router.choose(user_text, len(allowed), latency_budget_ms)
            resp = provider.complete(messages, allowed)
            cost = (resp.tokens_in + resp.tokens_out) / 1000 * provider.cost_per_1k
            self.tracer.log("model", provider=provider.name, reason=why, step=step,
                            tokens=resp.tokens_in + resp.tokens_out, cost=cost)
            if resp.tool_call is None:
                text = guardrails.redact(resp.text)
                self.memory.add_message(thread, "assistant", text)
                return text
            name, args = resp.tool_call["name"], resp.tool_call["args"]
            try:
                result = self.tools.call(name, args, role)
                self.tracer.log("tool", name=name, ok=True)
            except ToolError as e:
                result = f"tool error: {e}"
                self.tracer.log("tool", name=name, ok=False, error=str(e))
            self.memory.add_message(thread, "tool", guardrails.redact(str(result)))
        self.tracer.log("step_limit")
        return "Stopped: step limit reached."
