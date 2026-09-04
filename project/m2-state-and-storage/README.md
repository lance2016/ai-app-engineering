---
status: complete
kind: impl
depends_on: 前置 P09, P11, P12；lessons/06, 07
---

# M2 数据与状态

> 把第 07 课的事件线程从 JSON 文件搬进 PostgreSQL，把幂等键和运行锁放进 Redis。循环的写法一行不改，换的只是存储实现。做完这一步，服务重启不丢任务，两个进程抢写同一条线程只有一个能赢，重复的请求只产生一次副作用。

## 这一步加什么

- **Docker Compose**：仓库根目录 `docker-compose.yml`，PostgreSQL 16（pgvector 镜像，M4 直接用）加 Redis 7，一条命令起依赖，带健康检查
- **三张表**：`conversation`（租户、状态缓存）、`message`（即事件，一行一条）、`task`（一次运行一行，由 `run_started` 打开、`run_finished` / `run_failed` 关闭）。SQLAlchemy 2.0 声明式模型在 `storage/models.py`，Alembic 迁移在 `storage/migrations/`
- **`ThreadStore` 协议**换成三个方法：`create`、`load` 返回快照、`append(thread_id, event, expected_seq=)`。快照的意思是：改内存里的 `Thread` 不会写库，直到你带着"我期望写到第几位"去 `append`。`(conversation_id, seq)` 的唯一约束就是乐观锁：两个写者抢同一个位置，数据库只让一个成功，另一个拿到 `SeqConflict`
- **每步存盘**：`storage.flush(store, thread, persisted)` 把内存里新增的事件逐个 `append`。路由在每个事件 yield 给客户端后立即 flush，所以任意时刻崩溃最多丢正在飞的那一步，这是第 07 课"每步存盘"取舍的实现
- **Redis 只做两件事**：幂等键（`Idempotency-Key` 头，第 05 课）和"一个线程同时只有一个运行"的锁（第 07 课 double texting 的 reject 策略）。`KeyValueStore` 协议四个方法：`claim` 是 `SET NX EX`，`release` 用 Lua 脚本保证只有持有者能释放。Redis 不存任何事实，清空它系统照常工作，只是正在进行的锁和幂等记录没了
- **幂等重放**：同一个 `Idempotency-Key` 的第二次请求不再调模型，而是把第一次运行写进线程的那段事件按 SSE 重放，响应头带 `X-Idempotent-Replay: true`。失败的运行不记录，重试会真正重试
- **写入约束**：`human_input_requested` 之后不允许 `assistant_message`。Python 侧 `check_transition()` 在两种存储里都查；PostgreSQL 侧还有一个 `BEFORE INSERT` 触发器兜底，绕过 store 直接写库也会被拦，报 `check_violation`（23514）
- **两套实现过同一套契约测试**：`InMemoryThreadStore` + `InMemoryKeyValueStore` 用于课程和大部分测试，`PostgresThreadStore` + `RedisKeyValueStore` 用于真实运行。`tests/project/m2/` 的每个用例在两种后端上各跑一遍，真实后端不可达时自动跳过，CI 里用 service 容器跑

实际目录：

```text
docker-compose.yml
project/src/aiapp/storage/
├── base.py             # ThreadStore / KeyValueStore 协议, SeqConflict, InvalidTransition, check_transition(), flush()
├── memory.py           # InMemoryThreadStore, InMemoryKeyValueStore
├── models.py           # Conversation, Message, Task; 触发器 SQL
├── postgres.py         # PostgresThreadStore：append 的乐观锁、状态缓存、task 表记账
├── redis_kv.py         # RedisKeyValueStore：SET NX EX、只允许持有者释放的 Lua
├── alembic.ini
└── migrations/versions/0001_conversation_message_task.py
project/src/aiapp/api/routes/threads.py   # 每步 flush、运行锁、幂等重放
project/m2-state-and-storage/code/
└── 01_pause_resume_with_store.py         # 第 07 课的暂停恢复改用 ThreadStore，三个"进程"
tests/project/m2/
├── conftest.py                 # thread_store / kv_store 两种后端的参数化 fixture，自动跑迁移
├── test_thread_store_contract.py
├── test_kv_contract.py
└── test_api_m2.py
```

表结构：

