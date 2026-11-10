"""Tracing: one JSON line per event (model call, tool call, block), with cost."""
import json
import time


class Tracer:
    def __init__(self, path=None):
        self.path = path
        self.events = []

    def log(self, kind, **data):
        ev = {"ts": round(time.time(), 3), "kind": kind, **data}
        self.events.append(ev)
        if self.path:
            with open(self.path, "a") as f:
                f.write(json.dumps(ev) + "\n")

    def total_cost(self):
        return round(sum(e.get("cost", 0) for e in self.events), 6)

    def count(self, kind):
        return sum(1 for e in self.events if e["kind"] == kind)
