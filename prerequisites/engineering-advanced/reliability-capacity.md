---
status: complete
part: 背景知识
---

# 可靠性与容量：把“快”和“稳定”写成可测的承诺

> 平均数会藏住尾部请求；把 SLO、容量和成本放在同一条请求链上，才知道过载时该保护谁。

## SLO、容量与性能成本

平均延迟掩盖不了尾部请求。先写服务水平指标（SLI），再定服务水平目标（SLO），最后用错误预算决定是否继续发布。模型应用至少要分别看首 token 延迟、完整响应延迟、成功率、工具成功率、token 用量和单位请求成本；把它们揉成一个总分，定位不了问题。

容量估算也要从请求链开始：峰值到达率、每步平均耗时、同时运行的模型和工具数量、数据库连接池、供应商配额，任何一项都可能成为瓶颈。基于 Little's Law 的并发估算只是起点，最终还要用带真实输入长度和失败比例的压测校准。

参考实现把限流、模型超时、fallback、成本预算、健康检查和故障注入放在 M5；M6 再把容量假设、SLO 和迁移条件写进 RFC。可以从 [Google SRE 的 SLO 章节](https://sre.google/sre-book/service-level-objectives/)和[容量规划资料](https://sre.google/resources/)开始，资料访问日期均为 2026-09-10。


## 性能与成本：优化整条链，而不是只盯模型

模型调用常常是最显眼的一项，但端到端延迟还包括排队、连接建立、检索、工具、数据库写入和首块之前的等待。先区分首 token 延迟和完整响应延迟，再分别看输入 token、输出 token、缓存命中、并发和失败重试；否则一次“降延迟”可能只是少记了一段 trace，或者把工作推给后台。

成本优化也要保留质量和可回滚条件：短问题是否能路由到小模型，检索结果是否值得放进上下文，工具结果能否摘要，fallback 是否在预算内。参考实现的 [`ops/cost.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/cost.py)、[`runtime/context.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/context.py) 和 [`ops/resilience.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/resilience.py) 分别对应成本、上下文和失败路径。

---

[工程能力进阶概览](./README.md) · [工程能力基础](../engineering-foundations/README.md) · [背景知识总览](../README.md)