```sql
conversation(id varchar(64) pk, tenant_id text not null, created_at timestamptz, status text)  -- status 是缓存，事实在 message
message(id bigserial pk, conversation_id fk, seq int not null, type text not null,
        data jsonb not null, created_at timestamptz, unique(conversation_id, seq))
task(id varchar(64) pk, conversation_id fk, started_at, finished_at, stop_reason text, tokens_in int, tokens_out int)
```

和设计稿的一处不同：`conversation.id` 用 `Thread.thread_id` 的字符串（`thr_xxxxxxxx`）而不是 uuid，这样第 07 课的代码和 API 里的 id 是同一个。

## 运行步骤

```bash
docker compose up -d --wait
export DATABASE_URL=postgresql+asyncpg://aiapp:aiapp@localhost:5432/aiapp
export REDIS_URL=redis://localhost:6379/0
uv run alembic -c project/src/aiapp/storage/alembic.ini upgrade head

uv run pytest tests/project/m2 -q            # 30 passed：每个用例在内存和真实后端各跑一遍
uv run python project/m2-state-and-storage/code/01_pause_resume_with_store.py            # 内存
DATABASE_URL=$DATABASE_URL uv run python project/m2-state-and-storage/code/01_pause_resume_with_store.py   # PostgreSQL
INJECT_CRASH=1 uv run python project/m2-state-and-storage/code/01_pause_resume_with_store.py

# 端到端：M1 的服务改用 PostgreSQL + Redis，其他不变
uv run uvicorn aiapp.api.app:create_app --factory
curl -N -X POST localhost:8000/v1/threads/<id>/messages -H "Authorization: Bearer dev-token" \
     -H "Content-Type: application/json" -H "Idempotency-Key: r1" -d '{"content": "hello"}'
# 同一条再发一次：不调模型，事件重放，响应头 X-Idempotent-Replay: true
# 重启服务后 GET /v1/threads/<id> 历史完整
```

不设 `DATABASE_URL` 和 `REDIS_URL` 时服务用内存实现，行为一样，重启丢数据。

## 验收证据

每一条对应 `tests/project/m2/` 里的测试或上面能手工复现的命令。

- [x] 迁移文件能从空库升到 head 再降回去再升上来（CI 的 "Migrations apply, roll back and re-apply" 步骤）
- [x] 同一套契约测试对内存实现和 PostgreSQL 实现都通过（`test_thread_store_contract.py` 六个用例 × 两种后端）；键值契约对内存和 Redis 都通过（`test_kv_contract.py`）
- [x] 第 07 课的暂停、恢复、崩溃恢复三个场景改用 `ThreadStore` 后行为不变，工具不重跑（`code/01_pause_resume_with_store.py`，两种存储）
- [x] 失败注入：两个"进程"同时向同一线程 `append`，一个成功一个 `SeqConflict`，没有丢事件也没有乱序（`test_two_writers_on_one_thread_one_loses`）
- [x] 重复请求带同一幂等键，第二次直接重放第一次的事件，模型只被调用一次，线程里只有一条 `user_message`（`test_same_idempotency_key_replays_without_a_second_model_call`）；失败的运行不被记录，重试真的重试（`test_failed_run_releases_the_lock_and_records_nothing_for_the_key`）
- [x] 运行中收到第二条消息返回 409，运行结束锁释放后下一轮正常（`test_second_message_during_a_run_is_rejected`、`test_lock_is_released_after_the_run_so_the_next_turn_works`）
- [x] 服务重启后 `GET /v1/threads/{id}` 返回完整历史，状态由 `message` 推导；PostgreSQL 里 `conversation.status` 缓存和推导结果一致，`task` 表有 stop_reason 和 token 数（`test_history_survives_a_process_restart`、`test_status_is_derived_from_the_log_after_a_restart`）
- [x] `human_input_requested` 之后写 `assistant_message` 被拒绝，Python 侧和数据库触发器各拦一层（`test_assistant_message_cannot_follow_human_input_requested`；直接 `psql` 插入也会报 `invalid_transition`）
- [x] 租户 A 读不到租户 B 的线程，和不存在的线程是同一个错误（`test_other_tenant_and_unknown_id_are_the_same_error`）

## 依赖的课程

前置 P09, P11, P12；lessons/06, 07

---

[← M1](../m1-api-skeleton/README.md) · [项目总览](../README.md) · [M3 →](../m3-tool-workflow/README.md)
