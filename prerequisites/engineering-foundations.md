---
status: complete
part: 背景知识
---

# 编程与后端：这门课会用到什么，缺了去哪学

> **这门课不教 Python，也不教后端。** 这一页是一张索引，不是教程：把课程默认你会的东西列出来，标清每项在哪一课用到、不会的话去哪学。免得读到一半卡在和 AI 无关的地方。
>
> 算法和数学那一块在[隔壁一页](./algorithm-foundations.md)。
>
> 分三档：**必备**指不会就读不下去；**用到再学**指遇到那一课再补，半小时够；**可选**指补了有好处、不补也不影响主线。
>
> 每项都写了「这门课哪里用到它」——这一页不是通用学习清单，只列这门课真正会碰到的部分。
> 每节末尾的「去哪学」只给入口和该读的范围，这一页本身不教这些东西。

## Python

| 项 | 档 | 这门课哪里用到 |
|---|---|---|
| 类型注解（`typing`） | 必备 | 几乎每段示意代码。工具契约、状态定义、适配器接口全靠它表达 |
| `dataclass` | 必备 | 工具参数、事件、候选模型、检索结果，全是 dataclass |
| 异常与自定义异常 | 必备 | 失败分类是第 06 课的核心，「哪些错该重试」建立在异常层次上 |
| `async` / `await` | 必备 | 第 06 课起全部是异步的。模型调用、工具并行、流式都绕不开 |
| 上下文管理器（`with`） | 必备 | 第 19 课的 tracer 就是一个上下文管理器 |
| 生成器与异步生成器 | 用到再学 | 第 02 课的流式输出，一个 `async for` 就是全部 |
| Pydantic v2 | 用到再学 | 第 05 课工具参数校验。schema 和校验共用一个定义，是「契约」这个说法的由来 |
| `asyncio` 的取消与超时 | 用到再学 | 第 06 课的步数预算、第 20 课的超时控制 |
| `contextvars` | 可选 | 第 19 课让子 span 找到父 span 用的就是它，有个跨线程池不传播的坑 |

**去哪学。** 这里只给入口和范围，别整本读。

| 想补的项 | 去哪学 | 读哪几节 |
|---|---|---|
| 类型注解 | [mypy 类型速查表](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html) | 整页，十分钟看完，比 `typing` 文档快 |
| 泛型、Protocol、TypedDict | [`typing` 模块文档](https://docs.python.org/3/library/typing.html) | 需要时查，不通读 |
| dataclass、异常、生成器 | [Python 官方教程](https://docs.python.org/3/tutorial/) | 异常、类、生成器三章 |
| `async` / `await` | [`asyncio` 文档](https://docs.python.org/3/library/asyncio.html) | coroutine、task、`gather`、`wait_for` 四节 |
| 取消与超时 | [`asyncio` 任务文档](https://docs.python.org/3/library/asyncio-task.html) | Timeouts 一节 |
| 上下文管理器 | [`contextlib` 文档](https://docs.python.org/3/library/contextlib.html) | `@contextmanager` 一个装饰器就够 |
| Pydantic v2 | [Pydantic 文档](https://docs.pydantic.dev/latest/) | Models 与 Validators 两章 |

访问日期均为 2026-09-06。想找一份按这门课的用法写成的 Python 代码来读，[参考实现](https://github.com/lance2016/ai-app-engineering-ref)就是：
类型注解、dataclass、async、pytest 在里面都以这门课需要的形态出现，比看教程的玩具例子直接。

## 后端

| 项 | 档 | 这门课哪里用到 |
|---|---|---|
| HTTP 与状态码 | 必备 | 第 02 课重试策略建立在「哪些状态码该重试」上 |
| REST 与 JSON | 必备 | 模型 API 本身就是一组 REST 接口 |
| SQL 基础（建表、查询、索引） | 必备 | 第 04 课 pgvector、第 07 课事件线程、第 16 课删除演练 |
| 环境变量与配置分离 | 必备 | 第 00 课起，API key 一律走环境变量 |
| SSE（Server-Sent Events） | 用到再学 | 第 02 课流式返回、第 23 课流式界面 |
| 事务与隔离级别 | 用到再学 | 第 07 课 checkpoint、第 16 课删除的一致性 |
| Redis | 用到再学 | 第 07 课的运行时状态、第 05 课的幂等键存储 |
| Docker 与 compose | 用到再学 | 第 20 课容器化与灰度。想跑参考实现也需要 |
| pytest | 用到再学 | 第 18 课的断言和门禁就是普通测试 |
| WebSocket | 可选 | 双向实时场景。这门课的例子用 SSE 就够 |
| 消息队列 | 可选 | 第 20 课长任务那一节会提到，不展开 |

**去哪学。**

| 想补的项 | 去哪学 | 读哪几节 |
|---|---|---|
| HTTP 与状态码 | [MDN · HTTP 指南](https://developer.mozilla.org/en-US/docs/Web/HTTP) | 方法与状态码两节 |
| SSE | [MDN · Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) | 整页，很短 |
| SQL、索引、事务 | [PostgreSQL 官方文档](https://www.postgresql.org/docs/current/) | 索引和事务两章 |
| pgvector | [pgvector](https://github.com/pgvector/pgvector) | README 的建表与查询两节，第 04 课直接用 |
| 配置与环境变量 | [The Twelve-Factor App](https://12factor.net/) | Config 一条 |
| FastAPI 的并发模型 | [FastAPI · Concurrency and async](https://fastapi.tiangolo.com/async/) | 整页；它解释了什么时候该写 `def` 而不是 `async def` |
| Redis 用法 | [Redis 开发文档](https://redis.io/docs/latest/develop/) | 数据类型与过期两节 |
| Docker 与 compose | [Docker 入门](https://docs.docker.com/get-started/) | 到 compose 为止，编排不用看 |
| pytest | [pytest 文档](https://docs.pytest.org/) | fixture 一章 |

访问日期均为 2026-09-06。

## 另外几页

算法与数学那部分在[算法与数学](./algorithm-foundations.md)：复杂度、哈希表、向量与余弦、top-k、ANN 索引。
模型原理在 [LLM 原理那八篇](./README.md)。这门课用不到什么、从哪开始，见[背景知识总览](./README.md)。

---

[背景知识总览](./README.md) · [算法与数学](./algorithm-foundations.md)
