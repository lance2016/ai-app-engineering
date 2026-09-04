---
status: complete
kind: impl
depends_on: 前置 P07；lessons/00, 02
---

# M0 并发实验

> 主项目的第一个里程碑不写服务，先用五个对照实验把 asyncio 的直觉建立起来：并发能省多少、限流怎么做、超时和取消时资源怎么清理、一个同步调用能把整个服务拖慢多少。后面每个里程碑的模型调用、工具并行和流式输出都建立在这些直觉上。

## 这一步加什么

五个独立脚本，每个只演示一个机制，全部只用标准库：

| 文件 | 机制 | 看什么 |
|---|---|---|
| [`code/01_sequential_vs_gather.py`](./code/01_sequential_vs_gather.py) | 串行 vs `gather` | 五次 0.2s 的"模型调用"，串行 1.0s，并发 0.2s |
| [`code/02_semaphore_limit.py`](./code/02_semaphore_limit.py) | `Semaphore` 限并发 | 20 个调用限 4 个在飞，耗时约 5 轮，峰值在飞数不超过 4 |
| [`code/03_timeout.py`](./code/03_timeout.py) | `wait_for` 超时 | 慢调用被切断，`finally` 里的资源释放仍然执行 |
| [`code/04_cancellation.py`](./code/04_cancellation.py) | `TaskGroup` 级联取消与 `shield` | 一个任务失败，兄弟任务被取消，被 shield 的审计写入照常完成 |
| [`code/05_blocking_call.py`](./code/05_blocking_call.py) | 同步调用阻塞事件循环 | `INJECT_BLOCKING=1` 时一个 `time.sleep` 让整批变慢一倍；`to_thread` 修复 |

这五个机制在后面的落点：

- 并发与限流 → M3 并行工具调用、M5 对模型供应商的速率限制
- 超时与清理 → M3 `ToolRunner` 的每次执行、M5 的 Fallback
- 级联取消与 shield → M2 事件写入不能被请求取消打断、第 07 课的 double texting interrupt
- 阻塞调用 → M1 起任何同步 SDK 都必须走 `to_thread`

## 运行步骤

```bash
uv sync
uv run python project/m0-concurrency/code/01_sequential_vs_gather.py
uv run python project/m0-concurrency/code/02_semaphore_limit.py
uv run python project/m0-concurrency/code/03_timeout.py
uv run python project/m0-concurrency/code/04_cancellation.py
uv run python project/m0-concurrency/code/05_blocking_call.py
INJECT_BLOCKING=1 uv run python project/m0-concurrency/code/05_blocking_call.py
```

每个脚本打印耗时，机器不同数字略有差异，比例关系不变。

## 验收证据

- [ ] 五个脚本都能跑，且输出的耗时比例和上表一致
- [ ] 能用自己的话解释 `01` 里并发为什么省时间（等待网络时事件循环去干别的），以及它对 CPU 密集任务为什么无效
- [ ] 把 `02` 的 `limit` 改成 1，预测耗时再运行验证
- [ ] 把 `03` 里 `finally` 删掉，说出生产环境会发生什么（连接泄漏）
- [ ] 把 `04` 的 `shield` 去掉，观察审计写入是否还完成，解释为什么事件写入需要 shield
- [ ] 失败注入：`05` 带 `INJECT_BLOCKING=1` 跑一次，解释为什么整批变慢的不只是那一个调用

## 依赖的课程

前置 P07；lessons/00, 02

---

[← 项目总览](../README.md)
