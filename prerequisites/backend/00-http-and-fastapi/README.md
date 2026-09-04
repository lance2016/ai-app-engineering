---
status: complete
part: 前置 · 后端工程
estimated_time: 约 2 小时
---

# B00 HTTP 与 FastAPI

> 浏览器、手机 App、另一个服务想用你的程序，靠的是 HTTP：发一个请求过来，你回一个响应。这一模块先拆开请求和响应看看里面有什么，再用 FastAPI 写一个能收请求、校验数据、按规矩报错、还能一边算一边往回吐字的服务。

## 学习目标

- 能说出一个 HTTP 请求和响应各由哪几部分组成，以及 2xx / 4xx / 5xx 状态码分别表示谁的问题
- 能用 FastAPI 写出带路径参数、查询参数、JSON 请求体和统一错误响应的接口，并用 `TestClient` 在脚本里自测
- 能解释依赖注入解决了什么重复，以及 SSE 流式响应和普通响应的区别

## 前置

- [P06 Pydantic v2](../../python/06-pydantic/README.md)：FastAPI 的请求体校验就是 Pydantic
- [P07 asyncio](../../python/07-asyncio/README.md)：流式响应的例子用了 `async` 生成器

## 核心概念

### 请求和响应长什么样

一次 HTTP 交互就是一来一回两段文本：

```text
请求                                     响应
GET /items HTTP/1.1                      HTTP/1.1 200 OK
Host: api.local                          Content-Type: application/json
Authorization: Bearer secret             X-Request-Id: req_1

                                         {"items": ["a", "b"]}
```

请求有**方法**（GET 拿数据、POST 创建、PUT/PATCH 修改、DELETE 删除）、**路径**、**头**（Header，一行一个键值，放认证、格式说明这类元信息）、可选的**体**（Body，通常是 JSON）。响应有**状态码**、头、体。

状态码的第一位数字说的是"谁的问题"：

| 范围 | 意思 | 例子 |
|---|---|---|
| 2xx | 成功 | 200 OK、201 Created |
| 4xx | 客户端的问题 | 400 参数错、401 没登录、404 找不到、422 数据校验失败 |
| 5xx | 服务端的问题 | 500 代码炸了、503 服务不可用 |

`01_http_anatomy_httpx.py` 用 httpx 对一个假服务器发请求，每一步都把这些部分打印出来。httpx 是发请求的库，和 `requests` 用法相近，但有 async 版本，后面写 Agent 调外部接口用的就是它。

### 一个最小的 FastAPI 应用

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
def get_item(item_id: int, verbose: bool = False) -> dict:
    return {"id": item_id, "verbose": verbose}
