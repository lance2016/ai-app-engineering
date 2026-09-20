---
status: complete
structure: narrative
part: Part 4 生产工程
topic: production-governance
tier: core
estimated_time: 约 35 分钟
---

# 19 评测：Golden Set、LLM Judge 与 Agent Eval

> “感觉更好了”不是评测结论。评测要把一次改动和一组可重复的输入、标准、基线连接起来。

<details class="case" markdown="1">
<summary>例子：总分上升，但最重要的权限切片全部退步</summary>

新增的普通问题很多，拉高了平均分；高风险问题数量少，所以回归被平均数掩盖。上线后用户只遇到高风险切片，体验反而变差。

!!! note "构造的例子"
    分数变化用于说明切片和门禁；实际阈值需要根据产品风险设定。

</details>

## 评测分四层

| 层 | 适合回答 | 是否每次提交运行 |
|---|---|---|
| 确定性断言 | schema、权限、事件顺序 | 是 |
| 回放 | 代码和适配器有没有破坏既有行为 | 是 |
| Golden set | 这版模型 / Prompt 是否更好 | 定期或发布前 |
| 人或 Judge | 开放式质量和解释 | 校准后使用 |

CI 通过只能说明评测代码没坏，不能证明模型质量变好了。

## Golden set 要能暴露问题

每个样本保存问题、期望行为、标签、风险、来源和版本。除了成功案例，还要加入拒答、越权、长上下文、工具失败和证据不足的样本。样本按标签切片，避免平均分掩盖退步。

## Judge 不是权威答案

Judge 需要一批人工标注的校准集。比较它和人的一致性，检查不同语言、长度、风险等级是否偏置；调 Judge 的数据和验收 Judge 的数据要分开。没有校准，就不能只因为“模型打了分”而相信它。

## 轨迹评测看过程

Agent 不能只评最终文本，还要检查：工具是否选对、参数是否合规、是否越过确认门、失败后是否停止、预算是否耗尽。轨迹的事实来自事件和 trace，不来自模型自己的总结。

## 怎么测

每次改 Prompt、模型、检索或运行时，比较旧版和新版：

- 总分与每个风险切片的变化；
- 任务成功率、引用支持率和工具守卫命中率；
- 延迟、token、成本和重试率；
- 新增失败样本是否进入下一版 golden set。

门禁要规定允许下降的范围；高风险切片通常不能用平均分抵消。

## 参考实现与延伸

参考实现的 golden set、Judge 和回归门禁在 [M5 Production](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m5-production)（核对日期 2026-09-10）。可对照 [OpenAI Evals](https://github.com/openai/evals)（访问日期 2026-09-10）理解评测集与评测器的分离。

---

[← 上一课 18](../system-architecture/README.md) · [下一课 20 →](../observability/README.md)
