---
status: complete
part: 背景知识
---

# 评测与观测：把模型变化接进工程反馈

> 线上指标只能告诉你哪里变差，评测切片和 trace 才能帮助你定位是哪一层改变了结果。

## 评测切片、trace 与反馈

模型应用的回归不只是一条“答案对不对”。评测集要按意图、语言、难度、权限和风险切片；trace 要保存模型版本、提示词版本、检索来源、工具参数、停止原因、token 和耗时。线上指标发现退化后，再靠 trace 找到是检索、上下文、模型、工具还是基础设施改变了。

跨服务时，request id 只能靠约定传递；trace context 让调用方的 trace/span id 沿 HTTP 或消息边界继续传播，日志和指标才有机会连回同一次请求。OpenTelemetry 的[上下文传播说明](https://opentelemetry.io/docs/concepts/context-propagation/)和[观测信号说明](https://opentelemetry.io/docs/concepts/signals/)可作为深入入口，访问日期为 2026-09-10。

参考实现的 M5 把 golden set、评测门禁、结构化日志和 trace 放在同一条 CI 路径上；对应入口是 [`eval/suites.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/eval/suites.py)、[`eval/gate.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/eval/gate.py) 和 [`ops/telemetry.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/telemetry.py)。

---

[工程能力进阶概览](./README.md) · [工程能力基础](../engineering-foundations/README.md) · [背景知识总览](../README.md)
