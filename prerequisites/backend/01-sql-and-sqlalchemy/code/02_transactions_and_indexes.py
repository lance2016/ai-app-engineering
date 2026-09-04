"""Transactions make several writes succeed or fail together; indexes make lookups fast.

Run:  uv run python prerequisites/backend/01-sql-and-sqlalchemy/code/02_transactions_and_indexes.py
Expect: after a failed transfer both balances are unchanged; the query plan
        switches from SCAN to SEARCH once an index exists.
"""

# %% imports
import sqlite3

conn = sqlite3.connect(":memory:")
cur = conn.cursor()
cur.executescript("""
CREATE TABLE account (name TEXT PRIMARY KEY, balance INTEGER NOT NULL CHECK (balance >= 0));
INSERT INTO account VALUES ('alice', 100), ('bob', 20);
""")
conn.commit()


# %% transaction_rollback
def transfer(amount: int) -> None:
    try:
        cur.execute("UPDATE account SET balance = balance - ? WHERE name = 'alice'", (amount,))
        cur.execute("UPDATE account SET balance = balance + ? WHERE name = 'bob'", (amount,))
        conn.commit()
        print(f"transfer {amount}: committed")
    except sqlite3.IntegrityError as exc:
        conn.rollback()  # undo the first UPDATE too
        print(f"transfer {amount}: rolled back ({exc})")


transfer(30)
transfer(500)  # alice cannot go negative -> CHECK fails on the first UPDATE
print(dict(cur.execute("SELECT name, balance FROM account")))

# %% index
cur.executescript("CREATE TABLE message (id INTEGER PRIMARY KEY, conversation_id INTEGER, content TEXT);")
cur.executemany("INSERT INTO message (conversation_id, content) VALUES (?, ?)", [(i % 50, f"msg {i}") for i in range(5000)])
conn.commit()
q = "SELECT count(*) FROM message WHERE conversation_id = 7"
print("\nbefore index:", cur.execute(f"EXPLAIN QUERY PLAN {q}").fetchone()[-1])
cur.execute("CREATE INDEX ix_message_conversation ON message(conversation_id)")
print("after index: ", cur.execute(f"EXPLAIN QUERY PLAN {q}").fetchone()[-1])
