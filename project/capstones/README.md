---
status: outline
kind: capstone
depends_on: project/m1–m5；Framework Lab
---

# Capstone 实战

> 章节练习证明你懂一个机制，Capstone 证明你能交付一个系统。四个题目，每个都有明确的前置、可执行的验收和一张评分量表。做完任何一个，你就有了一个能放进简历、能在面试里讲一小时的项目。

## 四个题目

| # | Capstone | 一句话 | 前置 | 状态 |
|---|---|---|---|---|
| 1 | [Production Agent Service](./01-production-agent-service/README.md) | 把 M1～M5 交付成一个可上线的服务：一键部署、CI 门禁、评测报告、trace、故障演练、runbook | M5 | outline |
| 2 | [RAG + Memory Agent](./02-rag-memory-agent/README.md) | 自选语料，带引用与版本删除、可删的记忆、50 条以上评测集和失败分类 | M4, 17 | outline |
| 3 | [Long-running Durable Agent](./03-durable-agent/README.md) | 一个跨小时任务，kill -9 后从断点续上，副作用不重复；普通 Python 和一个框架各做一遍 | M3, Framework Lab | outline |
| 4 | [Multi-tenant AI Platform](./04-multi-tenant-platform/README.md) | M6 的 RFC 加一个实现切片：租户隔离测试、配额、按租户成本账、Skill 与 MCP 白名单 | 全部 | outline |

## 每个 Capstone 的固定结构

1. **需求**：用户是谁、要做成什么、明确不做什么
2. **约束**：数据边界、预算、延迟、团队规模
3. **验收清单**：能自动化的放 `tests/capstones/<name>/`，不能自动化的写清评审方法
4. **评分量表**：正确性、持久性、评测、可观测、安全、成本、文档七个维度，每个维度三档
5. **交付物**：代码、测试、报告、截图、文档各要什么
6. **常见失败**：前人怎么栽的

## 怎么做

- 一个人做，或两三个人分模块。做之前先写一页设计，用第 23 课的 ADR 格式。
- 先过验收清单里能自动化的部分，再补文档。CI 绿了再谈评分。
- 找一个人评审，把评审问题和修订附在交付物末尾。这一条不能省，M6 的验收里也有它。

---

[← 项目总览](../README.md)
