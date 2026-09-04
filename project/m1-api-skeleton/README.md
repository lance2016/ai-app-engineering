---
status: draft
kind: impl
depends_on: 前置 P06, P08, P10；lessons/02, 03
---

# M1 API 骨架

> 把第 00 课的 `aiapp` 包装成一个能被 HTTP 调用的服务：健康检查、鉴权、创建线程、发消息并以 SSE 流式返回、结构化错误。模型仍然默认 fake，所以整套服务离线就能跑通测试。

## 这一步加什么

- **FastAPI 应用**：`project/src/aiapp/api/` 目录，把 `fastapi` 从 `prereq` 依赖组提升为主依赖
- **四个端点**：健康检查、创建线程、向线程发消息（SSE 流式）、读取线程
- **鉴权**：`Authorization: Bearer <token>` 头，token 到租户 id 的映射先用配置文件
- **结构化错误**：统一的错误信封，含 `code`、`message`、`request_id`；模型超时和供应商错误映射成 502 / 504
- **system prompt 版本化**：提示词放 `prompts/` 目录，文件名带版本，响应头返回本次用的版本
- **测试**：`httpx.AsyncClient` 打真实的 ASGI 应用，覆盖每个端点的成功路径、鉴权失败、非法输入、模型超时

目标目录结构：

```text
project/src/aiapp/api/
├── app.py            # create_app(), lifespan, 注册路由与异常处理
├── deps.py           # get_tenant(token) -> Tenant, get_adapter() 注入
├── errors.py         # ErrorEnvelope, 异常到 HTTP 状态码的映射
├── schemas.py        # CreateThreadRequest, MessageRequest, ThreadView (pydantic)
└── routes/
    ├── health.py     # GET /healthz
    └── threads.py    # POST /v1/threads, POST /v1/threads/{id}/messages, GET /v1/threads/{id}
project/src/aiapp/prompts/
└── assistant.v1.md
tests/api/
├── test_health.py
├── test_threads.py
└── test_errors.py
```

关键接口签名：

```python
# routes/threads.py
@router.post("/v1/threads", status_code=201)
async def create_thread(body: CreateThreadRequest, tenant: Tenant = Depends(get_tenant)) -> ThreadView: ...

@router.post("/v1/threads/{thread_id}/messages")
async def send_message(thread_id: str, body: MessageRequest, tenant: Tenant = Depends(get_tenant),
                       model: ModelAdapter = Depends(get_adapter)) -> StreamingResponse:  # text/event-stream
    """Yields lesson-07 events as SSE: `event: <type>\\ndata: <json>\\n\\n`."""

# errors.py
class ErrorEnvelope(BaseModel):
    code: Literal["unauthorized", "invalid_request", "not_found", "model_timeout", "provider_error"]
    message: str
    request_id: str
```

M1 的线程还存在进程内存里（一个 dict），M2 换成 PostgreSQL。

## 运行步骤

```bash
uv sync --all-groups
uv run uvicorn aiapp.api.app:create_app --factory --reload --port 8000
curl -s localhost:8000/healthz
curl -s -X POST localhost:8000/v1/threads -H "Authorization: Bearer dev-token" -H "Content-Type: application/json" -d '{}'
curl -N -X POST localhost:8000/v1/threads/<id>/messages -H "Authorization: Bearer dev-token" \
     -H "Content-Type: application/json" -d '{"content": "hello"}'
uv run pytest tests/api
```

## 验收证据

- [ ] `pytest tests/api` 全绿，且不需要任何 API Key
- [ ] `curl -N` 能看到 SSE 事件逐条到达，事件类型和第 07 课 `Thread` 的事件类型一致
- [ ] 没有 token 返回 401，坏 JSON 返回 422，两者都是同一个错误信封格式
- [ ] 失败注入：把 fake adapter 换成一个 `sleep(10)` 的 adapter，请求在配置的超时后返回 504，连接被正确关闭
- [ ] 断开客户端连接后服务端日志显示流被取消，没有残留任务
- [ ] 响应头里有 prompt 版本；改 `assistant.v2.md` 并切换配置后头部随之变化

## 依赖的课程

前置 P06, P08, P10；lessons/02, 03

---

[← 项目总览](../README.md)
