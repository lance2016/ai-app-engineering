---
status: complete
part: 背景知识
---

# 工程能力：读懂一个 AI 应用怎样运行

> 这页先讲到能读懂主线和参考实现的最低程度，再给出继续学习的路线。它不替代 Python、Web 或数据库教程；读完一节，知道自己缺哪块，直接沿着这一节的官方资料往下补。
>
> 最短起步组合是：能在终端里进入目录和设置环境变量；能读懂 Python 的变量、函数、类型、异常和 `async`；知道 HTTP 请求由什么组成；能看懂一条 SQL；知道测试、日志和容器分别解决什么问题。完全没接触过后端，先读下面的“零基础先认这些词”，不必一开始就理解后面的所有术语。

## 完全没接触过后端，先认这些词

主线课程面向会写一点 Python、准备做 AI 应用的开发者。如果“进程、端口、API、JSON”还没有清晰的画面，先看这一节。它只建立阅读后文所需的词汇，不要求现在就学会部署服务。

| 词 | 最小概念 | 在这门课里的样子 |
|---|---|---|
| 程序和进程 | 程序是写在文件里的指令；进程是这些指令正在运行的一次实例 | 运行参考项目后，Python 服务就是一个进程 |
| 函数和模块 | 函数接收输入并返回结果；模块是可以被别的文件导入的代码文件 | `runtime/loop.py` 里的函数负责推进一次循环 |
| 终端和文件系统 | 终端用文字命令启动程序；目录组织文件，路径告诉程序去哪里找它们 | `uv run ...` 启动项目，`project/src/` 是源码目录 |
| 数据和 JSON | Python 里的字符串、列表、字典是内存中的值；JSON 是在网络上传输这些值的一种文本格式 | API body 和模型响应通常是 JSON |
| 依赖和虚拟环境 | 依赖是项目借用的第三方库；虚拟环境把项目用的版本和系统 Python 分开 | `pyproject.toml` 声明依赖，`uv.lock` 固定版本 |
| 配置和环境变量 | 配置随运行环境变化；环境变量在启动时传给进程，密钥不写进源代码 | `.env.example` 说明需要哪些变量 |
| 客户端和服务器 | 客户端发起请求；服务器监听请求并返回结果 | Playground 是客户端，FastAPI 是服务器 |
| URL 和端口 | URL 指向资源；端口是主机上区分网络服务的编号，服务器进程监听它 | `localhost:8000` 表示本机的 8000 端口 |
| API 和协议 | API 是一组约定：用什么方法、传什么字段、返回什么状态；协议规定消息怎样交换 | `POST /v1/threads/{id}/messages` 是一条接口约定 |
| 内存和数据库 | 内存适合暂存当前运行的数据，进程退出后通常消失；数据库保存需要跨进程、跨重启保留的事实 | 事件线程最终写入 PostgreSQL |
| 异常和状态码 | 异常是程序内部没有得到预期结果；状态码是服务器给客户端的结果分类 | Python 捕获异常后，API 返回 4xx 或 5xx |
| 测试和日志 | 测试把预期写成可重复的检查；日志记录运行时发生了什么 | pytest 验证行为，trace 帮忙串起一次请求 |
| Git 和提交 | Git 保存一组可比较、可回退的修改；提交是其中一个明确的版本点 | 课程改动和参考项目都应能回到某个提交 |

把这些词串起来，一次请求大致是：

```text
浏览器或脚本
  └─ HTTP 请求（URL、方法、headers、JSON body）
      └─ API 进程（监听端口）
          ├─ 业务函数
          ├─ 模型或第三方 API
          ├─ 数据库
          └─ HTTP 响应（状态码、headers、JSON 或事件流）
```

这里的“进程”解释了服务为什么能持续接请求，“端口”解释了客户端为什么能找到它，“API”解释了双方怎样对齐字段；后文的 `async`、SSE、checkpoint 和 trace 都是在这条链上增加能力。不会某个词时，先回到[术语索引](../reference/glossary.md)查一句话定义。

### 零基础的第一段学习路线

