---
status: complete
part: 背景知识
---

# 数据演进与异步工作流：事实、派生和长任务

> 迁移、删除和后台任务都跨越多个时间点；把事实、派生状态和任务进度分开，系统才有恢复路径。

## 数据一致性与演进

系统里常见三种数据：不可随意改写的事实（事件、账单、用户提交）、可以重新计算的派生数据（状态快照、检索索引、成本汇总）和可以丢失后重建的缓存。它们的事务边界、保留时间和删除方式不同。

数据库结构和 API 契约也会演进。成熟的迁移通常分成“先增加兼容结构 → 双写或回填 → 切读路径 → 删除旧结构”几个阶段；一次提交里直接改名或删列，容易让旧进程、后台任务和回滚版本互相不认识。文档、向量和记忆的删除还要沿着派生链验证，不能只删原表的一行。

参考实现的 M2 记录事件、消息和任务，M4/M5 处理文档版本、引用、记忆、评测数据和迁移；先看 [`storage/models.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/storage/models.py)、[`storage/migrations/versions/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/src/aiapp/storage/migrations/versions) 和 [`knowledge/citations.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/knowledge/citations.py)。事务和隔离级别可继续查 [PostgreSQL Transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html)，访问日期为 2026-09-10。


## 异步任务与工作流：请求结束后，谁还在工作

短 HTTP 请求适合在一个响应内完成；文档批量导入、长任务、评测和定时清理应交给可恢复的 worker。进程内的 `asyncio.Task` 随进程消失，不能当作持久任务记录。持久队列还要处理投递次数、租约、心跳、重试、死信、取消和背压。

许多持久队列按“至少一次投递”来设计，所以 worker 必须幂等；任务状态要能回答“已领取、执行到哪、最后一次心跳、失败原因、还能不能重试”。参考项目当前没有持久化消息队列：M3 选择同一线程第二次请求直接拒绝，Capstone 3 才把长任务的恢复和 worker 作为设计题。这样写是为了把边界说清，不把同步代码包装成已经完成的异步平台。

---

[工程能力进阶概览](./README.md) · [工程能力基础](../engineering-foundations/README.md) · [背景知识总览](../README.md)