```

三个信息都在函数签名里：`{item_id}` 是**路径参数**，类型写 `int`，FastAPI 会帮你转换和校验；`verbose` 不在路径里，就是**查询参数**（`?verbose=true`）；返回的 dict 自动变成 JSON。

访问 `/items/abc` 会得到 422，响应体里写着 `Input should be a valid integer`。你一行校验代码都没写。

### 请求体、错误响应

```python
class ItemIn(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(gt=0)

@app.post("/items", status_code=201)
def create_item(item: ItemIn) -> dict:
    ...

@app.get("/items/{item_id}")
def read_item(item_id: int) -> dict:
    if item_id not in DB:
        raise HTTPException(status_code=404, detail=f"item {item_id} not found")
```

参数的类型是一个 Pydantic 模型，FastAPI 就知道它来自 JSON 请求体。校验失败自动 422，`detail` 里是 Pydantic 那份逐字段错误。业务上的"找不到"用 `HTTPException` 抛出，客户端拿到的是 `{"detail": "..."}`，格式和校验错误一致。

### 依赖注入：把重复的检查抽出去

```python
def current_user(authorization: str = Header(default="")) -> str:
    token = authorization.removeprefix("Bearer ")
    if token not in TOKENS:
        raise HTTPException(status_code=401, detail="invalid token")
    return TOKENS[token]

@app.get("/me")
def me(user: str = Depends(current_user)) -> dict:
    return {"user": user}
```

十个接口都要检查登录，不能每个里面复制一遍。`Depends(current_user)` 的意思是"调我之前先调 `current_user`，把它的返回值当作 `user` 传给我"。检查失败它自己抛 401，接口函数根本不会执行。数据库连接、当前租户、权限，都是这样注入的。

### SSE 流式：一边算一边发

```python
async def token_stream():
    for word in ["Hello", "from", "the", "server"]:
        await asyncio.sleep(0.05)
        yield f"data: {word}\n\n"

@app.get("/stream")
async def stream():
    return StreamingResponse(token_stream(), media_type="text/event-stream")
```

普通响应是算完一次性发。模型生成一段话要几秒，用户不想盯着空白等，所以聊天界面都是一个词一个词出现的。SSE（Server-Sent Events）就是干这个的：响应类型是 `text/event-stream`，服务端每产生一块就写一行 `data: ...` 加一个空行，连接保持打开。客户端用 `iter_lines()` 逐行读。`05_sse_streaming.py` 里的生成器每 `yield` 一次，客户端就多收到一行。

### 测试不用起服务器

所有例子都用 `TestClient(app)` 在同一个进程里发请求。它模拟了完整的 HTTP 往返，但不占端口、不需要另开终端。写接口时先这样自测，`uv run uvicorn module:app --reload` 起真服务是给别人用的时候才做的事。

## 动手

| 文件 | 一个知识点 |
|---|---|
| [`code/01_http_anatomy_httpx.py`](./code/01_http_anatomy_httpx.py) | 请求/响应的组成，401 / 200 / 201 各是什么意思 |
| [`code/02_fastapi_minimal.py`](./code/02_fastapi_minimal.py) | 路径参数、查询参数、自动校验 |
| [`code/03_request_body_and_errors.py`](./code/03_request_body_and_errors.py) | Pydantic 请求体、422 和 404 的响应形状 |
| [`code/04_dependency_injection.py`](./code/04_dependency_injection.py) | `Depends` 抽出登录检查 |
| [`code/05_sse_streaming.py`](./code/05_sse_streaming.py) | `StreamingResponse` 逐行推送，客户端逐行读 |

没装依赖时每个文件会提示 `uv sync --all-groups` 后退出。

## 常见错误

**返回了 JSON 表示不了的东西。**

```text
ValueError: [TypeError("'object' object is not iterable"), TypeError('vars() argument must have __dict__ attribute')]
```

接口返回值里有 `datetime`、自定义对象、`set` 之类的东西。返回 Pydantic 模型或纯 dict/list/str/int，日期先 `.isoformat()`。

**POST 没带请求体。**

```text
422 {'detail': [{'type': 'missing', 'loc': ['body'], 'msg': 'Field required', 'input': None}]}
```

`loc` 是 `['body']` 说明整个请求体都没有。客户端要发 JSON（httpx 用 `json=`，curl 用 `-H 'Content-Type: application/json' -d '{...}'`）。如果 `loc` 是 `['body', 'price']`，那是体有了但某个字段有问题。

**在 `async def` 接口里调同步阻塞的东西。** 不报错，但整个服务在那一刻停下来服务不了别人。规则和 P07 一样：接口用 `async def` 就只 `await` 异步库；非要用同步库（比如老的数据库驱动），把接口写成普通 `def`，FastAPI 会把它放到线程池里跑。

## 练习

见 [exercises.md](./exercises.md)。

## 它在 AI 应用里用在哪

主线落点：[02 模型调用、结构化输出与流式](../../../lessons/02-model-api-structured-output-streaming/README.md)、[16 AI 应用系统架构](../../../lessons/16-system-architecture/README.md)、主项目 [M1 API 骨架](../../../project/m1-api-skeleton/README.md)。

具体场景：主项目 M1 就是这一模块的组合。`POST /chat` 接收一个 Pydantic 请求体（用户消息、会话 id），`Depends(current_user)` 认证并拿到用户，然后用 `StreamingResponse` 把模型一个词一个词吐出来的内容推给前端。模型调用失败时抛 `HTTPException(503)`，参数不对时 FastAPI 自动 422。第 07 课的事件流接到 SSE 上，前端看到的每一行 `data:` 就是运行时写下的每一条事件。

## 延伸阅读

- [MDN · HTTP 概述（中文）](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Overview)（访问日期 2026-09-04）：HTTP 是什么、请求响应的结构，配图清楚。
- [FastAPI · 教程（中文）](https://fastapi.tiangolo.com/zh/tutorial/)（访问日期 2026-09-04）：官方教程质量很高，按顺序读到"依赖项"一章就够本课程用。
- [httpx · QuickStart](https://www.python-httpx.org/quickstart/)（访问日期 2026-09-04）：发请求那一侧的库，重点看 `AsyncClient`。

---

[← P07](../../python/07-asyncio/README.md) · [B01 →](../01-sql-and-sqlalchemy/README.md)
