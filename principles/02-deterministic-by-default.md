---
status: complete
---

# 原则 02｜默认用确定性 Workflow，只把真正需要判断的节点交给模型

> 每把一个决定交给模型，系统就多一个不可预测点、多一次调用的钱和延迟、少一处能写单元测试的地方。所以默认不交，交出去的每一处都要有理由。

## 主张

拿到需求时，先假设整条路径都能用代码写死，然后逐步找出哪几个节点确实需要理解自然语言、做开放式判断或从多个选项里选。只有那几个节点用模型，其余全部是普通代码。

Anthropic 跟几十个团队做完 Agent 的总结是：最成功的实现用的是简单、可组合的模式，而不是复杂框架；很多场景根本不需要 agentic 系统，一次调用加检索加几个示例就够了。复杂度只在简单方案确实不够时才增加。

这条原则给出一个顺序：确定性代码 → prompt chaining → routing → parallelization → orchestrator-workers → evaluator-optimizer → 自治 Agent。从左往右，模型的决策权变大，系统的可预测性变小。每往右一格，都要能回答"左边那格为什么不够"。

## 违反它会怎样

- **步骤固定的任务做成了 Agent。** "抽取、校验、生成报告"三步被交给一个循环，模型有时跳过校验，有时生成两次。它的路径明明是固定的。
- **把业务规则写进提示词。** "退款超过 30 天要经理审批"写在系统提示词里，模型大多数时候遵守，偶尔不。这条规则应该是 `if days > 30: escalate()`，一行代码，百分之百遵守，还能测。
- **让模型决定要不要停。** 没有步数上限、没有预算，全靠模型"觉得做完了"。第 06 课整课都在讲这个的后果。
- **用 Agent 框架的默认循环处理所有请求。** 简单问题也走一遍完整的规划、工具选择、反思，延迟是直接回答的五倍，成本是十倍。

## 最小做法

对每个节点问一个问题：**这一步的输入到输出，能不能用代码写出来？** 能，就写代码。

```python
async def handle_refund(request):
    order = await orders.get(request.order_id)          # deterministic
    if (today() - order.date).days > 30:                 # deterministic rule
        return await escalate_to_manager(order)
    reason = await model.classify(request.text, REASONS)  # the one judgment call
    if reason not in REASONS:                            # validate what came back
        reason = "other"
    return await refund(order, reason)                   # deterministic
```

五行里只有一行是模型调用，而且它的输出立刻被校验。这就是"默认确定性"的样子。

## 对照

- 参考：[Anthropic · Building effective agents](https://www.anthropic.com/research/building-effective-agents)（访问日期 2026-09-04）；[12-factor-agents · factor 08 Own your control flow](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-08-own-your-control-flow.md)（访问日期 2026-09-04）
- 相关课程：[09 Workflow 还是 Agent](../lessons/09-workflow-vs-agent/README.md)、[06 Agent 循环与控制流](../lessons/06-agent-loop/README.md)

---

[← 原则总览](./README.md)
