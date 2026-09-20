---
status: complete
structure: narrative
part: Part 3 知识与记忆
topic: knowledge-data
tier: deep-dive
estimated_time: 约 30 分钟
---

# 16 Memory：提取、整合与检索

> “记忆”不是模型内部多了一块存储，而是运行时从历史中提取、保存、检索和删除信息的一套数据管线。

<details class="case" markdown="1">
<summary>例子：模型推断用户不吃辣，之后用户却无法删除这条偏好</summary>

记忆没有来源、置信度和删除入口，模型的一次猜测就变成了长期事实。下次推荐时，系统既不知道为什么这样记，也不知道该删哪一条。

!!! note "构造的例子"
    偏好和删除问题用于说明记忆的生命周期；真实产品还要遵守隐私和同意策略。

</details>

## 记忆有四个动作

```text
提取 → 整合 → 检索 → 定向删除
```

每个动作都可以是确定性代码加模型判断，但最终写入要带来源、时间、租户、置信度和删除条件。对话历史不是长期记忆的自动授权。

## 记忆和业务事实分开

用户偏好、过去经验和摘要可以进入记忆存储；订单状态、权限和余额必须回到业务数据库。记忆适合帮助模型理解用户，不适合作为事实系统。

冲突时优先级通常是：用户当前明确说明 > 业务系统事实 > 有来源的历史记忆 > 模型推断。这个优先级应写进运行时，而不是让模型自由决定。

## 怎么测

准备包含明确说法、隐含说法、冲突、过期和删除请求的对话集。测：

- 提取 precision：是否只记值得跨会话使用的内容；
- 检索 relevance：是否在需要时取到正确记忆；
- 冲突处理：新事实是否覆盖旧推断；
- 定向删除：用户删除后是否不再被召回。

## 参考实现与延伸

参考实现的 Memory 提取、来源和删除在 [M4 RAG 与 Memory](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m4-rag-and-memory)（核对日期 2026-09-10）。隐私删除可对照 [GDPR right to erasure](https://commission.europa.eu/law/law-topic/data-protection/data-protection-eu_en)（访问日期 2026-09-10）。

---

[← 上一课 15](../rag-end-to-end/README.md) · [下一课 17 →](../data-engineering/README.md)
