"""What goes in the cache and what goes in the database, shown by killing the cache.

A TTL cache (Redis in production) holds things that are cheap to rebuild:
the "run in progress" flag, rate-limit counters, a hot copy of the last
messages. The durable store (PostgreSQL) holds the event thread. Wipe the cache
mid-conversation and the conversation must survive; wipe it and lose history,
and the boundary was drawn in the wrong place.

Run:  uv run python lessons/16-system-architecture/code/03_storage_boundaries.py
      INJECT_HISTORY_IN_CACHE=1 uv run python lessons/16-system-architecture/code/03_storage_boundaries.py
Expect: after the cache is flushed the thread reloads from SQLite intact; with
        injection the history lived only in the cache and is gone.
"""

# %% imports
import os
import sqlite3
import tempfile
import time
from pathlib import Path

from aiapp import Thread

INJECT_HISTORY_IN_CACHE = os.environ.get("INJECT_HISTORY_IN_CACHE") == "1"
DB = Path(os.environ.get("CHECKPOINT_DIR", tempfile.gettempdir())) / "aiapp_lesson16.sqlite"


# %% cache
class TTLCache:
    """Stand-in for Redis. Everything here may vanish at any moment."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[float, str]] = {}

    def set(self, key: str, value: str, ttl: float = 60) -> None:
        self._data[key] = (time.monotonic() + ttl, value)

    def get(self, key: str) -> str | None:
        item = self._data.get(key)
        if item is None or item[0] < time.monotonic():
            return None
        return item[1]

    def flush(self) -> None:
        self._data.clear()


# %% durable_store
class ThreadRepo:
    """Stand-in for the PostgreSQL table M2 will create."""

    def __init__(self, path: Path) -> None:
        self.conn = sqlite3.connect(path)
        self.conn.execute("CREATE TABLE IF NOT EXISTS threads (thread_id TEXT PRIMARY KEY, body TEXT NOT NULL)")

    def save(self, thread: Thread) -> None:
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO threads VALUES (?, ?)", (thread.thread_id, thread.to_json()))

    def load(self, thread_id: str) -> Thread | None:
        row = self.conn.execute("SELECT body FROM threads WHERE thread_id = ?", (thread_id,)).fetchone()
        return Thread.from_json(row[0]) if row else None


# %% runtime
def handle_turn(thread: Thread, cache: TTLCache, repo: ThreadRepo, text: str) -> None:
    cache.set(f"run:{thread.thread_id}", "in_progress", ttl=30)  # cheap, rebuildable
    thread.append("user_message", content=text)
    thread.append("assistant_message", content=f"echo: {text}")
    if INJECT_HISTORY_IN_CACHE:
        cache.set(f"thread:{thread.thread_id}", thread.to_json())  # the mistake: history only in cache
    else:
        repo.save(thread)
        cache.set(f"thread:{thread.thread_id}", thread.to_json())  # hot copy is fine *in addition*
    cache.set(f"run:{thread.thread_id}", "idle", ttl=30)


def load_thread(thread_id: str, cache: TTLCache, repo: ThreadRepo) -> Thread | None:
    hot = cache.get(f"thread:{thread_id}")
    if hot:
        return Thread.from_json(hot)
    return repo.load(thread_id)  # cache miss falls through to the source of truth


# %% run
def main() -> None:
    if DB.exists():
        DB.unlink()
    cache, repo = TTLCache(), ThreadRepo(DB)
    thread = Thread(thread_id="thr_boundary")
    handle_turn(thread, cache, repo, "hello")
    handle_turn(thread, cache, repo, "what is the refund window?")
    print(f"before flush: {len(load_thread('thr_boundary', cache, repo).events)} events (served from cache)")
    cache.flush()
    print("cache flushed (Redis restarted)")
    reloaded = load_thread("thr_boundary", cache, repo)
    if reloaded is None:
        print("CONVERSATION LOST: history lived only in the cache")
    else:
        print(f"after flush: {len(reloaded.events)} events reloaded from the durable store")
        print(f"run flag after flush: {cache.get('run:thr_boundary')!r}  (fine: it is rebuildable)")


if __name__ == "__main__":
    main()
