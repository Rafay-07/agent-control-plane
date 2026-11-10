# agent-control-plane

A small agent runtime in Python that shows the parts a production agent platform needs around the model: routing, memory, tool access control, guardrails, durable workflows, tracing and evaluation. It runs offline with mock providers, so every behaviour is tested without an API key.

Built as a learning project on agent reliability. Real providers plug in by subclassing `Provider` in `acp/providers.py`.

## What it does

| Module | What it does |
|---|---|
| `router.py` | Scores task complexity and picks the cheapest model tier that fits the quality need and latency budget |
| `memory.py` | SQLite conversation history, per-thread state and keyword recall of stored facts. Survives restarts |
| `tools.py` | Tool registry with argument validation and role-based access. Users never see admin tools |
| `guardrails.py` | Blocks prompt injection and credential requests; redacts emails and phone numbers before saving or returning text |
| `agent.py` | Guardrails, route, model call, tool call, memory loop with a hard step limit |
| `workflow.py` | Checkpoints each step in SQLite so a crashed run resumes instead of restarting |
| `tracing.py` | One JSON line per model call, tool call and block, with token and cost estimates |
| `evals.py` | Fixed case set scoring tool choice, answer content, blocked unsafe input and cost |

## Run it

```bash
pip install -r requirements.txt
python -m pytest -q        # 11 tests
python -m acp.evals        # 6 evaluation cases
```

```python
from acp.evals import build_agent
agent = build_agent()
print(agent.run("thread-1", "Where is order A100?"))
print(agent.tracer.total_cost())
```

## Design notes

- Guardrails live outside the model so a prompt cannot switch them off.
- The mock provider is rule based and deterministic, which keeps tests and evals repeatable. It is not a language model.
- Token counts use a 4-characters-per-token estimate. Swap in the provider's real usage numbers for billing.
- Not built yet: vector and graph retrieval, multi-model fallback on errors, a trace viewer.
