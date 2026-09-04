"""Tables, rows, and a JOIN, with Python's built-in sqlite3.

Run:  uv run python prerequisites/python/09-sql-and-sqlalchemy/code/01_sql_basics.py
Expect: two conversations created, three messages inserted, a JOIN listing each
        message with its conversation title.
"""

# %% imports
import sqlite3

conn = sqlite3.connect(":memory:")  # a throwaway database that lives in RAM
cur = conn.cursor()

# %% create_tables
cur.executescript("""
CREATE TABLE conversation (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL
);
CREATE TABLE message (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversation(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL
);
""")

# %% insert
cur.execute("INSERT INTO conversation (title) VALUES (?)", ("weather chat",))
cur.execute("INSERT INTO conversation (title) VALUES (?)", ("travel plan",))
cur.executemany(
    "INSERT INTO message (conversation_id, role, content) VALUES (?, ?, ?)",
    [(1, "user", "weather in Shenzhen?"), (1, "assistant", "31°C and sunny"), (2, "user", "flights to Tokyo")],
)
conn.commit()

# %% select_and_join
for row in cur.execute("SELECT id, title FROM conversation"):
    print(row)
print()
query = """
SELECT c.title, m.role, m.content
FROM message m
JOIN conversation c ON c.id = m.conversation_id
ORDER BY m.id
"""
for title, role, content in cur.execute(query):
    print(f"{title:14} {role:10} {content}")
