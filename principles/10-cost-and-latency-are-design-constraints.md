---
status: complete
---

# 原则 10｜成本和延迟是设计约束，不是上线后的运维问题

> 一次模型调用的钱和时间都是由设计决定的：放了多长的上下文、选了哪个模型、循环允许跑几步、有没有缓存。上线后运维能做的只是把账单和 p95 画成图给你看。

## 主张

传统 Web 服务里，一个请求的成本接近零、延迟接近常数，所以"先做功能再优化性能"是可行的。LLM 应用不是这样：每个请求的成本和延迟随上下文长度、模型档位、循环步数线性甚至超线性增长，而这三样都是在写代码时决定的。所以：

1. **每个请求要能算出钱。** 响应里有 usage，乘上带日期的价格表，按租户归因。这不是财务的事，是运行时的事，因为预算耗尽要能当场停下（第 06 课）。
2. **模型按任务分档。** 意图分类、字段抽取这类任务用小模型，开放式生成才用大模型。评测集告诉你小模型够不够，而不是"以防万一都用最大的"。
3. **延迟预算要拆到每一层。** 用户能等的总时间是固定的，模型调用、工具执行、检索各自能占多少要事先分配，超了就该降级而不是让用户等。
4. **缓存和裁剪是设计的一部分。** 系统提示和工具描述放在上下文开头以命中提供商的缓存（第 08 课），历史按策略裁剪，相同问题不重复调用。

## 违反它会怎样

- **月底才发现账单翻了十倍。** 某个循环在特定输入下不收敛，每次跑到步数上限才停，每步都带着完整历史。没有按请求计费的话，这个问题在账单上才可见，那时已经跑了三十天。
- **所有任务都用旗舰模型。** 一个"判断用户是不是要退出"的分类任务也走最贵的模型，成本是小模型的二十倍，延迟是三倍，而准确率在评测集上没有差别。
- **上下文只增不减。** 对话历史全部带上，第五十轮的一次调用花的钱是第一轮的五十倍，延迟也跟着涨，用户感觉越聊越卡。
- **没有超时预算的工具链。** 检索 3 秒、模型 8 秒、工具 5 秒，加起来 16 秒，每一段单看都"还行"，用户已经走了。

## 最小做法

```python
@dataclass
class RequestBudget:
    max_usd: float
    max_seconds: float
    spent_usd: float = 0.0
    started: float = field(default_factory=time.monotonic)

    def charge(self, model: str, usage: Usage) -> None:
        p = PRICES[model]  # one table, dated, loaded from config
        self.spent_usd += (usage.input_tokens * p["in"] + usage.output_tokens * p["out"]) / 1e6

    def remaining_seconds(self) -> float:
        return self.max_seconds - (time.monotonic() - self.started)

    @property
    def exhausted(self) -> bool:
        return self.spent_usd >= self.max_usd or self.remaining_seconds() <= 0
```

循环每一步结算一次，`exhausted` 为真就以明确的原因停止。模型选择写成 `pick_model(task)` 一个函数，让评测数据决定它的分支。

## 对照

- 参考：[12-factor-agents · factor 11 Trigger from anywhere](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-11-trigger-from-anywhere.md)（访问日期 2026-09-04，"outer loop agents 可以跑 5 到 90 分钟"那一段说明为什么预算必须是显式的）；[ai-agents-for-beginners · 16 Deploying Scalable Agents](https://github.com/microsoft/ai-agents-for-beginners/blob/main/16-deploying-scalable-agents/README.md)（访问日期 2026-09-04，Cost Optimisation 一节的三个杠杆）
- 相关课程：[20 可靠性、成本、部署与 LLMOps](../lessons/20-reliability-cost-llmops/README.md)、[06 Agent 循环与控制流](../lessons/06-agent-loop/README.md)

---

[← 原则总览](./README.md)
