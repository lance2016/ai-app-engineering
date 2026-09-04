---
status: outline
kind: capstone
depends_on: project/m3；Framework Lab
---

# Capstone 3 Long-running Durable Agent

> 对话 Agent 几秒就结束，这个任务要跑几小时：多步、要等人批准、中途进程会被杀。做完你会真正理解 checkpoint、幂等和 durable execution 是三件事还是一件事。

## 需求

- 一个跨小时的多步任务，例如批量数据处理、多源调研报告、多系统运维变更
- 关键步骤暂停等人批准，批准可能几小时后才到
- 任意时刻 `kill -9`，重启后从断点续上，有副作用的步骤不重复
- 进度以事件流推送，预算与超时可配置
- **用普通 Python（M2/M3 的存储与 runtime）和 Framework Lab 里选定的一个框架各实现一遍**

## 约束

<!-- outline：数据边界、预算、延迟、团队规模。待写。 -->

## 验收清单

- [ ] `tests/capstones/durable/` 的 kill 与恢复 harness 连续跑 20 次，副作用计数始终正确
- [ ] 暂停超过进程生命周期后批准，任务能继续
- [ ] 两个实现过同一套一致性测试
- [ ] 一份对比文档：两个实现在 Checkpoint、Durable Execution、Debuggability 三个维度的差别，附代码行证据

## 评分量表

<!-- outline：正确性、持久性、评测、可观测、安全、成本、文档，每项三档。待写。 -->

## 交付物

两份实现与测试、harness、对比文档、trace 截图。

## 常见失败

<!-- outline：待写。 -->

---

[← Capstone 总览](../README.md)
