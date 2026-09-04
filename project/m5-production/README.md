---
status: complete
kind: impl
depends_on: lessons/17, 18, 19, 20；16 作为回顾
---

# M5 生产化

> 让前面四个里程碑的东西可以放心上线：每次改动有评测门禁，每次请求有 trace，供应商挂了有 Fallback，成本有账、有预算，六种故障各演练过一遍，镜像能一条命令起，生产配置不对直接拒绝启动。

## 这一步加什么

- **M5.1 评测**：`aiapp/eval/` 三个套件都跑真实运行时加剧本模型，离线可复现。`tasks` 12 条端到端用例断言轨迹（哪些工具跑了、副作用是否等了批准、注入的删除有没有被白名单挡住、跑偏和步数上限）；`tools` 20 条工具选型；`retrieval` 31 条 Recall@5。`judge.py` 用 20 条人工标注校准 LLM Judge，算一致率和 Cohen's kappa，不一致的用例列出来当 few-shot 素材。`gate.py` 读 `thresholds.toml` 的下限和容忍度，任一套件跌破下限、整体或某个切片相对基线跌超容忍度就失败。`scripts/eval_run.py` 出 Markdown 报告，`--update-baseline` 写基线，CI 里作为门禁；`INJECT_REGRESSION=1` 能演练门禁变红
- **M5.2 可观测**：`ops/telemetry.py` 装 OpenTelemetry SDK，span 名和属性照 GenAI 语义约定：`invoke_agent aiapp` 根 span 带租户、线程、停止原因、步数和 token；每次模型调用一个 `chat <model>` span 带 usage 和 finish reason，空输出标 ERROR；每次工具执行一个 `execute_tool <name>` span 带 route 和 attempts，错误结果标 ERROR 而不是只记事件；HTTP 中间件一个请求 span 带 request id 和 prompt 版本；成本记账一个 `cost.charge` span。`OTEL_EXPORTER_OTLP_ENDPOINT` 指到 Phoenix 就导出，不设就留在内存里给测试和演练脚本读。`ops/logging.py` 是一行一个 JSON 的日志，每行带 trace id。有一个实现细节值得读：SSE 生成器在响应任务里继续跑，contextvars 不跨任务，所以父 span 是显式传的，不靠 ambient context
- **M5.3 可靠性与成本**：`ops/ratelimit.py` 每租户令牌桶，Redis 用一段 Lua 原子执行，内存实现给测试，超限返回 429 加 `Retry-After`；`ops/resilience.py` 带抖动的超时重试、三态熔断器、`FallbackAdapter`（主模型超时或报错就切备用并记下谁服务的；流式只在首块之前切换，因为文本开始流出后没法无缝重来）；`ops/cost.py` 价格表是带日期的 `prices.json`，每次模型调用按 `assistant_message` 事件上的 usage 记账到 `cost_ledger` 表，按租户按天汇总，日预算耗尽返回 402；`scripts/chaos.py` 六个演练：模型超时、供应商宕机、工具持续失败、检索为空、预算耗尽、限流，每个断言预期行为并打印相关 span
- **M5.4 部署**：`Dockerfile` 多阶段构建，`uv sync --frozen --no-dev`，非 root 用户，自带 HEALTHCHECK，`.dockerignore` 把 `.env` 和课程目录挡在外面；`docker-compose.prod.yml` 起应用、PostgreSQL、Redis、Phoenix，`AIAPP_TOKENS` 不设直接起不来，应用容器启动先跑迁移；`GET /readyz` 逐个探测 PostgreSQL、Redis、模型，任一不可用返回 503 并说明哪个；`AIAPP_ENV=production` 时 `Settings.validate_for_production()` 拒绝默认 token、内存存储和故障注入。CI 多了三个门禁：评测、故障演练、构建镜像并冒烟（`/healthz` 通、生产守卫生效）
- **测试** `tests/project/m5/`：21 个用例，限流和成本账在内存与真实后端上各跑一遍

实际目录：

```text
project/src/aiapp/
├── ops/
│   ├── telemetry.py     # setup_tracing(), GenAI 属性常量, span(), mark_error(), recorded_spans()
│   ├── logging.py       # JsonFormatter（带 trace_id）, setup_logging(), log_event()
│   ├── ratelimit.py     # RateLimiter 协议, InMemoryRateLimiter, RedisRateLimiter（Lua）
│   ├── resilience.py    # with_timeout_retry(), CircuitBreaker, FallbackAdapter
│   ├── cost.py          # PriceTable, CostLedger, BudgetExhausted, InMemoryCostStore
│   ├── postgres_cost.py # PostgresCostStore（cost_ledger 表）
│   └── health.py        # run_checks(), postgres_check(), redis_check()
├── eval/
│   ├── suites.py        # run_tasks() / run_tools() / run_retrieval()
│   ├── judge.py         # calibrate(), cohen_kappa(), scripted_judge()
│   └── gate.py          # Thresholds, gate(), scores()
├── prices.json          # 带日期的价格表
├── api/routes/health.py # /healthz, /readyz
└── storage/migrations/versions/0003_cost_ledger.py
project/eval/
├── golden/{tasks,tools}.jsonl
├── judge_calibration.jsonl
├── thresholds.toml
├── baseline.json
└── reports/
scripts/eval_run.py, scripts/chaos.py
Dockerfile, docker-compose.prod.yml, .dockerignore
tests/project/m5/
├── test_resilience.py, test_ratelimit_and_cost.py, test_telemetry_and_api.py, test_eval_gate.py, test_deployment_files.py
```

