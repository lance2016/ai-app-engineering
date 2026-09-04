---
status: complete
part: 前置 · Python
estimated_time: 约 2 小时
---

# P07 asyncio 并发

> 一个 Python 程序默认一次只做一件事。调模型、查数据库、请求外部接口，大部分时间都在等对方回话。asyncio 让程序在等的时候去做别的事，等到了再回来。这一模块用五个对照实验把这件事讲清楚。

## 学习目标

- 能解释 coroutine、Task、事件循环三者的关系，说清为什么 `time.sleep` 会让整个程序停下而 `asyncio.sleep` 不会
- 能用 `gather` 和 `TaskGroup` 并发运行多个任务，并说出两者在有任务失败时的区别
- 能给一段等待加超时、处理取消、在 `finally` 里释放资源，并用 `Semaphore` 限制同时进行的任务数

## 前置

- [P03 模块、异常与日志](../03-modules-errors-and-logging/README.md)：`try / except / finally` 要熟
- [P04 类、dataclass 与 Protocol](../04-oop-and-dataclasses/README.md)

## 核心概念

### coroutine：一段"可以暂停"的函数

```python
import asyncio

async def greet(name: str) -> str:
    await asyncio.sleep(0.1)     # 在这里暂停，让别人先跑
    return f"hello, {name}"

thing = greet("Ada")             # 注意：什么都没发生，只得到一个 coroutine 对象
print(type(thing).__name__)      # coroutine
```

`async def` 定义的函数叫 coroutine 函数。直接调用它**不会执行函数体**，只会返回一个 coroutine 对象。真正让它跑起来的是 `await` 或者 `asyncio.run()`。

`await` 的意思是"在这里等结果，等的期间把控制权交出去"。只能在 `async def` 里面写 `await`。

### 事件循环：那个"交出去"的接收方

```python
async def main() -> None:
    result = await greet("Ada")
    print(result)

asyncio.run(main())              # 建一个事件循环，跑 main，跑完关掉
```

事件循环是一个调度器。所有 coroutine 在 `await` 时把控制权交给它，它看谁的等待结束了就让谁继续。整个程序只有一个线程在跑，快的原因不是"同时做"，而是"不傻等"。

### 为什么 `time.sleep` 是毒药

```python
async def blocking_job():
    time.sleep(0.3)              # 普通的等待，事件循环被卡住，谁都动不了

async def async_job():
    await asyncio.sleep(0.3)     # 告诉事件循环"0.3 秒后叫我"，然后让出去
```

三个 `blocking_job` 一起跑要 0.9 秒，三个 `async_job` 一起跑只要 0.3 秒。`02_blocking_vs_async.py` 能亲眼看到。同样的道理适用于所有同步的 I/O：`requests.get`、普通的 `open().read()`、同步数据库驱动。在 async 代码里调它们，整个服务都会停下来等。

### 并发跑多个：`gather` 和 `TaskGroup`

```python
await asyncio.gather(job(1), job(2), job(3))       # 三个一起跑，全部完成后返回结果列表

async with asyncio.TaskGroup() as tg:              # Python 3.11+
    tg.create_task(job(1))
    tg.create_task(job(2))
```

两者都能并发。区别在**有一个失败时**：`gather` 抛出那个异常，但其他任务继续跑；`TaskGroup` 会取消其他所有任务，然后把异常打包成 `ExceptionGroup` 抛出（用 `except*` 接）。`03_gather_vs_taskgroup.py` 把两种行为并排放在一起。

新代码优先用 `TaskGroup`。"一个失败全部停"通常是你想要的，而且不会留下没人管的任务。

### 超时与取消：`finally` 是唯一可靠的清理位置

```python
async def fetch():
    print("connection opened")
    try:
        await asyncio.sleep(1.0)
    finally:
        print("connection closed")   # 正常、报错、被取消，三种情况都会执行

async with asyncio.timeout(0.2):     # 0.2 秒没完成就取消里面的 await，抛 TimeoutError
    await fetch()
```

