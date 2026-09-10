---
status: complete
part: 背景知识
---

# 工程进阶：把系统当成一项长期运行的服务

> 这页给已经做过几年后端、能读懂基础页的人。重点从“这个功能怎么写”移到“系统对用户承诺什么、失败时怎么恢复、改动怎么回滚、凭什么决定继续投入”。
>
> 进阶不是再列一遍框架。先看基础页，再按下面的路线读主线第 07、17–22、26 课和参考项目 M2–M6。每一节都给一个判断问题、参考实现落点和继续深入的资料。

## 先建立一张进阶地图

| 能力域 | 要回答的问题 | 主线与参考实现 |
|---|---|---|
| 分布式执行 | 进程重启、重复请求、乱序事件和下游超时后，状态怎样恢复？ | 07、18；[`runtime/loop.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/loop.py)、[`storage/postgres.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/storage/postgres.py) |
| 数据一致性 | 哪份数据是事实，哪份是缓存或派生结果？迁移和删除怎样不留脏数据？ | 16、17；[`storage/migrations/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/src/aiapp/storage/migrations)、[`knowledge/ingest.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/knowledge/ingest.py) |
| 可靠性与容量 | 延迟、成功率、成本和并发的目标是什么？过载时先保护谁？ | 19–21、26；[`ops/resilience.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/resilience.py)、[`ops/ratelimit.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/ratelimit.py) |
| 多租户与安全 | 谁能看到什么、调用什么、改变什么？边界在哪一层执行？ | 13、22、26；[`runtime/registry.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/registry.py)、[`security/outbound.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/security/outbound.py) |
| 评测与观测 | 模型、提示词或数据变了，怎样知道质量和成本哪里变了？ | 19、20；[`eval/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/src/aiapp/eval)、[`ops/telemetry.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/telemetry.py) |
| 架构决策 | 为什么现在选这个方案，什么证据出现时要换？ | 18、23、26；[`m6-platform-design/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m6-platform-design)、[`capstones/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/capstones) |

本页所有参考实现路径均按仓库 `main` 分支核对，访问日期为 2026-09-10；仓库会继续演进，读者以当前版本为准。

## 分布式执行：先接受“会重复、会丢回应、会重启”

网络调用和进程都可能在任意一步失败。请求已经让下游完成了工作，响应却在回程中丢掉；客户端于是重试，服务端再次收到同一个请求。系统设计要先假设这种情况会发生，再决定怎样识别重复、保存进度和补偿。

| 失败时刻 | 可能看到的状态 | 设计要点 |
|---|---|---|
| 写事件前进程退出 | 客户端看到超时，数据库没有新事件 | 重试可以重新执行，但要有总超时和幂等键 |
| 事件已经提交，响应丢失 | 客户端以为失败，数据库其实已经前进 | 重试返回已有事件或回放结果，不能再次产生副作用 |
| 两个 worker 同时写同一序号 | 一个成功，一个拿到冲突 | 用唯一约束或版本号拒绝旧写入，再从最新状态重算 |
| 工具调用成功，结果记录失败 | 外部世界已改变，线程里没有结果 | 工具调用要有稳定幂等键，并把“已执行但未记录”作为恢复分支 |

