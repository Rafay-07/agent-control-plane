"""Durable workflow: each step's output is checkpointed in SQLite, so a run that
crashes can resume from the last finished step instead of starting over."""
import json
import sqlite3


class Workflow:
    def __init__(self, run_id, steps, path=":memory:", db=None):
        self.run_id, self.steps = run_id, steps          # steps: list of (name, fn)
        self.db = db or sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS checkpoints(run TEXT, step TEXT, output TEXT, PRIMARY KEY(run, step))")

    def run(self):
        data = None
        for name, fn in self.steps:
            row = self.db.execute("SELECT output FROM checkpoints WHERE run=? AND step=?",
                                  (self.run_id, name)).fetchone()
            if row:                                       # finished earlier: reuse
                data = json.loads(row[0])
                continue
            data = fn(data)                               # may raise; earlier steps stay saved
            self.db.execute("INSERT INTO checkpoints VALUES (?,?,?)", (self.run_id, name, json.dumps(data)))
            self.db.commit()
        return data