取消是通过在 `await` 处抛出 `CancelledError` 实现的。你不需要到处检查"是否被取消"，只要把释放资源的代码放进 `finally`。`04_timeout_and_cancel.py` 展示了超时触发的取消和手动 `task.cancel()` 走的是同一条路。

### `Semaphore`：一次最多几个

```python
sem = asyncio.Semaphore(3)

async def call_api(i):
    async with sem:              # 同时最多 3 个 coroutine 在这个块里
        await asyncio.sleep(0.1)
```

无限并发会把下游打垮，比如对模型 API 一口气发 500 个请求会直接被限流。`Semaphore(3)` 像三张通行证，拿到才能进，出来时还回去。`05_semaphore.py` 里 8 个任务：串行 0.8 秒，无限并发 0.1 秒，限 3 个 0.3 秒。

## 动手

| 文件 | 一个知识点 |
|---|---|
| [`code/01_coroutine_and_await.py`](./code/01_coroutine_and_await.py) | 调用 coroutine 函数不会执行，`await` 才会 |
| [`code/02_blocking_vs_async.py`](./code/02_blocking_vs_async.py) | `time.sleep` 对比 `asyncio.sleep`，计时 |
| [`code/03_gather_vs_taskgroup.py`](./code/03_gather_vs_taskgroup.py) | 有任务失败时两者的不同 |
| [`code/04_timeout_and_cancel.py`](./code/04_timeout_and_cancel.py) | 超时、取消、`finally` 清理 |
| [`code/05_semaphore.py`](./code/05_semaphore.py) | 串行、无限并发、限并发三种耗时 |

这五个实验和主项目 [M0](../../../project/m0-concurrency/README.md) 是同一组口径。这里讲原理，M0 要求你自己从零写一遍并记录结果。

## 常见错误

**忘了 `await`。**

```text
RuntimeWarning: coroutine 'f' was never awaited
```

看到这行警告，几乎一定是某处写了 `f()` 而不是 `await f()`。函数体一行都没执行。

**在普通函数里写 `await`。**

```text
SyntaxError: 'await' outside function
```

`await` 只能出现在 `async def` 里。把外层函数改成 `async def`，一直往上改到某个 `asyncio.run()` 为止。

**在已经运行的事件循环里再调 `asyncio.run()`。**

```text
RuntimeError: asyncio.run() cannot be called from a running event loop
```

`asyncio.run()` 是程序的入口，整个进程调一次。在 async 函数里想跑另一个 coroutine，直接 `await` 它，或者 `asyncio.create_task()`。Jupyter 里默认已经有一个事件循环在跑，所以在 notebook 里也不能用 `asyncio.run()`，直接 `await` 就行。

## 练习

见 [exercises.md](./exercises.md)。

## 它在 AI 应用里用在哪

主线落点：[02 模型调用、结构化输出与流式](../../../lessons/02-model-api-structured-output-streaming/README.md)、[10 多智能体、Handoff 与 Racing](../../../lessons/10-multi-agent-handoff/README.md)、主项目 [M0](../../../project/m0-concurrency/README.md)。

具体场景：一个 Agent 一轮里要同时查天气、查日程、查路况三个工具。串行调用要等三次网络往返；用 `TaskGroup` 并发发出去，总时间只等最慢的那一个。其中一个工具超时了，`asyncio.timeout` 把它取消，其他两个结果照常返回，超时那个作为错误结果回给模型。整个服务同时服务几十个用户，靠的就是"等的时候去做别的"。第 10 课的双模型竞速，本质是两个 coroutine 谁先返回用谁，另一个取消，用的全是这一模块的东西。

## 延伸阅读

- [asyncio · Coroutines and Tasks（中文）](https://docs.python.org/zh-cn/3/library/asyncio-task.html)（访问日期 2026-09-04）：官方文档，重点看 `gather`、`TaskGroup`、`timeout`、`Task Cancellation` 四节。
- [asyncio · Coroutines and Tasks（英文）](https://docs.python.org/3/library/asyncio-task.html)（访问日期 2026-09-04）：中文翻译有滞后时看这个。

---

[← P06](../06-pydantic/README.md) · [B00 →](../../backend/00-http-and-fastapi/README.md)
