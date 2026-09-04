"""JSON bodies validated by Pydantic, and how errors come back to the client.

Run:  uv run python prerequisites/backend/00-http-and-fastapi/code/03_request_body_and_errors.py
Expect: 201 for a good body, 422 with field detail for a bad one, 404 from HTTPException.
"""

# %% imports
import sys

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
except ImportError:
    print("fastapi is not installed. Run: uv sync --all-groups")
    sys.exit(0)
from pydantic import BaseModel, Field

# %% app
app = FastAPI()
DB: dict[int, dict] = {}


class ItemIn(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(gt=0)


@app.post("/items", status_code=201)
def create_item(item: ItemIn) -> dict:
    item_id = len(DB) + 1
    DB[item_id] = item.model_dump()
    return {"id": item_id, **DB[item_id]}


@app.get("/items/{item_id}")
def read_item(item_id: int) -> dict:
    if item_id not in DB:
        raise HTTPException(status_code=404, detail=f"item {item_id} not found")
    return DB[item_id]


# %% try_it
client = TestClient(app)
print(client.post("/items", json={"name": "tea", "price": 12}).status_code, "created")
bad = client.post("/items", json={"name": "", "price": -1})
print(bad.status_code, [(e["loc"][-1], e["msg"]) for e in bad.json()["detail"]])
missing = client.get("/items/99")
print(missing.status_code, missing.json())
