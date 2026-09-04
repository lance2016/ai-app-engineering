---
status: draft
updated: 2026-09-04
---

# Track｜语音、机器人与具身 AI Agent

> 主线讲的是"把 LLM 做成可上线的 Agent 系统"。这条 track 讲当这个系统长了耳朵、嘴和身体之后多出来的问题：声音是流、用户会插话、每段延迟都听得见、动作不可撤销、用户可能是孩子。
> 素材来自作者的语音机器人生产项目，只保留架构模式和取舍，不含业务细节。

## 目录

| # | 篇 | 一句话 | 状态 |
|---|---|---|---|
| 01 | [语音 Agent 的整体管线](./01-voice-agent-pipeline.md) | pipeline 与 Realtime 两种形态，轮次是核心抽象 | draft |
| 02 | [打断与背压](./02-interruption-and-backpressure.md) | 用户不会等你说完；作废三类进行中的工作 | draft |
| 03 | [端到端延迟预算](./03-latency-budget.md) | 一秒钟分给七个环节，按 P95 定预算 | draft |
| 04 | [双模型竞速](./04-dual-model-racing.md) | 聊天模型和意图模型并行，运行时按矩阵合并 | draft |
| 05 | [设备端工具下发](./05-device-tool-dispatch.md) | 工具在另一台机器上，而且会动 | draft |
| 06 | [具身场景的状态与安全](./06-embodied-state-and-safety.md) | 边界分三层，绝对不能发生的事放最底层 | draft |
| 07 | [语音场景的评测](./07-evaluating-voice-agents.md) | 文本、管线、动作三层评测加回归门禁 | draft |

## 前置

主线 Part 2 的 [05](../../lessons/05-tool-calling/README.md)、[06](../../lessons/06-agent-loop/README.md)、[07](../../lessons/07-agent-state-and-runtime/README.md) 三课。这条 track 假设你已经知道工具契约、Agent 循环和事件线程是什么，只讲语音和具身带来的增量。

## 状态说明

七篇都是 draft：架构模式和取舍已写，没有代码。原因是语音管线的代码离不开 ASR/TTS 供应商和设备端，做不到"离线 fake 一跑就通"。下一步会以回放音频加假设备的形式加 `code/`（假 ASR 分片、假 TTS 时长、轮次管理、打断注入、延迟埋点、双模型竞速、带安全边界的假设备、回放评测），全部复用 `aiapp` 运行时；并补三篇具身章节：LLM 作为 planner 调度技能原语、动作不可撤销时的确认与仿真预演、设备状态同步与离线兜底。

素材公开范围的规则：不出现产品名、内部接口名、模型名、人名、公司名；提到项目时统一说"作者的语音机器人项目"。

## 参考

- [LiveKit Agents](https://docs.livekit.io/agents/)（访问日期 2026-09-04）：pipeline 形态的开源框架，术语以它为准。
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)、[Gemini Live API](https://ai.google.dev/gemini-api/docs/live)（访问日期 2026-09-04）：Realtime 形态的两个代表。

---

[← 课程总表](../../README.md)
