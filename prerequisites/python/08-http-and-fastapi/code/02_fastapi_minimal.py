"""A FastAPI app with a path parameter and a query parameter, tested in-process.

Run:  uv run python prerequisites/python/08-http-and-fastapi/code/02_fastapi_minimal.py
Expect: three responses: the health check, one item, and a 422 for a non-integer id.
"""

# %% imports
import sys

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
except ImportError:
    print("fastapi is not installed. Run: uv sync --all-groups")
    sys.exit(0)

# %% app
app = FastAPI()
ITEMS = {1: "tea", 2: "coffee"}


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/items/{item_id}")
def get_item(item_id: int, verbose: bool = False) -> dict:  # path param typed as int -> validated
    name = ITEMS.get(item_id, "unknown")
    return {"id": item_id, "name": name, "verbose": verbose}


# %% try_it
client = TestClient(app)
print(client.get("/health").json())
print(client.get("/items/1?verbose=true").json())
r = client.get("/items/abc")
print(r.status_code, r.json()["detail"][0]["msg"])
