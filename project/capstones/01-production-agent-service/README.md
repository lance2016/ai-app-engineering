---
status: outline
kind: capstone
depends_on: project/m5
---

# Capstone 1 Production Agent Service

> M1～M5 做完的服务离上线还差一层：一键部署、每次改动有门禁、每次请求有 trace、故障演练过一遍、出事有人知道怎么办。这个 Capstone 补的就是这一层。

## 需求

- 面向一个租户的任务 Agent 服务，能力用 M3 的工具集
- 一条命令起全部依赖并部署，健康与就绪探针齐全
- 每次合并前跑 golden set 回归，跌破基线阻断
- 每租户限流与预算，供应商挂了有 fallback

## 约束

<!-- outline：数据边界、预算、延迟、团队规模。待写。 -->

## 验收清单

- [ ] `docker compose up` 一键起服务与依赖，探针通过
- [ ] CI 四个门禁加评测门禁全绿
- [ ] Phoenix 里一次请求能看到完整链路
- [ ] `chaos.py` 五种故障各有一份演练记录，系统行为与预期一致
- [ ] runbook 覆盖至少五个告警的处置步骤

## 评分量表

<!-- outline：正确性、持久性、评测、可观测、安全、成本、文档，每项三档。待写。 -->

## 交付物

代码与测试、评测报告、trace 截图、故障演练记录、runbook、部署文档。

## 常见失败

<!-- outline：待写。 -->

---

[← Capstone 总览](../README.md)
