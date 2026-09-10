---
status: complete
part: 背景知识
---

# 可靠性与测试：验证每一层的承诺

> 超时、重试和并发会让同一个操作出现多次；测试要覆盖这些边界，而不是只检查一个 200。

## 可靠性：同一个请求可能执行多次

网络超时只说明调用方没有等到结果，不能证明服务端没有执行。把所有失败都重试，可能把一次扣款、发信或工具副作用执行两遍。参考实现把重试、幂等、限流和熔断分别处理：

| 概念 | 最小概念 | 参考实现 |
|---|---|---|
| 重试和退避 | 只重试暂时性失败；每次有超时，总体有次数上限，等待时间逐步增加并加入抖动 | [`ops/resilience.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/resilience.py) |
| 幂等 | 同一个请求或工具调用重放时，返回已有结果，不再次产生副作用 | [`api/routes/threads.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/routes/threads.py)、[`runtime/runner.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/runner.py) |
| 限流 | 在请求进入模型和数据库前控制速率；拒绝时返回 429 和 `Retry-After`，让客户端决定何时再试 | [`ops/ratelimit.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/ratelimit.py) |
| 熔断和 fallback | 下游连续失败时暂时停止调用；恢复或切备用路径，避免每个请求都撞向故障服务 | [`ops/resilience.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/resilience.py) |
| 队列和后台任务 | 把耗时工作从短 HTTP 请求中移出，由 worker 稍后处理；队列通常至少一次投递，所以任务也要幂等 | 当前参考项目没有持久化队列；长任务只在 [Capstone 3](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/capstones/03-durable-agent) 的设计里讨论 |

先理解“超时后可能已经成功”这一个事实，再看[asyncio 队列](https://docs.python.org/3/library/asyncio-queue.html)和第 21 课。上面资料访问日期均为 2026-09-10。短请求适合直接返回，文档导入、批量评测和长任务才需要队列；不要为了看起来像生产系统而额外加队列。


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

---

[工程能力概览](./README.md) · [背景知识总览](../README.md)
