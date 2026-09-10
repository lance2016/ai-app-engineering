---
status: complete
part: 背景知识
---

# 工程能力：读懂一个 AI 应用怎样运行

> 这组页面从“能读懂一个请求”开始，逐步走到“能定位一次线上失败”。它不替代完整的 Python、Web 或数据库教程；每页先给最低概念，再指向参考实现和官方资料。
>
> 推荐顺序：先看[零基础与开工](./getting-started.md)，再按需要读 Python、Web、数据、可靠性、观测和安全。已经做过后端的人可以直接看[工程能力进阶](../engineering-advanced/README.md)。

## 先建立一张图

一次请求通常会经过这些边界：客户端发 HTTP 请求，API 校验输入，运行时组装上下文并调用模型；模型返回文本或工具请求，运行时校验后才执行工具；状态和结果写入数据库，日志和 trace 记录这次请求经过了哪些边界。

| 能力页 | 解决的问题 | 主线与参考实现 |
|---|---|---|
| [零基础与开工](./getting-started.md) | 进程、端口、API、JSON、依赖和 Git 到底是什么 | 第 00 课；M0、M1 |
| [Python 运行时](./python-runtime.md) | 类型、异常、async、生成器和资源生命周期怎样影响运行时 | 第 05–07 课；`runtime/`、`api/` |
| [Web 与 HTTP](./web-http.md) | 请求、响应、REST、HTTPS、SSE、认证和跨域如何配合 | 第 02、05、18 课；`api/routes/` |
| [数据与存储](./data-storage.md) | 事实、索引、事务、迁移、缓存和连接池分别负责什么 | 第 04、07、15、17 课；`storage/`、`knowledge/` |
| [可靠性与测试](./reliability-testing.md) | 超时、重试、幂等、限流和测试怎样避免重复副作用 | 第 05、19、21 课；`ops/`、`tests/` |
| [观测、部署与工具](./observability-deployment.md) | 用日志、trace、容器和健康检查重现、定位和发布 | 第 18–21 课；`ops/`、`Dockerfile` |
| [安全与权限](./tooling-security.md) | 谁能读取、调用和改变什么，密钥与提示注入如何处理 | 第 12、22 课；`security/`、`runtime/registry.py` |

读代码时先问五个问题：输入从哪里来？谁校验它？谁改变外部世界？事实写到哪里？出了问题拿什么证据定位？这五个问题比记框架名更有用。想先看完整运行链，可从参考项目的[项目路线](../../reference/project-playbook.md)进入。

## 推荐学习路线

| 阶段 | 先掌握 | 推荐资料 |
|---|---|---|
| 0. 编程入门 | 变量、函数、条件、循环、异常、文件和模块 | [CS50P Python 入门课](https://cs50.harvard.edu/python/)、[Python Tutorial](https://docs.python.org/3/tutorial/) |
| 1. Python 与终端 | 类型、异常、async、路径、环境变量、Git | [Python Tutorial](https://docs.python.org/3/tutorial/)、[Pro Git](https://git-scm.com/book/en/v2)、[Shell Tools](https://missing.csail.mit.edu/2020/course-shell/) |
| 2. HTTP 服务 | 方法、状态码、JSON、schema、超时、SSE | [MDN HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview)、[FastAPI async](https://fastapi.tiangolo.com/async/)、[MDN SSE](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) |
| 3. 数据与并发 | SQL、索引、事务、迁移、Redis、取消 | [PostgreSQL Tutorial](https://www.postgresql.org/docs/current/tutorial.html)、[Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)、[Redis 开发文档](https://redis.io/docs/latest/develop/)、[asyncio](https://docs.python.org/3/library/asyncio.html) |
| 4. 测试与可靠性 | fixture、替身、契约测试、golden set、重试、幂等、CI | [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)、[pytest monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)、[GitHub Actions](https://docs.github.com/en/actions) |
| 5. 运行与安全 | 镜像、Compose、健康检查、日志、trace、最小权限 | [Docker Compose](https://docs.docker.com/compose/)、[OpenTelemetry primer](https://opentelemetry.io/docs/concepts/observability-primer/)、[OWASP LLM Top 10](https://genai.owasp.org/llm-top-10/) |

上表链接访问日期均为 2026-09-10。资料很多时不要从头通读：先看目录和示例，再拿参考实现中的一个请求或一个失败测试对照。

## 从哪里开始

| 你的情况 | 建议 |
|---|---|
| 没写过程序，也不了解后端 | 先读[零基础与开工](./getting-started.md)，掌握进程、端口、HTTP 和 Git 的最小画面 |
| Python 和后端基本熟悉，没做过 AI 应用 | 读第 00 课；遇到能力表里的“用到再学”再回来补 |
| 只缺 Python 基础 | 先看[Python 运行时](./python-runtime.md)，再补类型、异常、asyncio 和 pytest |
| 只缺服务和数据库基础 | 先看[Web 与 HTTP](./web-http.md)和[数据与存储](./data-storage.md)，再读第 02、05、07 课 |
| 想直接跑项目 | 按[参考项目路线](../../reference/project-playbook.md)从 M0 或 M1 开始；fake model 不需要 API key |
| 想补模型原理 | 回到[背景知识总览](../README.md)的 F00–F07，不必先读完工程能力 |

这组页面只讲概念和阅读路径。真要动手，参考实现在 [ai-app-engineering-ref](https://github.com/lance2016/ai-app-engineering-ref)；每页的“参考实现”链接会落到具体目录或文件。

---

[背景知识总览](../README.md) · [工程能力进阶](../engineering-advanced/README.md) · [算法与数学](../algorithm-foundations.md)
