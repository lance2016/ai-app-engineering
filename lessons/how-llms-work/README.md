---
status: complete
structure: narrative
part: Part 1 模型与上下文
topic: model-interface
tier: core
estimated_time: 约 30 分钟
---

# 01 从模型到应用：能力、成本与选型

> 这课只回答一个问题：面对多个模型，凭什么选出“够用且可控”的那个，而不是凭排行榜或感觉。

<details class="case" markdown="1">
<summary>例子：换了更强的模型，意图识别反而把退款请求分错</summary>

升级模型后，开放式回答变好了，但退款意图的准确率下降。原因可能是输出格式变了、标签边界变了、延迟预算不够，不能只看总榜分数。

!!! note "构造的例子"
    场景用于说明选型不能只看能力排名；具体模型、分数和价格需要用自己的评测集重新测量。

</details>

## 选型先看四个约束

模型不是“越大越好”的插件。先写清：

| 约束 | 要问什么 | 怎么拿证据 |
|---|---|---|
| 能力 | 它能否稳定完成这类任务 | 小型 golden set，按场景切片 |
| 输出 | 能否返回可解析、可校验的结果 | schema 解析率、拒答率 |
| 成本 | 一次请求最多花多少钱 | 输入/输出 token × 价格 |
| 延迟 | 用户和下游各能等多久 | p50/p95，加上工具等待 |

硬约束先于价格。一个便宜但无法返回结构化结果的模型，实际成本可能更高，因为失败会触发重试和人工处理。

## 模型能力要用探针测

模型卡和排行榜适合筛选候选，不足以证明它适合你的业务。探针是一组最小输入，每条都配一个确定性检查：

```python
cases = [
    {"input": "把退款原因归为 shipping、quality 或 other", "must_include": ["shipping", "quality", "other"]},
    {"input": "从这段文本抽取 order_id", "schema": OrderId},
]

for case in cases:
    result = model.complete(case["input"])
    assert validate(result, case)
```

这只是说明评测形状，省略了模型接口和错误记录，不能直接运行。重点不是断言写法，而是每次换模型都跑同一批输入。

## 成本不是一次调用的价格

一次对话的成本大致是：

```text
总成本 = Σ(输入 token × 输入单价 + 输出 token × 输出单价)
```

输入历史、工具结果和检索片段会在每轮重复计费。比较模型时至少记录每个请求的 token、耗时、重试次数和最终结果，不能只看供应商的单价。

## 最容易犯的三个错误

- **把排行榜当业务评测**：通用分数无法替代自己的任务切片。
- **只测成功回答**：还要测格式错误、拒答、超时和工具调用。
- **换模型不跑回归**：模型升级可能改变语气、字段、工具选择和安全边界。

“模型是不可信的部件”不是说它没有能力，而是说它的能力必须通过输入、输出和评测来确认。

## 怎么测

保留一份带标签的探针集，至少按任务类型、语言、长短和风险等级切片。每次模型变更比较：

- 任务成功率和结构化解析率；
- p95 延迟、重试率和单请求成本；
- 高风险切片是否出现新的越权或幻觉。

把失败样本加入 golden set，而不是只记录平均分。

## 参考实现与延伸

参考实现的模型适配器和 fake model 在 [M1 API 骨架](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m1-api-skeleton)，模型成本和容量决策在 [M5 生产化](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m5-production)（核对日期 2026-09-10）。

价格和能力会变化，使用前查供应商的[模型与价格文档](https://api-docs.deepseek.com/quick_start/pricing)（访问日期 2026-09-10）。下一课进入调用接口和输出形状。

---

[← 上一课 00](../setup/README.md) · [下一课 02 →](../model-api-structured-output-streaming/README.md)
