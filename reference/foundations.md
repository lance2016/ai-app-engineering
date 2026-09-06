---
status: complete
part: 开始这里
---

# 进这门课之前，该有哪些底子

> **这门课不教 Python，也不教后端。** 但它默认你有一些东西。这一页把这些默认值列出来，免得读到一半卡在和 AI 无关的地方。
>
> 分三档：**必备**指不会就读不下去；**用到再学**指遇到那一课再补，半小时够；**可选**指补了有好处、不补也不影响主线。
>
> 每项都写了「这门课哪里用到它」——这一页不是通用学习清单，只列这门课真正会碰到的部分。链接都是官方文档入口。

## Python

| 项 | 档 | 这门课哪里用到 |
|---|---|---|
| 类型注解（`typing`） | 必备 | 几乎每段示意代码。工具契约、状态定义、适配器接口全靠它表达 |
| `dataclass` | 必备 | 工具参数、事件、候选模型、检索结果，全是 dataclass |
| 异常与自定义异常 | 必备 | 失败分类是第 06 课的核心，「哪些错该重试」建立在异常层次上 |
| `async` / `await` | 必备 | 第 06 课起全部是异步的。模型调用、工具并行、流式都绕不开 |
| 上下文管理器（`with`） | 必备 | 第 18 课的 tracer 就是一个上下文管理器 |
| 生成器与异步生成器 | 用到再学 | 第 02 课的流式输出，一个 `async for` 就是全部 |
| Pydantic v2 | 用到再学 | 第 05 课工具参数校验。schema 和校验共用一个定义，是「契约」这个说法的由来 |
| `asyncio` 的取消与超时 | 用到再学 | 第 06 课的步数预算、第 19 课的超时控制 |
| `contextvars` | 可选 | 第 18 课让子 span 找到父 span 用的就是它，有个跨线程池不传播的坑 |

- [Python 官方教程](https://docs.python.org/3/tutorial/)（访问日期 2026-09-06）
- [`typing` 模块文档](https://docs.python.org/3/library/typing.html)（访问日期 2026-09-06）
- [`asyncio` 文档](https://docs.python.org/3/library/asyncio.html)（访问日期 2026-09-06）：只需要看 coroutine、task、`gather`、`wait_for` 四节
- [Pydantic 文档](https://docs.pydantic.dev/latest/)（访问日期 2026-09-06）

## 后端

| 项 | 档 | 这门课哪里用到 |
|---|---|---|
| HTTP 与状态码 | 必备 | 第 02 课重试策略建立在「哪些状态码该重试」上 |
| REST 与 JSON | 必备 | 模型 API 本身就是一组 REST 接口 |
| SQL 基础（建表、查询、索引） | 必备 | 第 04 课 pgvector、第 07 课事件线程、第 15 课删除演练 |
| 环境变量与配置分离 | 必备 | 第 00 课起，API key 一律走环境变量 |
| SSE（Server-Sent Events） | 用到再学 | 第 02 课流式返回、第 22 课流式界面 |
| 事务与隔离级别 | 用到再学 | 第 07 课 checkpoint、第 15 课删除的一致性 |
| Redis | 用到再学 | 第 07 课的运行时状态、第 05 课的幂等键存储 |
| Docker 与 compose | 用到再学 | 第 19 课容器化与灰度。想跑参考实现也需要 |
| pytest | 用到再学 | 第 17 课的断言和门禁就是普通测试 |
| WebSocket | 可选 | 双向实时场景。这门课的例子用 SSE 就够 |
| 消息队列 | 可选 | 第 19 课长任务那一节会提到，不展开 |

- [MDN · HTTP 指南](https://developer.mozilla.org/en-US/docs/Web/HTTP)（访问日期 2026-09-06）
- [MDN · Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)（访问日期 2026-09-06）
- [PostgreSQL 官方文档](https://www.postgresql.org/docs/current/)（访问日期 2026-09-06）：索引和事务两章
- [pgvector](https://github.com/pgvector/pgvector)（访问日期 2026-09-06）：第 04 课直接用它建表
- [FastAPI 文档](https://fastapi.tiangolo.com/)（访问日期 2026-09-06）
- [pytest 文档](https://docs.pytest.org/)（访问日期 2026-09-06）

## 算法与计算机基础

这门课不考算法。但下面几项如果没有直觉，某些判断会做不出来。

| 项 | 档 | 这门课哪里用到 |
|---|---|---|
| 复杂度直觉（O(n) 还是 O(n log n)） | 必备 | 第 04 课「十万条以内暴力扫描就够，什么时候该建索引」 |
| 哈希表 | 必备 | 幂等键、result store、去重，到处都是 |
| 向量、点积、余弦相似度 | 必备 | 第 04 课的全部基础。前置 [F02](../prerequisites/llm-foundations/02-embeddings/README.md) 讲了够用的部分 |
| top-k 与堆 | 用到再学 | 检索返回 top-k，重排是在这个 k 上再排一次 |
| 队列与并发模型 | 用到再学 | 第 07 课的 double texting 三种策略，本质是队列策略 |
| ANN 索引原理（HNSW） | 可选 | 第 04 课会用它，但调参靠实测，不靠推导 |
| 图与 BFS/DFS | 可选 | 第 09 课 workflow 是有向图，理解「图」这个说法有帮助 |

- [前置 · LLM 原理](../prerequisites/README.md)：模型侧的基础在这里，八篇，不需要线性代数
- [pgvector 的索引说明](https://github.com/pgvector/pgvector#indexing)（访问日期 2026-09-06）：HNSW 参数的含义

## 不需要的东西

省下时间，这门课用不到：

- **训练和微调模型的能力。** 第 21 课讲什么时候该微调、怎么算显存、成本临界点在哪，但不教你训一个模型。
- **深度学习框架。** 全课不出现 PyTorch。前置里的小实验是纯标准库的。
- **线性代数和概率论的推导。** 需要的部分（向量、余弦、采样）在前置里用具体数字讲完了。
- **前端框架。** 第 22 课讲交互设计和状态机，不写 React。
- **Kubernetes。** 第 19 课到容器和灰度为止。

## 底子够了，从哪开始

| 你的情况 | 建议 |
|---|---|
| 上面必备项基本都有，没做过 AI 应用 | [第 00 课](../lessons/00-setup/README.md)顺着读 |
| 做过 AI 应用，想查漏补缺 | 先做[自测](./diagnostic.md)，按结果挑 Part |
| 模型原理不熟（token、attention、KV cache） | [前置 · LLM 原理](../prerequisites/README.md)，八篇 |
| 必备项缺得比较多 | 先补 Python 的类型注解、dataclass、async 三项和 SQL，其余边读边补 |

课程结构和各 Part 的出师标准见[课程总览](../lessons/README.md)。
