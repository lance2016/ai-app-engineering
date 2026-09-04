---
status: complete
kind: impl
depends_on: 前置 P06, P08, P10；lessons/02, 03
---

# M1 API 骨架

> 把第 00 课的 `aiapp` 包装成一个能被 HTTP 调用的服务：健康检查、鉴权、创建线程、发消息并以 SSE 流式返回、结构化错误、system prompt 版本化。模型仍然默认 fake，所以整套服务离线就能跑通测试；换 `MODEL_PROVIDER=deepseek` 一行代码不改。

## 这一步加什么

- **FastAPI 应用**：`aiapp.api.create_app()` 工厂，`fastapi`、`uvicorn`、`httpx` 从 `prereq` 依赖组提升为主依赖
- **四个端点**：`GET /healthz`；`POST /v1/threads` 建线程；`POST /v1/threads/{id}/messages` 发消息并以 SSE 流式返回本轮事件；`GET /v1/threads/{id}` 读整条事件线程
- **鉴权**：`Authorization: Bearer <token>`，token 到租户 id 的映射来自 `AIAPP_TOKENS` 环境变量；别的租户的线程一律 404，不区分"不存在"和"不是你的"
- **结构化错误**：统一信封 `{code, message, request_id}`。缺 token 401，坏 JSON 422，线程不存在 404，模型首块超时 504，供应商报错 502，未捕获 500。每个响应带 `X-Request-ID`，客户端可以自带
- **system prompt 版本化**：`aiapp/prompts/assistant.v1.md`、`assistant.v2.md`，`AIAPP_PROMPT_VERSION` 选版本，启动时就加载（文件不存在直接起不来），每次流式响应的 `X-Prompt-Version` 头告诉你用的是哪版
- **一轮对话的运行时** `aiapp.runtime.run_turn()`：追加 `user_message`，流式调模型，把文本增量作为 `assistant_delta` 推给客户端但不存，最后追加 `assistant_message` 和 `run_finished`。M3 会把它换成带工具的循环，接口不变
- **超时的两个阶段**：模型第一块到达之前超时或报错，运行时把 `run_failed` 记进线程并抛给路由，路由返回真正的 504 / 502，因为还没有任何字节发给客户端；第一块之后卡住，流里发一条 `run_failed` 事件后结束，HTTP 状态已经是 200 改不了了。这就是为什么 `run_turn` 在拿到第一块之前什么都不 yield
- **失败注入**：`AIAPP_INJECT=slow_model` 把模型包成延迟 10 秒的版本，`AIAPP_INJECT=provider_error` 包成必报错的版本。包装器在 `aiapp/adapters/inject.py`，测试也用它们
- **测试** `tests/project/m1/`：16 个用例，`TestClient` 打真实的 ASGI 应用，不需要任何 key

实际目录：

```text
project/src/aiapp/
├── config.py               # Settings.from_env(): AIAPP_TOKENS / AIAPP_PROMPT_VERSION / AIAPP_MODEL_TIMEOUT_S / AIAPP_INJECT
├── prompts/                # load_prompt("assistant", "v1") -> assistant.v1.md
├── storage/
│   ├── base.py             # ThreadStore 协议, ThreadNotFound
│   └── memory.py           # InMemoryThreadStore：一个 dict，M2 换 PostgreSQL
├── runtime/turn.py         # run_turn(): 一轮对话，先拿到模型第一块再 yield
├── adapters/inject.py      # SlowAdapter, FailingAdapter, apply_injection()
└── api/
    ├── app.py              # create_app(), request id 中间件, 装错误处理器和路由
    ├── deps.py             # get_tenant(token) -> Tenant, get_store / get_model / get_settings
    ├── errors.py           # ErrorEnvelope, AppError 家族, 异常到状态码的映射
    ├── schemas.py          # CreateThreadRequest, MessageRequest, ThreadView
    └── routes/{health,threads}.py
tests/project/m1/
├── conftest.py             # make_client(), StallingAdapter, parse_sse()
├── test_health.py
├── test_threads.py
└── test_errors.py
```