参考实现用事件序号和唯一约束做乐观并发控制，用 Redis 保存短期幂等声明；`ThreadStore` 的内存版和 PostgreSQL 版还要通过同一组契约测试。对应代码在 [`storage/base.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/storage/base.py)、[`storage/postgres.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/storage/postgres.py)、[`runtime/runner.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/runner.py)。

这里不追求“恰好执行一次”的口号。跨网络和外部系统时，通常只能把重复控制在业务可接受的范围，再用幂等、去重和补偿把结果收敛到正确状态。

## SLO 与容量：把“快”和“稳定”写成可测的承诺

平均延迟掩盖不了尾部请求。先写服务水平指标（SLI），再定服务水平目标（SLO），最后用错误预算决定是否继续发布。模型应用至少要分别看首 token 延迟、完整响应延迟、成功率、工具成功率、token 用量和单位请求成本；把它们揉成一个总分，定位不了问题。

容量估算也要从请求链开始：峰值到达率、每步平均耗时、同时运行的模型和工具数量、数据库连接池、供应商配额，任何一项都可能成为瓶颈。基于 Little's Law 的并发估算只是起点，最终还要用带真实输入长度和失败比例的压测校准。

参考实现把限流、模型超时、fallback、成本预算、健康检查和故障注入放在 M5；M6 再把容量假设、SLO 和迁移条件写进 RFC。可以从 [Google SRE 的 SLO 章节](https://sre.google/sre-book/service-level-objectives/)和[容量规划资料](https://sre.google/resources/)开始，资料访问日期均为 2026-09-10。

## 数据一致性与演进：事实、派生和删除要分开

系统里常见三种数据：不可随意改写的事实（事件、账单、用户提交）、可以重新计算的派生数据（状态快照、检索索引、成本汇总）和可以丢失后重建的缓存。它们的事务边界、保留时间和删除方式不同。

数据库结构和 API 契约也会演进。成熟的迁移通常分成“先增加兼容结构 → 双写或回填 → 切读路径 → 删除旧结构”几个阶段；一次提交里直接改名或删列，容易让旧进程、后台任务和回滚版本互相不认识。文档、向量和记忆的删除还要沿着派生链验证，不能只删原表的一行。

参考实现的 M2 记录事件、消息和任务，M4/M5 处理文档版本、引用、记忆、评测数据和迁移；先看 [`storage/models.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/storage/models.py)、[`storage/migrations/versions/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/src/aiapp/storage/migrations/versions) 和 [`knowledge/citations.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/knowledge/citations.py)。事务和隔离级别可继续查 [PostgreSQL Transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html)，访问日期为 2026-09-10。

## 异步任务与工作流：请求结束后，谁还在工作

短 HTTP 请求适合在一个响应内完成；文档批量导入、长任务、评测和定时清理应交给可恢复的 worker。进程内的 `asyncio.Task` 随进程消失，不能当作持久任务记录。持久队列还要处理投递次数、租约、心跳、重试、死信、取消和背压。

许多持久队列按“至少一次投递”来设计，所以 worker 必须幂等；任务状态要能回答“已领取、执行到哪、最后一次心跳、失败原因、还能不能重试”。参考项目当前没有持久化消息队列：M3 选择同一线程第二次请求直接拒绝，Capstone 3 才把长任务的恢复和 worker 作为设计题。这样写是为了把边界说清，不把同步代码包装成已经完成的异步平台。

## 多租户与安全架构：边界要穿过每一层

只在 API 入口检查租户还不够。租户身份要随请求进入工具注册表、上下文、数据库查询、事件、成本和 trace；否则某一层忘记过滤，就会出现跨租户读取。控制面（租户、配额、配置、权限）和数据面（消息、文档、工具结果）也应分开考虑。

