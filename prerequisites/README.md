# 前置｜Python 与后端基础

> 面向零基础或只会一点 Python 的读者。12 个模块，学完能独立写一个带类型、校验、测试和数据库的 async Web 服务，这是主线课程的起点。
> 已经有后端经验的人做一遍下面的自检，缺哪个补哪个，不用从头学。

## 自检

每一条都能做到，就直接去 [主线第 00 课](../lessons/00-setup/README.md)。

- [ ] 会用 uv 建虚拟环境、装依赖、跑脚本
- [ ] 能读懂并写出带类型注解的函数、dataclass 和 Pydantic 模型
- [ ] 能解释 coroutine、Task、事件循环的关系；知道同步 I/O 为什么会阻塞整个服务；用过 `TaskGroup` 和 `timeout`
- [ ] 写过 FastAPI 接口，知道状态码语义、鉴权头、依赖注入
- [ ] 会建表、加索引、写 JOIN；能解释一种事务隔离级别；用过 SQLAlchemy 2.0 和 Alembic
- [ ] 用 pytest 写过 fixture 和参数化测试
- [ ] 会 Git 分支、rebase、解决冲突；会 Docker Compose 起依赖

## 模块

| # | 模块 | 一句话 | 主线落点 | 状态 |
|---|---|---|---|---|
| P00 | [环境与工具链](./python/00-setup-and-tooling/README.md) | 装好 Python 3.12 和 uv，会用终端、虚拟环境、REPL 和编辑器，能跑第一个脚本 | lessons/00 | complete |
| P01 | [Python 基础语法](./python/01-python-basics/README.md) | 变量、数字与字符串、条件与循环、函数与作用域 | 全部 | complete |
| P02 | [容器与迭代](./python/02-collections-and-iteration/README.md) | list / dict / set / tuple、切片、推导式、生成器、`enumerate` / `zip` | lessons/02 | complete |
| P03 | [模块、异常与日志](./python/03-modules-errors-and-logging/README.md) | 把代码拆成模块和包；用异常表达失败并正确捕获；用 logging 而不是 print | lessons/05, 19 | complete |
| P04 | [类、dataclass 与 Protocol](./python/04-oop-and-dataclasses/README.md) | 类和实例、`@dataclass`、`Protocol` 鸭子类型 | lessons/05, 06, 07 | complete |
| P05 | [类型注解](./python/05-typing/README.md) | 为什么 AI 应用代码离不开类型：注解语法、Optional、泛型、TypedDict、Literal，用 pyright 检查 | lessons/02, 05 | complete |
| P06 | [Pydantic v2](./python/06-pydantic/README.md) | 用模型定义数据、校验输入、序列化输出、导出 JSON Schema | lessons/02, 05 | complete |
| P07 | [asyncio 并发](./python/07-asyncio/README.md) | coroutine、Task、事件循环；`gather` 与 `TaskGroup`；超时、取消与资源清理；Semaphore 限并发 | lessons/02, 10；project/m0 | complete |
| P08 | [HTTP 与 FastAPI](./python/08-http-and-fastapi/README.md) | HTTP 请求响应、状态码、JSON、鉴权头；httpx 发请求；FastAPI 写最小 API、路径参数、依赖注入、SSE 流式 | lessons/02, 16；project/m1 | complete |
| P09 | [SQL、PostgreSQL 与 SQLAlchemy](./python/09-sql-and-sqlalchemy/README.md) | 建表、索引、JOIN、事务；SQLAlchemy 2.0 的 ORM 与 session；Alembic 迁移 | lessons/14, 16；project/m2 | complete |
| P10 | [pytest 与测试思维](./python/10-testing/README.md) | fixture、参数化、mock、断言异常；先写测试再写实现；怎样给不确定的模型输出写测试 | lessons/17；project 全部 | complete |
| P11 | [Git、命令行与 Docker Compose](./python/11-git-cli-and-docker/README.md) | 分支、提交、rebase、解决冲突；常用 shell 命令；用 Docker Compose 一条命令起 PostgreSQL 和 Redis | project/m2 起 | complete |

## 学法

1. 按顺序学。P00～P06 是语言本身，P07～P11 是后端工程，两段之间没有捷径。
2. 每个模块先跑 `code/`，再读正文，再做 `exercises.md`。
3. 「它在 AI 应用里用在哪」这一节告诉你这个知识点将来在哪会用到。看不懂没关系，知道有这回事就行。
4. 学到 P07 asyncio 时同步做 [project/m0](../project/m0-concurrency/README.md)，这是主项目的第一个里程碑。

## 不在这里讲的

- 数据结构与算法：AI 应用开发用得少，需要时看 [Hello 算法](https://www.hello-algo.com/)。
- 前端：主线第 20 课会讲 AI 产品的交互设计，但不教写页面。
- 机器学习数学：主线第 01 课和 [tracks/llm-internals](../tracks/llm-internals/README.md) 只讲应用工程师需要的那一层。