先学变量、函数、条件、循环、异常、文件和模块，再学类型注解、`async` 和第三方库。哈佛的 [CS50P Python 入门课](https://cs50.harvard.edu/python/)按这个顺序组织，面向没有编程经验的人；需要查语法时，再看[Python 官方教程](https://docs.python.org/3/tutorial/)。两份资料访问日期均为 2026-09-10。

## 先建立一张图

一次请求通常会经过这些边界：客户端发 HTTP 请求，API 校验输入，运行时组装上下文并调用模型；模型返回文本或工具请求，运行时校验后才执行工具；状态和结果写入数据库，日志和 trace 记录这次请求经过了哪些边界。

| 边界 | 它解决的问题 | 主线落点 | 参考实现入口 |
|---|---|---|---|
| HTTP API | 请求怎样进来，错误怎样返回，流式结果怎样送回去 | 00、02、18 | [`api/routes/threads.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/routes/threads.py) |
| 运行时 | 循环什么时候停，状态怎样恢复，副作用怎样去重 | 06、07、09、10 | [`runtime/runner.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/runner.py) |
| 模型适配器 | 不同供应商的请求和响应怎样转换 | 01、02、23 | [`adapters/base.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/adapters/base.py) |
| 数据与状态 | 事实数据、事件、缓存和向量分别存在哪里 | 04、07、15、17 | [`storage/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/src/aiapp/storage)、[`knowledge/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/src/aiapp/knowledge) |
| 观测与控制 | 出错后怎样定位，怎样限制时间、成本和权限 | 19、20、21、22 | [`ops/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/src/aiapp/ops)、[`security/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/src/aiapp/security) |

读代码时先问这五个问题：输入从哪里来？谁校验它？谁改变外部世界？事实写到哪里？出了问题拿什么证据定位？这五个问题比记框架名更有用。

## Python：数据、错误和等待

### 类型和数据模型

类型注解主要给人和静态检查工具看，运行时默认不会替你校验数据。`dataclass` 适合表达应用内部的值对象；Pydantic 模型会在边界上解析和校验外部输入，还能生成 JSON Schema。一个工具参数既要有 Python 类型，也要有运行时校验，因为模型返回的参数仍是外部输入。

| 最低概念 | 这门课怎样用 | 参考实现 |
|---|---|---|
| `typing`、`Protocol`、`TypedDict` | 表达模型、工具、事件和存储接口 | [`adapters/base.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/adapters/base.py) |
| `dataclass` | 表达配置、事件和检索结果 | [`runtime/turn.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/turn.py) |
| Pydantic v2 | 校验 API 输入、工具参数并生成 schema | [`api/schemas.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/schemas.py)、[`runtime/registry.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/registry.py) |

官方资料访问日期均为 2026-09-10：[Python 类型注解](https://docs.python.org/3/library/typing.html)、[`dataclasses`](https://docs.python.org/3/library/dataclasses.html)、[Pydantic Models](https://docs.pydantic.dev/latest/concepts/models/)。先看类型、类和异常，再查 Pydantic 的模型与验证。

### 异常和错误边界

异常表示当前操作没有得到承诺的结果。调用方要先区分错误类型：输入不合法通常返回 4xx；下游暂时不可用可能重试；预算耗尽和权限不足应该停止；未知异常要记录上下文并返回通用错误。不要把所有异常都重试，也不要把 traceback 原样返回给用户。

参考实现把 API 错误、运行时错误和工具结果分开：[`api/errors.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/errors.py)、[`runtime/errors.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/errors.py)、[`runtime/runner.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/runner.py)。官方资料访问日期为 2026-09-10：[Python Errors and Exceptions](https://docs.python.org/3/tutorial/errors.html)。

### `async`、并发和取消

`async` 适合等待网络、数据库或文件 I/O。`await` 把控制权交回事件循环，其他任务可以在等待期间运行；它不会把 CPU 密集计算自动变成并行。并发也不等于并行：前者是交错推进多个任务，后者需要多个线程、进程或执行单元同时计算。

取消是正常控制流的一部分。用户断开连接、预算用完或超时后，运行时要把取消传到正在等待的模型和工具；吞掉取消异常会留下继续运行的后台任务。同步库放进异步处理函数，还会阻塞整个事件循环。

参考实现的并发和取消在 [`runtime/loop.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/loop.py)、[`runtime/budget.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/budget.py)；M0 用五个小实验对照顺序执行、`gather`、超时和取消。官方资料访问日期均为 2026-09-10：[asyncio](https://docs.python.org/3/library/asyncio.html)、[asyncio Tasks](https://docs.python.org/3/library/asyncio-task.html)、[FastAPI 并发与 async](https://fastapi.tiangolo.com/async/)。先理解 coroutine、task、取消和超时，再看框架怎样调用它们。

### 生成器和上下文管理器

生成器一次产出一个值，异步生成器可以边等待边产出事件，所以适合 SSE 和流式模型响应。上下文管理器把“开始、结束、异常时清理”绑定在一起，数据库事务、文件、trace span 都常用它。它们不是语法装饰，而是控制资源生命周期的工具。

参考实现的事件生成在 [`api/routes/threads.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/routes/threads.py)，trace 生命周期在 [`ops/telemetry.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/telemetry.py)。官方资料访问日期为 2026-09-10：[生成器](https://docs.python.org/3/tutorial/classes.html#generators)、[`contextlib`](https://docs.python.org/3/library/contextlib.html)。

## HTTP：把一次调用看成一组消息

HTTP 请求至少有方法、URL、headers 和可选 body；响应有状态码、headers 和可选 body。JSON 只是 body 的一种格式，schema 才说明字段、类型和必填关系。HTTP 本身无状态，应用要用 cookie、token 或自己的 thread id 关联多次请求。

| 概念 | 先理解什么 | 主线落点 |
|---|---|---|
| 方法语义 | `GET` 读取，`POST` 通常创建或触发动作，`PUT` 替换，`DELETE` 删除；是否幂等要看接口语义 | 02、05、17 |
| 状态码 | 4xx 多是请求或权限问题，5xx 多是服务或下游问题；具体语义以接口契约为准 | 02、21 |
| 超时与重试 | 超时只说明客户端没等到结果，不说明服务端没有完成；重试前要确认操作是否可重复 | 05、21 |
| SSE | 服务端在一个 HTTP 响应里连续发送事件；断线恢复需要事件 id 或 checkpoint | 02、07、18 |

### 常见 Web 词汇：知道它解决哪一层问题

这些词经常一起出现在项目文档里，但它们不在同一层。REST 是接口设计风格，HTTPS 是传输安全，Jinja2 是 HTML 模板工具；把它们都叫“后端框架”会混淆排查方向。

| 词 | 先形成的直觉 | 参考实现中的位置 | 优先级 |
|---|---|---|---|
| REST / RESTful | 用资源和 HTTP 方法表达操作的一组设计约束；HTTP API 不一定都满足完整 REST 约束 | `/v1/threads`、`/v1/knowledge` 是资源路径，`human-input` 这类动作接口仍要看契约和幂等性 | 现在理解 |
| HTTPS / TLS | HTTP 在 TLS 加密连接上传输；它保护传输过程并验证服务器身份，不负责判断用户有没有权限 | 本地参考项目用 HTTP 便于调试；公开部署时由入口层提供 HTTPS | 现在理解 |
| Cookie、Session、Bearer token | Cookie 通常由浏览器自动带回；Session 是服务器保存的会话状态；Bearer token 是请求主动携带的凭证 | 参考实现从 `Authorization: Bearer ...` 解析租户，见 [`api/deps.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/deps.py) | 现在理解 |
| CORS / Origin | 浏览器默认限制脚本跨来源读取响应；CORS 用响应头声明允许哪些来源，和服务端之间的调用无关 | Playground 和 API 由同一个 FastAPI 服务提供，不需要额外跨来源配置；拆成两个域名时再配置 | 遇到跨域再学 |
| Jinja2 | 服务端先把变量填进 HTML 模板，再把生成后的页面发给浏览器；它和返回 JSON 的 API 是两条输出路径 | 参考实现的 Playground 是静态 [`playground.html`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/static/playground.html)，没有使用 Jinja2 | 知道名字 |
| 反向代理 / 网关 | 站在应用前面接收域名和 HTTPS，再把请求转给应用；常放证书、压缩、限流和访问日志 | 参考实现本地直接运行 FastAPI；生产部署再看 M5 的[容器与部署说明](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/m5-production/README.md) | 遇到部署再学 |
| SSE 和 WebSocket | SSE 是服务器到浏览器的单向事件流；WebSocket 是双方都能持续发送消息的连接 | 文本 Playground 使用 SSE；语音方案只在[协议说明](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/demos/voice-agents.md)里讨论 WebSocket | 现在理解差异 |

官方资料访问日期均为 2026-09-10：[REST](https://developer.mozilla.org/en-US/docs/Glossary/REST)、[HTTPS](https://developer.mozilla.org/en-US/docs/Glossary/HTTPS)、[CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)、[Jinja 模板](https://jinja.palletsprojects.com/en/stable/templates/)、[WebSocket](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)。遇到一个词时先判断它属于接口、传输、浏览器还是部署层，再决定去哪里查。

名词的放置也按这个标准：主线需要拿来做判断的，写在工程能力正文；项目没用但读 Web 文档常会遇到的，放在本节表格；只需要查一句定义的，放[术语索引](../reference/glossary.md)；具体依赖版本和安装方式，放[技术选型](../reference/stack.md)或参考项目的启动说明。这样不会把工程能力页变成一张没有重点的名词清单。

一个最小请求链是：客户端先发 `POST /v1/threads` 建立线程，再发 `POST /v1/threads/{id}/messages` 发送消息。服务端校验 body 和权限后，以 JSON 或 `text/event-stream` 返回结果。模型输出的每个增量都只是一个事件，只有运行时写入事件存储后，客户端才有恢复依据。

官方资料访问日期均为 2026-09-10：[MDN HTTP 概览](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview)、[HTTP 方法](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods)、[状态码](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)、[Server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)。读完方法和状态码，再看主线第 02 课的流式与错误处理。

## 数据：事实、索引和缓存不是一回事

### 表、索引和查询

关系数据库用表保存事实，用约束保证字段和关系，用索引减少查询需要扫描的行。索引是读路径的加速结构，不能代替权限过滤，也不能证明写入已经成功。向量列只是表中的一种数据；租户、文档版本、权限和更新时间仍然需要普通字段和索引。

参考实现的表模型和 PostgreSQL 存储在 [`storage/models.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/storage/models.py)、[`storage/postgres.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/storage/postgres.py)、[`knowledge/postgres_store.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/knowledge/postgres_store.py)。官方资料访问日期均为 2026-09-10：[PostgreSQL Tutorial](https://www.postgresql.org/docs/current/tutorial.html)、[Indexes](https://www.postgresql.org/docs/current/indexes.html)、[pgvector](https://github.com/pgvector/pgvector)。

### 事务和迁移

事务把一组写入放进一个提交边界：全部成功才提交，失败则回滚。隔离级别决定一个事务能看到哪些并发写入；它不会替你解决业务幂等。迁移是数据库结构的版本控制，升级和回滚都要在 CI 中跑过，不能只在本地手动改表。

参考实现用 Alembic 管理迁移，入口在 [`storage/migrations/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/src/aiapp/storage/migrations)；CI 会执行升级、降级和再次升级，见 [`.github/workflows/ci.yml`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/.github/workflows/ci.yml)。官方资料访问日期均为 2026-09-10：[PostgreSQL Transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html)、[Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)。

### Redis、缓存和锁

Redis 适合保存有过期时间的缓存、短期幂等记录、限流桶和运行锁。它不是 PostgreSQL 事实表的替代品：缓存可以重建，事件和账单不能因为缓存丢失而失去。锁也只是并发控制，不能把外部支付和本地记录变成一个原子事务。

参考实现的 Redis 键值和锁在 [`storage/redis_kv.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/storage/redis_kv.py)、[`ops/ratelimit.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/ratelimit.py)。官方资料访问日期为 2026-09-10：[Redis 开发文档](https://redis.io/docs/latest/develop/)。先看数据类型、过期和事务，再看主线第 07、21 课为什么把事实数据和临时控制数据分开。

## 测试：验证每一层的承诺

测试不是“请求返回 200”就结束。单元测试验证一个纯函数；集成测试验证数据库、Redis 或 HTTP 边界；契约测试让内存实现和 PostgreSQL 实现遵守同一组接口；评测集验证模型行为；故障演练验证超时、断连和重启后的状态。

| 测试材料 | 它替代什么 | 参考实现 |
|---|---|---|
| fake model | 不稳定、昂贵的真实模型调用 | [`adapters/fake.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/adapters/fake.py) |
| fixture | 每个测试重复搭建的环境 | [`tests/project/m1/conftest.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/tests/project/m1/conftest.py) |
| monkeypatch / mock | 外部时间、环境变量和故障 | [`tests/project/m1/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/tests/project/m1) |
| golden set | “这次输出更好”的主观印象 | [`project/m5-production/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m5-production)、[`scripts/eval_run.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/scripts/eval_run.py) |
| chaos script | 假设服务永远正常 | [`scripts/chaos.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/scripts/chaos.py) |

fake 和 mock 的边界要分清：fake 是一个行为稳定、可以真正运行的替代实现；mock 更适合断言某个调用是否发生。两者都不能证明真实供应商的质量，所以模型评测和协议测试还要单独保留。

官方资料访问日期均为 2026-09-10：[pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)、[pytest monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)、[GitHub Actions](https://docs.github.com/en/actions)。学习顺序是 fixture 和参数化 → 替换外部依赖 → 在 CI 中运行 → 为模型和轨迹建立回归集。

## 日志、指标和 trace：给失败留下证据

日志回答“发生了什么”，指标回答“发生了多少”，trace 回答“一次请求经过了哪些步骤、每步花了多久”。一次模型请求至少要能关联 request id、thread id、model、工具名、耗时、token 用量和停止原因；这些字段要避免放入密钥、完整用户隐私和未经处理的 prompt。

参考实现的结构化日志、成本和 trace 在 [`ops/logging.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/logging.py)、[`ops/cost.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/cost.py)、[`ops/telemetry.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/telemetry.py)。第 20 课会把一条请求串成模型、工具、检索和存储的 span。

官方资料访问日期为 2026-09-10：[OpenTelemetry Observability primer](https://opentelemetry.io/docs/concepts/observability-primer/)。先分清 logs、metrics、traces，再看 trace context 怎样跨异步任务和 HTTP 边界传播。

## 容器、配置和部署

容器镜像是应用和依赖的只读打包，容器是这个镜像的一次运行。镜像本身不保存运行时数据；数据库卷、环境变量和密钥要单独管理。Compose 适合在本地把应用、PostgreSQL、Redis 和观测服务接成一组，生产环境还要考虑备份、滚动更新和资源限制。

健康检查至少分两类：`/healthz` 只说明进程还活着，`/readyz` 才说明依赖已经连好、可以接流量。收到 `SIGTERM` 后，进程应停止接新请求，等待正在写入的事件完成，再退出；否则重启可能留下半条流或未保存的 checkpoint。

参考实现的镜像、Compose、健康检查和退出处理在 [`Dockerfile`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/Dockerfile)、[`docker-compose.yml`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/docker-compose.yml)、[`ops/health.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/health.py)、[`runtime/runner.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/runner.py)。官方资料访问日期均为 2026-09-10：[Docker Compose](https://docs.docker.com/compose/)、[Dockerfile reference](https://docs.docker.com/reference/dockerfile/)。

## 工具链：让问题可以重现

终端、Git 和依赖锁文件解决的是同一个问题：别人能不能重建你看到的结果。环境变量把配置从代码中分开；`pyproject.toml` 描述项目和依赖；`uv.lock` 固定解析后的版本；Git 记录每次改变了什么。遇到失败时，先保存完整 traceback，再缩小输入、固定 seed、记录依赖版本和运行命令。

参考实现把项目元数据和锁文件放在 [`pyproject.toml`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/pyproject.toml)、[`uv.lock`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/uv.lock)，启动配置示例在 [`.env.example`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/.env.example)。官方资料访问日期均为 2026-09-10：[Pro Git](https://git-scm.com/book/en/v2)、[uv 项目结构](https://docs.astral.sh/uv/concepts/projects/layout/)、[uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)、[Missing Semester Shell Tools](https://missing.csail.mit.edu/2020/course-shell/)。

## 安全边界：谁能让系统做什么

认证回答“你是谁”，授权回答“你能做什么”。最小权限意味着工具注册表、数据库查询、文件访问和管理操作都要按用户、租户和资源范围限制。把 `tenant_id` 从请求一路传到 repository、事件、成本和 trace，才能在每一层检查边界；只在前端隐藏按钮不算授权。

密钥只进运行时配置，不进仓库、镜像、日志和 trace。用户输入、检索文档和 MCP/Skill 内容都可能包含指令，模型可以提出工具调用，但不能凭这段文字获得新的权限。工具白名单、参数校验、人工确认、幂等和审计要由确定性代码执行。

参考实现的出站限制在 [`security/outbound.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/security/outbound.py)，工具权限和租户过滤分布在 [`runtime/registry.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/registry.py)、[`api/deps.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/deps.py) 和存储层。官方资料访问日期为 2026-09-10：[OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/)。先看风险名称，再回到主线第 05、12、22 课看代码怎样挡住它们。

## 参考实现：按这个顺序观察

参考实现默认使用 fake model，先把协议、状态和失败路径跑通，再替换真实供应商。下面的顺序对应仓库里的里程碑，不要求把所有代码一次读完。

| 阶段 | 先观察什么 | 运行入口或测试 |
|---|---|---|
| M0 并发 | 顺序、并发、超时、取消的差异 | [`project/m0-concurrency/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m0-concurrency) |
| M1 API 骨架 | fake adapter、HTTP schema、结构化错误 | [`tests/project/m1/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/tests/project/m1) |
| M2 数据与状态 | 事件、checkpoint、PostgreSQL、Redis 锁 | [`project/m2-state-and-storage/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m2-state-and-storage) |
| M3 工具与运行时 | 注册、白名单、确认、幂等和恢复 | [`project/m3-tool-workflow/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m3-tool-workflow) |
| M4 检索与记忆 | 入库、引用、混合检索和记忆生命周期 | [`project/m4-rag-and-memory/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m4-rag-and-memory) |
| M5 生产化 | 评测、trace、限流、成本、容器和故障演练 | [`project/m5-production/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m5-production) |

课程按理解顺序排，参考实现按装配顺序排。想边读边跑，先看[参考项目路线](../reference/project-playbook.md)；想只补一个概念，直接从上面的章节入口跳进去。

## 推荐学习路线

下面按“先能读代码，再能运行服务，最后能判断线上问题”的顺序排列。每一步先看概念页，再回到课程和参考实现中找它的落点。

| 阶段 | 先掌握 | 推荐资料 |
|---|---|---|
| 0. 编程入门 | 变量、函数、条件、循环、异常、文件和模块 | [CS50P Python 入门课](https://cs50.harvard.edu/python/)、[Python Tutorial](https://docs.python.org/3/tutorial/) |
| 1. Python 与终端 | 类型、异常、`async`、路径、环境变量、Git | [Python Tutorial](https://docs.python.org/3/tutorial/)、[Pro Git](https://git-scm.com/book/en/v2)、[Shell Tools](https://missing.csail.mit.edu/2020/course-shell/) |
| 2. HTTP 服务 | 方法、状态码、JSON、schema、超时、SSE | [MDN HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview)、[FastAPI async](https://fastapi.tiangolo.com/async/)、[MDN SSE](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) |
| 3. 数据与并发 | SQL、索引、事务、迁移、Redis、取消 | [PostgreSQL Tutorial](https://www.postgresql.org/docs/current/tutorial.html)、[Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)、[Redis 开发文档](https://redis.io/docs/latest/develop/)、[asyncio](https://docs.python.org/3/library/asyncio.html) |
| 4. 测试与证据 | fixture、替身、契约测试、golden set、CI | [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)、[pytest monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)、[GitHub Actions](https://docs.github.com/en/actions) |
| 5. 运行与安全 | 镜像、Compose、健康检查、日志、trace、最小权限 | [Docker Compose](https://docs.docker.com/compose/)、[OpenTelemetry primer](https://opentelemetry.io/docs/concepts/observability-primer/)、[OWASP LLM Top 10](https://genai.owasp.org/llm-top-10/) |

上表链接访问日期均为 2026-09-10。资料很多时不要从头通读：先看目录和示例，再拿参考实现中的一个请求或一个失败测试对照。

## 从哪里开始

| 你的情况 | 建议 |
|---|---|
| 没写过程序，也不了解后端 | 先走“零基础的第一段学习路线”，掌握变量、函数、条件、循环和文件，再回到这页的 Python 与终端 |
| Python 和后端基本熟悉，没做过 AI 应用 | 读第 00 课；遇到表格里的“用到再学”再回来补 |
| 只缺 Python 基础 | 先看“Python”一节，再补类型、异常、`asyncio` 和 pytest |
| 只缺服务和数据库基础 | 先看“HTTP”和“数据”两节，再读第 02、05、07 课 |
| 想直接跑项目 | 按[参考项目路线](../reference/project-playbook.md)从 M0 或 M1 开始；fake model 不需要 API key |
| 想补模型原理 | 回到[背景知识总览](./README.md)的 F00–F07，不必先读完工程能力 |

## 这门课不要求你先学什么

- **训练和微调模型。** 第 23 课讲什么时候考虑微调、怎样估显存和成本，但不要求自己训练模型。
- **深度学习框架。** LLM 原理的八篇小实验只用 Python 标准库。
- **线性代数和概率论的完整推导。** 主线需要的向量、余弦和采样直觉在 LLM 原理的对应章节里给出。
- **前端框架。** 第 24 课只讲交互状态、确认和反馈，不要求 React。
- **Kubernetes。** 第 21 课到容器、CI、灰度和回滚；更大的编排系统不影响主线理解。

---

[背景知识总览](./README.md) · [算法与数学](./algorithm-foundations.md)
