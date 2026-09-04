---
status: draft
kind: impl
depends_on: lessons/17, 18, 19, 20；16 作为回顾
---

# M5 生产化

> 让前面四个里程碑的东西可以放心上线：每次改动有回归评测，每次请求有 trace，供应商挂了有 Fallback，成本有账，故障演练过一遍。

## 这一步加什么

- **M5.1 评测**：`eval/` 目录放 Golden set（任务成功率、工具准确率、Recall@k 三类），`scripts/eval_run.py` 跑全部并出报告；CI 里作为门禁，任一指标跌破基线阈值则失败；LLM Judge 用于开放式回答，先用 20 条人工标注校准
- **M5.2 可观测**：OpenTelemetry SDK，span 命名和属性遵循 GenAI 语义约定，`tenant_id`、`thread_id`、`model`、`prompt_version` 是必带属性；导出到 Arize Phoenix（Docker）；结构化 JSON 日志带 `trace_id`；四个故障实验（模型超时、工具报错、检索为空、预算耗尽）各自在 trace 里能一眼看出
- **M5.3 可靠性与成本**：每租户令牌桶限流；模型调用超时加有上限的重试；供应商错误率超阈值时熔断并 Fallback 到备用 adapter；`cost_ledger` 表按租户按天记 token 和费用；预算耗尽时拒绝新运行并给出明确错误；故障演练脚本按顺序注入五种故障并核对系统行为

目标目录：

```text
project/src/aiapp/ops/
├── telemetry.py    # setup_tracing(app), span helpers, GenAI attribute names
├── ratelimit.py    # TokenBucket per tenant (Redis)
├── resilience.py   # with_timeout_retry(), CircuitBreaker, FallbackAdapter(primary, secondary)
└── cost.py         # CostLedger.charge(tenant_id, usage, model)
eval/
├── golden/         # tasks.jsonl, tools.jsonl, retrieval.jsonl
├── judge_calibration.jsonl
└── thresholds.toml
scripts/
├── eval_run.py
└── chaos.py        # --inject model_timeout|tool_error|empty_retrieval|budget|provider_down
docker-compose.yml  # + phoenix
```

关键接口：

```python
class FallbackAdapter:
    def __init__(self, primary: ModelAdapter, secondary: ModelAdapter, breaker: CircuitBreaker): ...
    async def complete(self, messages, tools=None) -> ModelResponse:
        """Try primary under the breaker; on open circuit or failure, use secondary and tag the span."""

class CostLedger:
    async def charge(self, tenant_id: str, usage: Usage, model: str) -> Decimal: ...
    async def remaining(self, tenant_id: str) -> Decimal: ...
```

## 运行步骤

```bash
docker compose up -d postgres redis phoenix
uv run python scripts/eval_run.py --report eval/reports/$(date +%F).md
uv run uvicorn aiapp.api.app:create_app --factory
open http://localhost:6006                       # Phoenix
uv run python scripts/chaos.py --inject model_timeout
uv run python scripts/chaos.py --inject provider_down
```

## 验收证据

- [ ] `eval_run.py` 报告含三类指标和基线对比；故意改坏一个提示词后 CI 门禁变红
- [ ] Judge 和人工标注在校准集上的一致率有记录，低于阈值时报告标黄
- [ ] Phoenix 里一次请求能看到完整链路：API → 模型调用 → 工具 → 检索，每个 span 带租户和 prompt 版本
- [ ] 四个故障实验各有一张 trace 截图或导出，能指出失败发生在哪个 span
- [ ] 失败注入：`chaos.py --inject provider_down` 后请求仍然成功，trace 标记走了 Fallback，恢复后熔断器自动关闭
- [ ] 某租户超出限流或预算时返回明确的 429 / 402 类错误，其他租户不受影响
- [ ] `cost_ledger` 的日汇总和供应商账单在误差范围内对得上

## 依赖的课程

lessons/17, 18, 19, 20；16 作为回顾

---

[← 项目总览](../README.md)