高阶安全工作还包括：密钥轮换和审计、第三方 Skill/MCP 的来源验证、出站网络限制、敏感字段脱敏、供应商数据保留政策、删除请求的可证明完成，以及把模型输出当作不可信输入。可以用 [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)检查通用 Web 控制，再对照 [OWASP LLM Top 10](https://genai.owasp.org/llm-top-10/)检查模型特有风险，资料访问日期均为 2026-09-10。

参考实现把工具白名单、租户依赖、出站限制和删除路径拆在 [`runtime/registry.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/registry.py)、[`api/deps.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/deps.py)、[`security/outbound.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/security/outbound.py) 和知识库存储层。读代码时要追踪同一个 `tenant_id` 走过哪些边界，而不是只看登录函数。

## 评测与观测：把模型变化接进工程反馈

模型应用的回归不只是一条“答案对不对”。评测集要按意图、语言、难度、权限和风险切片；trace 要保存模型版本、提示词版本、检索来源、工具参数、停止原因、token 和耗时。线上指标发现退化后，再靠 trace 找到是检索、上下文、模型、工具还是基础设施改变了。

跨服务时，request id 只能靠约定传递；trace context 让调用方的 trace/span id 沿 HTTP 或消息边界继续传播，日志和指标才有机会连回同一次请求。OpenTelemetry 的[上下文传播说明](https://opentelemetry.io/docs/concepts/context-propagation/)和[观测信号说明](https://opentelemetry.io/docs/concepts/signals/)可作为深入入口，访问日期为 2026-09-10。

参考实现的 M5 把 golden set、评测门禁、结构化日志和 trace 放在同一条 CI 路径上；对应入口是 [`eval/suites.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/eval/suites.py)、[`eval/gate.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/eval/gate.py) 和 [`ops/telemetry.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/telemetry.py)。

## 性能与成本：优化整条链，而不是只盯模型

模型调用常常是最显眼的一项，但端到端延迟还包括排队、连接建立、检索、工具、数据库写入和首块之前的等待。先区分首 token 延迟和完整响应延迟，再分别看输入 token、输出 token、缓存命中、并发和失败重试；否则一次“降延迟”可能只是少记了一段 trace，或者把工作推给后台。

成本优化也要保留质量和可回滚条件：短问题是否能路由到小模型，检索结果是否值得放进上下文，工具结果能否摘要，fallback 是否在预算内。参考实现的 [`ops/cost.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/cost.py)、[`runtime/context.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/context.py) 和 [`ops/resilience.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/resilience.py) 分别对应成本、上下文和失败路径。

## 架构决策：写清楚为什么现在这样做

几年经验后，最容易缺的不是组件知识，而是决策记录。每个重要选择至少写下：问题和约束、候选方案、测量结果、迁移成本、失败时的回退路径、什么新证据会推翻它。ADR 不是会议纪要，它要能在半年后帮助另一个人判断是否还适用。

参考项目的 M6 用 RFC 记录多租户、容量、威胁模型、模型与推理选型、迁移和退出条件；第 26 课和 [M6 综合设计](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m6-platform-design)适合一起读。不要先选框架再给它找问题，先写约束和验收，再看框架能省掉哪部分工作。

## 给有工作经验读者的路线

| 顺序 | 读什么 | 读完要能回答 |
|---|---|---|
| 1 | M2 + 第 07、18 课 | 进程重启、重复写入和并发冲突时，哪份状态是事实？ |
| 2 | M3 + 第 05、06、09、12、13 课 | 模型建议、工具副作用和第三方能力之间，哪些边界由代码守住？ |
| 3 | M4 + 第 15–17 课 | 文档更新、删除和引用校验怎样沿派生链保持一致？ |
| 4 | M5 + 第 19–22 课 | 一次质量或成本退化，能否从评测切片和 trace 定位到具体层？ |
| 5 | M6 + 第 23、26 课 | 什么时候该换模型、拆服务或引入框架，退出条件是什么？ |

外部路线可以按“可靠性 → 数据 → 安全 → 观测”补：先读 [Google SRE Book](https://sre.google/sre-book/introduction/)，再看 PostgreSQL 的事务和并发控制、OpenTelemetry 的上下文传播、OWASP ASVS。上述资料访问日期均为 2026-09-10。

## 这页暂时不展开什么

共识算法、跨地域复制、Kubernetes 控制器、内核网络调优、GPU kernel、服务网格和完整身份平台都是真正的进阶主题，但当前课程的参考项目没有这些实现。遇到相关工作时，再按实际约束单独补；不要为了“像大厂架构”提前引入一套自己无法观测和回滚的基础设施。

---

[工程能力基础](./engineering-foundations.md) · [背景知识总览](./README.md) · [参考项目路线](../reference/project-playbook.md)
