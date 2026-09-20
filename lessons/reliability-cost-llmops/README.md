---
status: complete
structure: narrative
part: Part 4 生产工程
topic: production-governance
tier: core
estimated_time: 约 40 分钟
---

# 21 可靠性、成本、部署与 LLMOps

> 生产可靠性不是给 Agent 套一个重试装饰，而是让失败分类、预算、降级、发布和回滚都能被运行时执行。

<details class="case" markdown="1">
<summary>例子：供应商抖动触发重试，延迟、成本和并发一起失控</summary>

模型请求超时后全部重试，重试又带着完整历史。下游恢复时，积压请求同时打满配额；用户等待更久，账单也增加。

!!! note "构造的例子"
    故障链用于说明控制面之间的关系；具体阈值要由流量和供应商限制测出。

</details>

## 先分类失败

| 失败 | 默认动作 | 不该做什么 |
|---|---|---|
| 参数 / 权限 | 立即返回或回喂修正 | 重试同一请求 |
| 临时网络 / 限流 | 有预算地退避重试 | 无上限重试 |
| 供应商不可用 | fallback 或降级 | 把所有流量打到同一故障点 |
| 外部副作用未知 | 查询 / 对账 / 人工 | 直接再做一次 |
| 超预算 | 停止并说明原因 | 为完成回答继续花钱 |

重试次数不是可靠性指标。重试必须带超时、退避、幂等键和总预算。

## 四个运行时控制

1. **Timeout**：每一跳和整次运行都有截止时间。
2. **Retry**：只对可恢复错误使用，指数退避并设上限。
3. **Circuit breaker**：连续失败时暂时停止调用，给下游恢复机会。
4. **Budget**：每轮结算 token、金额、时间和步数，耗尽就结束或降级。

成本可以按请求计算：

```text
请求成本 = Σ(输入 token × 价格表 + 输出 token × 价格表)
```

价格表要带日期，模型选择、上下文长度和循环步数是成本设计，不是月底才看的财务数据。

## 发布和回滚也是运行时的一部分

Prompt、模型、检索索引、工具 schema 和代码都可能改变行为。发布要有版本、灰度、回滚条件和对应评测集；只回滚代码但不回滚 Prompt 或索引，系统仍可能处于坏状态。

## 怎么测

用故障注入逐个验证：模型超时、限流、返回坏 JSON、工具失败、数据库不可用、预算耗尽和取消。记录：

- p95 延迟、错误率、重试率和 fallback 比例；
- 单请求成本和预算拒绝率；
- 熔断打开后是否真的减少下游流量；
- 灰度版本退步时能否自动停止并回滚。

## 参考实现与延伸

参考实现的限流、fallback、预算、成本和 chaos 场景在 [M5 Production](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m5-production)（核对日期 2026-09-10）。可靠性指标可对照 [Google SRE Workbook](https://sre.google/workbook/implementing-slos/)（访问日期 2026-09-10）。

---

[← 上一课 20](../observability/README.md) · [下一课 22 →](../security-governance/README.md)