M1 的线程存在进程内存里，重启就没了。M2 换成 PostgreSQL，`ThreadStore` 协议不变。

## 运行步骤

```bash
uv sync
uv run pytest tests/project/m1 -q                         # 16 passed，不需要 key

uv run uvicorn aiapp.api.app:create_app --factory --port 8000
curl -s localhost:8000/healthz
curl -s -X POST localhost:8000/v1/threads -H "Authorization: Bearer dev-token" \
     -H "Content-Type: application/json" -d '{}'          # 记下 thread_id
curl -N -X POST localhost:8000/v1/threads/<id>/messages -H "Authorization: Bearer dev-token" \
     -H "Content-Type: application/json" -d '{"content": "hello"}'
curl -s localhost:8000/v1/threads/<id> -H "Authorization: Bearer dev-token"

# 换真实模型：其他命令不变
MODEL_PROVIDER=deepseek uv run uvicorn aiapp.api.app:create_app --factory

# 失败注入：模型 10 秒才响应，超时设 0.5 秒，看 504 在 0.5 秒后到达
AIAPP_INJECT=slow_model AIAPP_MODEL_TIMEOUT_S=0.5 uv run uvicorn aiapp.api.app:create_app --factory
AIAPP_INJECT=provider_error uv run uvicorn aiapp.api.app:create_app --factory   # 502

# 换提示词版本
AIAPP_PROMPT_VERSION=v2 uv run uvicorn aiapp.api.app:create_app --factory       # 响应头 X-Prompt-Version: v2
```

`dev-token` 到 `tenant-demo` 的映射是开发默认值，生产必须设 `AIAPP_TOKENS=token1:tenant-a,token2:tenant-b`。

## 验收证据

每一条对应 `tests/project/m1/` 里的测试，或一条能手工复现的命令。

- [x] `pytest tests/project/m1` 全绿，不需要任何 API Key（16 个用例）
- [x] `curl -N` 能看到 SSE 事件逐条到达，事件类型和第 07 课 `Thread` 的事件类型一致；文本增量是额外的 `assistant_delta` 事件，只流不存（`test_send_message_streams_lesson_07_events_then_persists_them`）
- [x] 没有 token 返回 401，坏 JSON 和缺字段返回 422，两者是同一个错误信封（`test_errors.py` 前两个用例）
- [x] 别的租户读不到我的线程，返回 404 而不是 403（`test_threads_are_invisible_to_other_tenants`）
- [x] 失败注入：把 fake adapter 换成延迟 10 秒的 adapter，请求在配置的超时后返回 504，线程状态变为 `failed` 并记录了原因（`test_slow_model_becomes_504_before_any_bytes_are_streamed`，以及上面 `AIAPP_INJECT=slow_model` 的 curl）
- [x] 供应商报错返回 502，错误细节只进日志不进响应（`test_provider_outage_becomes_502`）
- [x] 模型发出第一块后卡住，流内收到 `run_failed` 事件而不是连接挂死（`test_stall_after_first_chunk_ends_the_stream_with_run_failed`）
- [x] 响应头里有 prompt 版本；切到 `v2` 后头部和模型看到的 system prompt 一起变（`test_switching_prompt_version_changes_header_and_prompt`）
- [x] 模型每一轮看到的消息是 system prompt 加完整历史（`test_model_sees_versioned_system_prompt_then_history`）
- [ ] 断开客户端连接后服务端日志显示流被取消，线程末尾多一条 `client_disconnected` 的 `run_failed`。代码路径在 `routes/threads.py` 的 `events()` 里，`TestClient` 没法模拟中途断开，手工验证方法：用 `MODEL_PROVIDER=deepseek` 起服务，`curl -N` 后在流式输出中间 Ctrl+C，看服务端日志。M5 的故障演练脚本会把这条自动化

## 依赖的课程

前置 P06, P08, P10；lessons/02, 03

---

[← 项目总览](../README.md) · [M2 →](../m2-state-and-storage/README.md)
