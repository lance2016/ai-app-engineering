---
status: complete
part: 背景知识
---

# Python 运行时：数据、错误和等待

> 类型、异常和异步控制流会直接改变 AI 应用的行为；这一页把它们放到参考实现的运行时里看。

## 类型、错误与等待的基础

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

---

[工程能力概览](./README.md) · [背景知识总览](../README.md)