## 基线（2026-09-04，fake 模型）

| 套件 | n | 通过率 | 下限 |
|---|---|---|---|
| tasks | 12 | 100% | 95% |
| tools | 20 | 100% | 90% |
| retrieval | 31 | 90% | 85% |

Judge 校准：20 条，一致率 85%，kappa 0.70，三条不一致都是 judge 对含糊或过度承诺的回答太宽松。fake 模型下 tools 是 100% 因为剧本就是答案，这个套件的真实基线要用 `MODEL_PROVIDER=deepseek uv run python scripts/eval_run.py --real-tools` 跑出来再写回 `baseline.json`。

## 运行步骤

```bash
uv run pytest tests/project/m5 -q
uv run python scripts/eval_run.py                       # 门禁；--update-baseline 接受当前数字
INJECT_REGRESSION=1 uv run python scripts/eval_run.py   # 看门禁变红：tools 掉到下限以下
uv run python scripts/chaos.py --all                    # 六个演练；--inject provider_down 单跑一个；--spans 看全部 span

# 带 trace 跑起来
docker compose up -d --wait                             # 含 Phoenix
export DATABASE_URL=postgresql+asyncpg://aiapp:aiapp@localhost:5432/aiapp REDIS_URL=redis://localhost:6379/0
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:6006 AIAPP_FALLBACK_PROVIDER=fake AIAPP_DAILY_BUDGET_USD=1 \
  uv run uvicorn aiapp.api.app:create_app --factory
open http://localhost:6006                              # Phoenix：一次请求 = POST → invoke_agent → chat / execute_tool → cost.charge
curl -s localhost:8000/readyz

# 生产形态
AIAPP_TOKENS=tok1:tenant-a docker compose -f docker-compose.prod.yml up --build
docker run --rm -e AIAPP_ENV=production aiapp:ci        # 没有 AIAPP_TOKENS：refusing to start in production
```

## 验收证据

- [x] `eval_run.py` 报告含三类指标和基线对比；`INJECT_REGRESSION=1` 让门禁变红（`test_gate_catches_an_overall_and_a_slice_regression`，CI 步骤 "Evaluation gate"）
- [x] Judge 和人工标注在校准集上的一致率有记录，低于阈值时报告标黄（`test_judge_calibration_reports_agreement_and_kappa`，宽松 judge 的 kappa 为 0）
- [x] 一次请求能看到完整链路 POST → invoke_agent → chat / execute_tool → cost.charge，每个 span 带租户和 prompt 版本（`test_a_run_produces_the_genai_span_tree`）；Phoenix 里看是同一棵树
- [x] 故障实验各自在 trace 里能一眼看出：模型超时是 `chat` span ERROR + `error.type=TimeoutError`，工具失败是 `execute_tool` ERROR + `route=transient_exhausted` + `attempts=3`，空输出是 `aiapp.empty_output`（`test_model_timeout_marks_chat_and_root_spans_error`，`chaos.py --spans`）
- [x] 失败注入：`chaos.py --inject provider_down` 后请求仍然成功，`served_by` 显示走了 Fallback，熔断器三次失败后打开、后续请求不再碰主模型；恢复窗口后半开探测（`test_breaker_opens_after_threshold_and_half_opens_after_cooldown`）
- [x] 某租户超出限流或预算时返回 429 / 402，其他租户不受影响（`test_rate_limit_returns_429_with_retry_after_and_isolates_tenants`，`test_budget_returns_402_and_ledger_records_usage`，chaos `rate_limit` / `budget`）
- [x] `cost_ledger` 按租户按天汇总，价格表带日期，未知模型按默认价而不是零（`test_ledger_prices_by_model_and_enforces_the_daily_budget`）。和供应商账单对账要有真实 key 跑过再做
- [x] `/readyz` 在依赖不可达时返回 503 并指出哪个（`test_readiness_reports_each_dependency`）
- [x] 镜像可构建、容器起来 `/healthz` 通、缺 `AIAPP_TOKENS` 的生产配置拒绝启动（CI job `image`；`test_production_mode_refuses_unsafe_configuration`）
- [ ] 真实模型下的 tools 基线和 judge 校准：需要 key，跑 `--real-tools` 和 `REAL_JUDGE=1` 后把数字写回
- [ ] 安全测试里"带注入的文档进知识库后模型被诱导删除"这条走了 `tasks.jsonl` 的 `task-injected-delete-blocked`（白名单挡住），跨租户查询靠 `search_knowledge` 只从 `RunContext` 取租户；第 20 课的 PII 出站过滤没有做，留给 Capstone 1

## 依赖的课程

lessons/17, 18, 19, 20；16 作为回顾

---

[← M4](../m4-rag-and-memory/README.md) · [项目总览](../README.md) · [M6 →](../m6-platform-design/README.md)
