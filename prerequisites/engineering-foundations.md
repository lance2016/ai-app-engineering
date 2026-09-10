---
status: complete
part: 背景知识
---

# 工程能力：读懂、跑通和排查这门课的代码

> 这页是索引，不是另一套 Python 或后端教程。它回答三个问题：主线开始前要会什么、遇到具体主题去哪补、在参考实现里先看哪个文件。
>
> 最小开工组合是：会在终端里进入目录并设置环境变量，会读 Python 的类型注解、`dataclass`、异常和 `async`，能看懂 HTTP/JSON，能写一条 SQL，能用 `pytest` 验证一个结果。其他能力可以跟着课程补。
>
> **必备**表示缺了会卡住主线；**用到再学**表示遇到对应课程再补；**可选**表示有帮助，但不影响主线。每一项都只列这门课实际会碰到的范围。

## 先按这条路线补

| 你要做的事 | 先补的能力 | 参考实现里的入口 |
|---|---|---|
| 读懂第 00–05 课 | 类型注解、`dataclass`、异常、HTTP/JSON、环境变量 | [`src/aiapp/adapters/base.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/adapters/base.py)、[`api/errors.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/errors.py) |
| 读懂第 06–14 课 | `asyncio`、取消、生成器、SQL 事务、Redis、MCP 的进程通信 | [`runtime/loop.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/loop.py)、[`storage/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/src/aiapp/storage)、[`mcp/client.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/mcp/client.py) |
| 读懂第 15–18 课 | 文档入库、迁移、数据库索引、请求链和 SSE | [`knowledge/ingest.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/knowledge/ingest.py)、[`api/routes/threads.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/routes/threads.py) |
| 读懂第 19–23 课 | 测试分层、日志与 trace、限流、容器、配置和安全边界 | [`tests/project/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/tests/project)、[`ops/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/src/aiapp/ops)、[`.github/workflows/ci.yml`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/.github/workflows/ci.yml) |

参考实现默认用 fake model，先跑通协议和失败路径，再接真实模型。第一次可以按[参考项目路线](../reference/project-playbook.md)走，不需要先把下面所有项目学完。

## Python

| 项 | 档 | 这门课哪里用到它 |
|---|---|---|
| 类型注解（`typing`） | 必备 | 工具契约、状态、事件和适配器接口都靠它表达 |
| `dataclass` | 必备 | 工具参数、事件、候选模型、检索结果和配置对象 |
| 异常与自定义异常 | 必备 | 第 06 课按错误类型选择重试、停止或回退 |
| `async` / `await` | 必备 | 第 06 课起的模型调用、并行工具和流式响应 |
| 上下文管理器（`with`） | 用到再学 | 第 20 课用它管理 span 的开始、结束和异常状态 |
| 生成器与异步生成器 | 用到再学 | 第 02 课的 `async for` 消费增量事件 |
| Pydantic v2 | 用到再学 | 第 05 课用同一份模型定义校验工具参数和生成 schema |
| `asyncio` 的任务、取消与超时 | 用到再学 | 第 06 课的预算与取消，第 21 课的超时和重试 |
| `contextvars` | 可选 | 第 20 课在异步任务间关联 trace；线程池不会自动继承上下文 |

**去哪学。** 只读对应范围，不必通读整套文档。链接访问日期均为 2026-09-10。

| 想补的项 | 去哪学 | 读哪几节 |
|---|---|---|
| 类型注解 | [mypy 类型速查表](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html) | 常用类型、联合类型、泛型 |
| `Protocol`、泛型、`TypedDict` | [`typing` 模块文档](https://docs.python.org/3/library/typing.html) | 需要时查，不通读 |
| `dataclass`、异常、生成器 | [Python 官方教程](https://docs.python.org/3/tutorial/) | 类、异常、生成器 |
| `async` / `await` | [`asyncio` 文档](https://docs.python.org/3/library/asyncio.html) | coroutine、task、`gather`、取消 |
| 任务和超时 | [`asyncio` 任务文档](https://docs.python.org/3/library/asyncio-task.html) | `Task`、取消、`wait_for` 和 timeout |
| 上下文管理器 | [`contextlib` 文档](https://docs.python.org/3/library/contextlib.html) | `@contextmanager` 和异步上下文管理器 |
| Pydantic v2 | [Pydantic 文档](https://docs.pydantic.dev/latest/) | Models、Validators、JSON Schema |

## 工具链与工程协作

这些能力不会出现在某一段 Agent 代码里，却决定你能不能复现一次运行、确认改动来自哪里、在另一台机器上重建环境。

| 项 | 档 | 这门课哪里用到它 |
|---|---|---|
| 终端、路径、管道和环境变量 | 必备 | 第 00 课启动服务、设置模型和数据库配置；所有参考项目命令都从终端执行 |
| Git 基础与代码 review | 必备 | 每次实验要比较改动、保留回滚点；第 26 课的 ADR 也应和代码一起版本化 |
| `pyproject.toml`、虚拟环境和 `uv` | 必备 | 用 `uv sync` 重建环境，用 `uv run` 在项目环境里执行测试和脚本 |
| 锁文件与可复现安装 | 用到再学 | 参考实现把 `uv.lock` 提交到仓库；部署镜像用冻结的依赖安装 |
| 读 traceback、缩小复现样本 | 必备 | 每一课的失败案例都要先定位层，再判断是模型、工具、数据还是基础设施 |
| 格式化、静态检查和类型检查 | 可选 | 改动较大时减少低级错误；它们不能代替运行时测试和评测 |

| 想补的项 | 去哪学 | 读哪几节 |
|---|---|---|
| 命令行 Git | [Pro Git · Git 基础](https://git-scm.com/book/en/v2) | Getting Started、Basic Git Workflow、撤销改动 |
| Python 项目与锁文件 | [uv · 项目结构](https://docs.astral.sh/uv/concepts/projects/layout/) | `pyproject.toml`、虚拟环境、`uv.lock` |
| 安装与冻结依赖 | [uv · Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/) | `uv sync`、`--locked`、`--frozen` |
| 终端和环境变量 | [The Missing Semester · Shell Tools](https://missing.csail.mit.edu/2020/course-shell/) | 路径、重定向、管道、环境变量 |

## Web、并发与数据

| 项 | 档 | 这门课哪里用到它 |
|---|---|---|
| HTTP 方法、状态码、超时和重试 | 必备 | 第 02、21 课根据状态码和错误类型决定是否重试 |
| REST、JSON 和 schema | 必备 | 模型适配器、工具调用和 `/v1` 接口都交换结构化数据 |
| SQL（建表、查询、索引） | 必备 | 第 04 课的 pgvector、第 07 课事件线程、第 17 课文档版本和删除 |
| 事务、隔离和迁移 | 用到再学 | 第 07、17 课保证 checkpoint、事件和删除的一致性；参考实现用 Alembic 管迁移 |
| `asyncio` 并发模型 | 用到再学 | 第 06 课并行工具、第 07 课运行锁、第 21 课限流和超时 |
| SSE（Server-Sent Events） | 用到再学 | 第 02、18 课把增量事件送到客户端，断线后按事件序号恢复 |
| Redis 的锁、缓存和限流桶 | 用到再学 | 第 07、21 课；需要分清可重建缓存和事实数据 |
| WebSocket | 可选 | 语音或客户端持续上行时使用；主线文本示例用 SSE |
| 消息队列 | 可选 | 第 10 课长任务会比较队列和同步请求，但主线不要求自己搭建队列 |

| 想补的项 | 去哪学 | 读哪几节 |
|---|---|---|
| HTTP 与状态码 | [MDN · HTTP 指南](https://developer.mozilla.org/en-US/docs/Web/HTTP) | 方法、状态码、缓存和连接 |
| SSE | [MDN · Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) | `EventSource`、事件格式和重连 |
| SQL、索引、事务 | [PostgreSQL 官方文档](https://www.postgresql.org/docs/current/) | SQL、索引、事务 |
| 数据库迁移 | [Alembic 教程](https://alembic.sqlalchemy.org/en/latest/tutorial.html) | 创建迁移、升级、回滚 |
| pgvector | [pgvector](https://github.com/pgvector/pgvector) | 建表、距离查询和索引 |
| FastAPI 并发模型 | [FastAPI · Concurrency and async](https://fastapi.tiangolo.com/async/) | `def` 与 `async def` 的选择 |
| Redis | [Redis 开发文档](https://redis.io/docs/latest/develop/) | 数据类型、过期和事务 |

## 测试、观测与运行

工程能力不止是“接口返回 200”。这门课会把成功路径、失败路径、评测集和运行证据放在一起看。

| 项 | 档 | 这门课哪里用到它 |
|---|---|---|
| pytest、fixture 和参数化 | 必备 | 第 19 课把确定性断言、golden set 和回归门禁放进测试 |
| fake、mock 和故障注入 | 用到再学 | 第 00–07 课的离线适配器、第 21 课的超时、供应商故障和预算演练 |
| 结构化日志 | 用到再学 | 第 20 课用 JSON 日志记录 request、thread、trace 和停止原因 |
| trace、span 和上下文传播 | 用到再学 | 第 20 课定位一次请求经过了哪些模型、工具和数据边界 |
| CI 工作流 | 用到再学 | 第 19、21 课把测试、评测、迁移、故障演练和镜像构建串起来 |
| Docker 与 Compose | 用到再学 | 第 18、21 课起 PostgreSQL、Redis、Phoenix 和应用服务 |
| 配置、密钥与健康检查 | 用到再学 | 第 00、21、22 课区分配置和密钥，区分 `/healthz` 与 `/readyz` |
| 进程退出与重启 | 可选 | 第 07、10 课验证 checkpoint、取消和恢复；了解 `SIGTERM` 有助于部署排查 |

| 想补的项 | 去哪学 | 读哪几节 |
|---|---|---|
| pytest fixture 与参数化 | [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html) | fixture、参数化、作用域 |
| 测试替身与环境隔离 | [pytest monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html) | `setenv`、替换依赖、恢复环境 |
| CI 工作流 | [GitHub Actions 文档](https://docs.github.com/en/actions) | workflow、job、service container、artifact |
| Docker 与 Compose | [Docker Compose](https://docs.docker.com/compose/) | 服务、网络、卷和健康检查 |
| 日志、指标与 trace | [OpenTelemetry Observability primer](https://opentelemetry.io/docs/concepts/observability-primer/) | logs、metrics、spans、trace 和关联关系 |

参考实现里的对应入口：[`tests/project/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/tests/project) 是分里程碑的测试，[`scripts/chaos.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/scripts/chaos.py) 是故障演练，[`ops/telemetry.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/telemetry.py) 和 [`ops/logging.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/logging.py) 是观测入口，`.github/workflows/ci.yml` 把它们放进同一条 CI。

## 安全边界

| 项 | 档 | 这门课哪里用到它 |
|---|---|---|
| 鉴权与最小权限 | 必备 | 第 05、22 课限制工具、资源和管理操作的可见范围 |
| 租户上下文与数据过滤 | 用到再学 | 第 07、18、22 课；`tenant_id` 要从请求传到 repository、事件、成本和 trace |
| 密钥和敏感数据处理 | 用到再学 | 第 00、20、22 课；密钥进运行时，prompt、日志和 trace 做脱敏 |
| 依赖和供应链边界 | 可选 | 第 13、22 课的 Skill / MCP 加载、白名单和内容校验 |

去哪学：先读 [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/) 的风险名称，再回到[第 22 课](../lessons/security-governance/README.md)看确定性代码怎样挡住它们。访问日期为 2026-09-10。

## 这门课不要求你先学什么

- **训练和微调模型。** 第 23 课讲什么时候考虑微调、怎样估显存和成本，但不要求自己训练模型。
- **深度学习框架。** LLM 原理的八篇小实验只用 Python 标准库。
- **线性代数和概率论的完整推导。** 主线需要的向量、余弦和采样直觉在 LLM 原理的对应章节里给出。
- **前端框架。** 第 24 课只讲交互状态、确认和反馈，不要求 React。
- **Kubernetes。** 第 21 课到容器、CI、灰度和回滚；更大的编排系统不影响主线理解。

## 从哪里开始

| 你的情况 | 建议 |
|---|---|
| Python 和后端基本熟悉，没做过 AI 应用 | 先读[第 00 课](../lessons/setup/README.md)，遇到表格中的“用到再学”再补 |
| 只缺 Python 基础 | 先补类型注解、`dataclass`、异常、`asyncio` 和 pytest，再读第 00 课 |
| 只缺数据库和服务基础 | 先补 HTTP/JSON、SQL、事务、SSE，再从第 05 或第 07 课切入 |
| 想直接跑项目 | 按[参考项目路线](../reference/project-playbook.md)执行；fake model 不需要 API key |
| 想补模型原理 | 回到[背景知识总览](./README.md)的 F00–F07，不必先读完工程能力页 |

---

[背景知识总览](./README.md) · [算法与数学](./algorithm-foundations.md)
