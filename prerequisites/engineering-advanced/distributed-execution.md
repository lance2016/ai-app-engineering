---
status: complete
part: 背景知识
---

# 分布式执行：先接受“会重复、会丢回应、会重启”

> 网络调用和进程都可能在任意一步失败；先把恢复问题说清，再决定存什么状态。

## 故障时刻与恢复策略

网络调用和进程都可能在任意一步失败。请求已经让下游完成了工作，响应却在回程中丢掉；客户端于是重试，服务端再次收到同一个请求。系统设计要先假设这种情况会发生，再决定怎样识别重复、保存进度和补偿。

| 失败时刻 | 可能看到的状态 | 设计要点 |
|---|---|---|
| 写事件前进程退出 | 客户端看到超时，数据库没有新事件 | 重试可以重新执行，但要有总超时和幂等键 |
| 事件已经提交，响应丢失 | 客户端以为失败，数据库其实已经前进 | 重试返回已有事件或回放结果，不能再次产生副作用 |
| 两个 worker 同时写同一序号 | 一个成功，一个拿到冲突 | 用唯一约束或版本号拒绝旧写入，再从最新状态重算 |
| 工具调用成功，结果记录失败 | 外部世界已改变，线程里没有结果 | 工具调用要有稳定幂等键，并把“已执行但未记录”作为恢复分支 |

参考实现用事件序号和唯一约束做乐观并发控制，用 Redis 保存短期幂等声明；`ThreadStore` 的内存版和 PostgreSQL 版还要通过同一组契约测试。对应代码在 [`storage/base.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/storage/base.py)、[`storage/postgres.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/storage/postgres.py)、[`runtime/runner.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/runner.py)。

这里不追求“恰好执行一次”的口号。跨网络和外部系统时，通常只能把重复控制在业务可接受的范围，再用幂等、去重和补偿把结果收敛到正确状态。

---

[工程能力进阶概览](./README.md) · [工程能力基础](../engineering-foundations/README.md) · [背景知识总览](../README.md)
