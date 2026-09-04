"""Depends(): shared logic (here, checking a token) declared once, used by many routes.

Run:  uv run python prerequisites/python/08-http-and-fastapi/code/04_dependency_injection.py
Expect: 401 without a token, 200 with it, and the user name injected into the handler.
"""

# %% imports
import sys

try:
    from fastapi import Depends, FastAPI, Header, HTTPException
    from fastapi.testclient import TestClient
except ImportError:
    print("fastapi is not installed. Run: uv sync --all-groups")
    sys.exit(0)

# %% dependency
TOKENS = {"secret": "ada"}


def current_user(authorization: str = Header(default="")) -> str:
    token = authorization.removeprefix("Bearer ").strip()
    if token not in TOKENS:
        raise HTTPException(status_code=401, detail="invalid token")
    return TOKENS[token]


# %% app
app = FastAPI()


@app.get("/me")
def me(user: str = Depends(current_user)) -> dict:  # FastAPI calls current_user for you
    return {"user": user}


@app.get("/orders")
def orders(user: str = Depends(current_user)) -> dict:
    return {"user": user, "orders": []}


# %% try_it
client = TestClient(app)
print(client.get("/me").status_code, client.get("/me").json())
ok = client.get("/me", headers={"Authorization": "Bearer secret"})
print(ok.status_code, ok.json())
