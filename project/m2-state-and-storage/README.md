---
status: draft
kind: impl
depends_on: 前置 P09, P11；lessons/06, 07
---

# M2 数据与状态

> 把第 07 课的事件线程从 JSON 文件搬进 PostgreSQL，把幂等键和运行锁放进 Redis。`run()` 一行不改，换的只是存储实现。做完这一步，服务重启不丢任务，用户回来能续上。

## 这一步加什么

- **Docker Compose**：PostgreSQL 16 加 Redis 7，一条命令起依赖
- **三张表**：`conversation`、`message`（即事件）、`task`（运行记录）；SQLAlchemy 2.0 声明式模型；Alembic 迁移
- **`ThreadStore` 协议**：替换 `Thread.save()` / `Thread.load()`，先有内存实现再有 PostgreSQL 实现，测试同时跑两个实现
- **Redis 用途只有两个**：幂等键（第 05 课）和"一个线程同时只有一个运行"的锁（第 07 课 double texting 的 reject 策略）。Redis 不存任何事实来源
- **写入约束**：`human_input_requested` 之后不允许 `assistant_message`，在存储层用检查约束或触发器兜底，对应第 07 课练习 5

表结构：

```sql
conversation(id uuid pk, tenant_id text not null, created_at timestamptz, status text)   -- status 是缓存，事实在 message
message(id bigserial pk, conversation_id uuid fk, seq int not null, type text not null,
        data jsonb not null, created_at timestamptz, unique(conversation_id, seq))
task(id uuid pk, conversation_id uuid fk, started_at, finished_at, stop_reason text, tokens_in int, tokens_out int)
```

关键接口：

```python
class ThreadStore(Protocol):
    async def load(self, thread_id: str, *, tenant_id: str) -> Thread: ...
    async def append(self, thread_id: str, event: Event, *, expected_seq: int) -> None:
        """Optimistic concurrency: fails if another writer appended first."""
    async def create(self, tenant_id: str) -> Thread: ...

class IdempotencyStore(Protocol):
    async def claim(self, key: str, ttl_s: int) -> bool: ...      # SET NX
    async def record(self, key: str, result: str) -> None: ...
```

目标目录：`project/src/aiapp/storage/{models.py, postgres.py, memory.py, redis.py}`，`project/src/aiapp/storage/migrations/`，`docker-compose.yml` 在仓库根目录。

## 运行步骤

```bash
docker compose up -d postgres redis
uv run alembic -c project/src/aiapp/storage/alembic.ini upgrade head
DATABASE_URL=postgresql+asyncpg://... REDIS_URL=redis://localhost:6379 uv run pytest tests/storage
# 端到端：M1 的服务改用 PostgresThreadStore
uv run uvicorn aiapp.api.app:create_app --factory
```

## 验收证据

- [ ] 迁移文件能从空库升到 head 再降回去
- [ ] 同一套 `tests/storage` 对内存实现和 PostgreSQL 实现都通过
- [ ] 第 07 课的 `02_pause_resume.py` 改用 `ThreadStore` 后，暂停、恢复、崩溃恢复三个场景行为不变
- [ ] 失败注入：两个进程同时向同一线程 `append`，一个成功一个因 `expected_seq` 不匹配失败，没有丢事件也没有乱序
- [ ] 重复请求带同一幂等键，第二次直接返回第一次的结果，数据库里只有一次副作用
- [ ] 服务重启后 `GET /v1/threads/{id}` 返回完整历史，状态由 `message` 推导而不是读 `conversation.status`

## 依赖的课程

前置 P09, P11；lessons/06, 07

---

[← 项目总览](../README.md)
