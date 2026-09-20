---
status: complete
structure: narrative
part: Part 2 Tool 与 Agent
topic: runtime
tier: core
estimated_time: 约 35 分钟
---

# 08 Agent 的 Context Engineering

> 从应用的角度看，模型服务不会替你持有这次任务的状态。运行时每一轮都要决定：把什么放进窗口，什么删掉，什么只能作为不可信数据出现。

<details class="case" markdown="1">
<summary>例子：用户说过对花生过敏，长对话压缩后 Agent 又推荐了含花生的菜</summary>

摘要保留了“用户喜欢中餐”，却丢了“对花生过敏”。问题不一定在模型，而在上下文构建没有区分高风险约束和普通闲聊。

!!! note "构造的例子"
    对话和摘要用于说明裁剪风险；保留策略需要在产品的真实对话上评测。

</details>

## Context 是一次请求的全部输入

```text
固定指令 + 当前任务 + 可靠事实 + 历史摘要 + 最近事件 + 工具观察 + 检索结果
```

Prompt 是其中的指令部分，Context 是实际发送的完整窗口。模型看不到没有被放进请求的状态，也不能替运行时保存状态。

## 组装顺序比“塞满窗口”重要

先放不可丢的约束和当前任务，再放与当前任务相关的事实，最后放可裁剪历史。外部文档和工具结果要标明来源和不可信边界。

| 内容 | 默认策略 |
|---|---|
| 权限、合规和用户明确约束 | 不压缩，超预算就换策略或请求澄清 |
| 当前任务与结构化状态 | 保留原形 |
| 检索结果与工具观察 | 限长、去重、保留来源 |
| 普通历史 | 摘要或按相关性裁剪 |

```python
def build_context(state, budget):
    fixed = [state.system_rules, state.current_task, state.authority]
    facts = select_relevant(state.observations, budget.remaining(fixed))
    history = compress_history(state.messages, budget.remaining(fixed + facts))
    return fixed + facts + history
```

这段代码只说明决策顺序，省略 token 计算和具体消息类型，不能直接运行。`build_context` 的输出应该能被记录和回放。

## 三种操作不要混为一谈

- **裁剪**：删除低价值内容，成本最低但可能丢信息。
- **压缩**：用摘要保留信息，摘要本身可能产生错误。
- **检索**：按当前问题重新找证据，能补回历史但依赖索引质量。

缓存只适合稳定前缀或确定结果，不能把带权限和用户状态的内容跨请求复用。

## 怎么测

保存每次请求的 context snapshot，测：

- 关键约束在不同轮数和压缩后是否仍然存在；
- 上下文 token、首 token 延迟和成本；
- 工具结果过长时是否被截断并保留错误标记；
- 同一问题在原始历史和压缩历史下的答案差异。

上下文评测要包含“应该保留什么”和“必须丢掉什么”两类样本。

## 参考实现与延伸

参考实现的上下文预算、工具结果整形和事件线程在 [M3 Tool Workflow](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m3-tool-workflow)（核对日期 2026-09-10）。可对照 [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)（访问日期 2026-09-10）。

---

[← 上一课 07](../agent-state-and-runtime/README.md) · [下一课 09 →](../workflow-vs-agent/README.md)
