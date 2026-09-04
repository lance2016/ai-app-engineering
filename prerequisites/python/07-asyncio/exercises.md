# P07 asyncio 并发｜练习

> 每题写清：任务、验收标准、提示。答案折叠。第一题照着做就能完成。

## 练习 1：把三个任务改成五个

在 `02_blocking_vs_async.py` 里，把 `gather(job(1), job(2), job(3))` 改成五个任务，再跑一次。

验收：`time.sleep` 那一组耗时约 1.5 秒，`asyncio.sleep` 那一组仍然约 0.3 秒。

<details><summary>答案</summary>

`await asyncio.gather(*(job(i) for i in range(1, 6)))`。async 版本的耗时只取决于最慢的那一个任务，和任务数量无关，这就是"不傻等"的直接体现。

</details>

## 练习 2：让 TaskGroup 里的失败不影响别人

`03_gather_vs_taskgroup.py` 里 `TaskGroup` 遇到一个失败会取消所有任务。有时你想要"每个任务各自失败各自处理，其他人继续"。在不换回 `gather` 的前提下做到这一点。

验收：`fails_fast` 抛出的异常被打印出来，`slow` 正常跑完，程序 exit 0。

<details><summary>答案</summary>

把异常处理放进任务内部，不让它逃出去：

```python
async def safe(coro):
    try:
        await coro
    except Exception as exc:
        print(f"task failed: {exc!r}")

async with asyncio.TaskGroup() as tg:
    tg.create_task(safe(fails_fast()))
    tg.create_task(safe(slow("taskgroup")))
```

原则：`TaskGroup` 只看到"逃出来"的异常。你想让哪些失败是致命的，就让哪些逃出来。

</details>

## 练习 3：超时之后拿到部分结果

写一个函数并发请求 5 个"接口"（用 `asyncio.sleep(random.uniform(0.1, 0.5))` 模拟），整体超时 0.3 秒。超时后返回已经完成的结果，没完成的记为 `None`。

验收：多跑几次，每次返回的列表长度都是 5，其中一部分是结果一部分是 `None`，程序不抛异常。

<details><summary>提示与答案</summary>

用 `asyncio.wait(tasks, timeout=0.3)` 而不是 `gather`：它返回 `(done, pending)` 两个集合，不会因为超时抛异常。然后对 `pending` 里的每个 task 调 `cancel()`。

```python
tasks = [asyncio.create_task(fetch(i)) for i in range(5)]
done, pending = await asyncio.wait(tasks, timeout=0.3)
for t in pending:
    t.cancel()
results = [t.result() if t in done else None for t in tasks]
```

这个模式在"多个工具并行调用，慢的不等了"的场景里很常用。

</details>

## 练习 4：Semaphore 该设多少

不写代码。`05_semaphore.py` 里 `Semaphore(3)` 的 3 是随手写的。假设你在调一个模型 API，它的限制是每分钟 60 次请求，每次请求平均 2 秒。`Semaphore` 应该设多少？设大了和设小了各会发生什么？

<details><summary>参考答案</summary>

每次 2 秒，一分钟一个"通行证"能用 30 次。60 次/分钟的上限意味着大约 2 个通行证就够了，设 2～3 比较合适。

设大了：请求在对方那边被限流，返回 429 错误，你还要处理重试，比在自己这边排队更慢。设小了：并发跑不满，用户等得更久。真实系统里这个数字需要观察限流错误率来调，不是算出来就不动了。

</details>

## 练习 5：找出这段代码为什么慢

```python
async def handle(user_id):
    data = requests.get(f"https://api.example.com/users/{user_id}").json()
    return data["name"]

await asyncio.gather(*(handle(i) for i in range(20)))
```

<details><summary>答案</summary>

`requests.get` 是同步调用，它在等网络的时候不会把控制权交给事件循环。20 个 `handle` 名义上并发，实际上一个接一个地把事件循环卡住，总耗时和串行一样。

修法：换成 `httpx.AsyncClient`，`data = (await client.get(url)).json()`。规律是：在 `async def` 里，任何会等待的操作都必须是 `await` 得了的版本，否则并发就是假的。P08 会用到 httpx。

</details>
