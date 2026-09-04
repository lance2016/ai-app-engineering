"""What a request and a response are made of, using httpx against a fake server.

No network needed: MockTransport answers in-process, so you can read every part.

Run:  uv run python prerequisites/backend/00-http-and-fastapi/code/01_http_anatomy_httpx.py
Expect: the outgoing method/url/headers/body, then status, headers and JSON of the reply.
"""

# %% imports
import json
import sys

try:
    import httpx
except ImportError:
    print("httpx is not installed. Run: uv sync --all-groups")
    sys.exit(0)


# %% fake_server
def handler(request: httpx.Request) -> httpx.Response:
    print(f"server saw: {request.method} {request.url.path} auth={request.headers.get('authorization')}")
    if request.headers.get("authorization") != "Bearer secret":
        return httpx.Response(401, json={"error": "missing or bad token"})
    if request.method == "POST":
        body = json.loads(request.content)
        return httpx.Response(201, json={"created": body["name"]})
    return httpx.Response(200, json={"items": ["a", "b"]}, headers={"x-request-id": "req_1"})


client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://api.local")

# %% get_without_token
r = client.get("/items")
print(r.status_code, "Unauthorized ->", r.json())  # 4xx: the client did something wrong

# %% get_with_token
r = client.get("/items", headers={"Authorization": "Bearer secret"})
print(r.status_code, "OK ->", r.json(), "| header x-request-id =", r.headers["x-request-id"])

# %% post_json
r = client.post("/items", json={"name": "tea"}, headers={"Authorization": "Bearer secret"})
print(r.status_code, "Created ->", r.json())
