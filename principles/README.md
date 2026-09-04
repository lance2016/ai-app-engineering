# 12 条 AI 应用工程原则

> 借 [12-factor-agents](https://github.com/humanlayer/12-factor-agents) 的形式：一条原则一个文件，观点先行。
> 前 6 条和 12-factor 高度重合，这是有意的；7～12 条是从生产视角补的，12-factor 没有覆盖。
> 每条原则都应在 `lessons/` 里有至少一课作为落点。

| # | 原则 | 状态 |
|---|---|---|
| 01 | [模型输出是建议，不是执行结果](./01-model-output-is-a-suggestion.md) | complete |
| 02 | [默认用确定性 Workflow，只把真正需要判断的节点交给模型](./02-deterministic-by-default.md) | complete |
| 03 | [Prompt 和 Context Window 必须自己掌控，不交给框架黑盒](./03-own-your-prompts-and-context.md) | complete |
| 04 | [Tool 就是带契约的结构化输出](./04-tools-are-contracts.md) | complete |
| 05 | [状态由运行时持有，分清对话、任务、业务、长期记忆四类](./05-runtime-owns-state.md) | complete |
| 06 | [每个副作用都要幂等、可确认、可审计](./06-side-effects-are-idempotent-and-auditable.md) | complete |
| 07 | [失败要分层定位：数据、检索、上下文、模型、工具、控制流](./07-locate-failures-by-layer.md) | complete |
| 08 | [没有评测集，就没有「变好了」](./08-no-eval-no-improvement.md) | complete |
| 09 | [Trace 是一等公民，第一次调用就该有](./09-trace-is-first-class.md) | complete |
| 10 | [成本和延迟是设计约束，不是上线后的运维问题](./10-cost-and-latency-are-design-constraints.md) | complete |
| 11 | [安全边界由确定性代码执行，不靠提示词](./11-guardrails-in-code-not-prompts.md) | complete |
| 12 | [模型是可替换的适配器，任何代码都不该绑死一家供应商](./12-models-are-swappable-adapters.md) | complete |

## 怎么读

原则不是课程。先扫一遍知道有哪些主张，学完对应课再回来看会有不同体会。
每条原则的结构固定：主张 → 违反它会怎样 → 最小做法 → 对照。
