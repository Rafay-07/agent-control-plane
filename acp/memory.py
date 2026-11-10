"""Persistent memory in SQLite: conversation history per thread, plus small
key/value state and a keyword-overlap recall for long-term facts."""
import json
import sqlite3
import time


class Memory:
    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path)
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, thread TEXT, role TEXT, content TEXT, ts REAL);
        CREATE TABLE IF NOT EXISTS state(thread TEXT, key TEXT, value TEXT, PRIMARY KEY(thread, key));
        CREATE TABLE IF NOT EXISTS facts(id INTEGER PRIMARY KEY, thread TEXT, fact TEXT, ts REAL);
        """)

    def add_message(self, thread, role, content):
        self.db.execute("INSERT INTO messages(thread, role, content, ts) VALUES (?,?,?,?)",
                        (thread, role, content, time.time()))
        self.db.commit()

    def history(self, thread, limit=20):
        rows = self.db.execute(
            "SELECT role, content FROM messages WHERE thread=? ORDER BY id DESC LIMIT ?",
            (thread, limit)).fetchall()
        return [{"role": r, "content": c} for r, c in reversed(rows)]

    def set_state(self, thread, key, value):
        self.db.execute("INSERT OR REPLACE INTO state VALUES (?,?,?)", (thread, key, json.dumps(value)))
        self.db.commit()

    def get_state(self, thread, key, default=None):
        row = self.db.execute("SELECT value FROM state WHERE thread=? AND key=?", (thread, key)).fetchone()
        return json.loads(row[0]) if row else default

    def remember(self, thread, fact):
        self.db.execute("INSERT INTO facts(thread, fact, ts) VALUES (?,?,?)", (thread, fact, time.time()))
        self.db.commit()

    def recall(self, thread, query, k=3):
        """Rank stored facts by how many query words they share."""
        q = set(query.lower().split())
        rows = self.db.execute("SELECT fact FROM facts WHERE thread=?", (thread,)).fetchall()
        scored = [(len(q & set(f.lower().split())), f) for (f,) in rows]
        scored = [s for s in scored if s[0] > 0]
        return [f for _, f in sorted(scored, key=lambda s: -s[0])[:k]]
