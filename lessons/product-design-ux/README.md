---
status: complete
structure: narrative
part: Part 5 产品与技术决策
topic: product-and-decisions
tier: deep-dive
estimated_time: 约 25 分钟
---

# 24 AI 产品设计与交互

> 用户不只需要一个答案，还需要知道系统正在做什么、依据是什么、什么时候需要自己决定，以及失败后如何恢复。

<details class="case" markdown="1">
<summary>例子：工具已经暂停等待确认，界面却只显示“正在思考”</summary>

用户不知道是否要等待、批准还是取消，于是重复点击发送。产品把运行时状态隐藏了，用户只能用重复请求来补偿。

!!! note "构造的例子"
    界面状态用于说明反馈和恢复边界；真实文案要结合用户测试。

</details>

## 至少表达六种状态

开始、生成中、调用工具、等待确认、完成、失败 / 可恢复。每种状态要告诉用户：发生了什么、下一步能做什么、是否会产生副作用。

不确定时不要假装确定；引用、来源、工具结果和模型推断要区分。高风险动作要有明确确认，确认内容应包含对象、范围和后果。

## 失败不是一个错误弹窗

把失败分成可重试、需要补充信息、需要人工处理和不可恢复。提供取消、重试、编辑参数、查看证据和回到上一状态的路径。用户看到的状态要和事件线程一致。

## 怎么测

用任务测试和事件回放检查：

- 用户能否判断当前是否需要等待或操作；
- 确认前是否没有副作用；
- 失败后能否恢复且不重复执行；
- 用户完成任务的成功率、取消率、重复提交率和误确认率。

## 参考实现与延伸

参考实现的 Playground、确认状态和错误恢复在 [M5 Production](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m5-production)（核对日期 2026-09-10）。交互状态可对照 [Nielsen usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/)（访问日期 2026-09-10）。

---

[← 上一课 23](../model-adaptation-finetuning-inference/README.md) · [下一课 25 →](../voice-agents/README.md)
