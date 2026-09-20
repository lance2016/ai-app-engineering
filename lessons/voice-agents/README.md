---
status: complete
structure: narrative
part: Part 5 产品与技术决策
topic: product-and-decisions
tier: deep-dive
estimated_time: 约 30 分钟
---

# 25 语音应用：链路、延迟预算与打断

> 语音应用不是聊天页面加一个麦克风。用户听不到中间文本，且会随时打断，所以延迟、状态和取消要成为一等边界。

<details class="case" markdown="1">
<summary>例子：模型还在朗读上一句，用户已经说“等等”，系统却继续执行后面的工具</summary>

播放、语音识别、模型生成和工具执行没有共享取消信号。用户以为自己打断了，副作用却已经发生。

!!! note "构造的例子"
    打断链用于说明取消传播；真实体验要用目标设备和网络测量。

</details>

## 级联链路和实时链路

```text
麦克风 → ASR → 模型 / 工具 → TTS → 扬声器
```

级联方案容易拆开观测，代价是每一段都可能增加延迟；实时语音模型减少中间跳转，但改变了供应商、成本和状态边界。先根据延迟目标和可观测性选择，不要只看演示效果。

## 延迟预算要分配

总等待时间包括首个可听反馈、完整回答和工具结果。ASR、模型首 token、工具、TTS 都要有预算；一段超时就要降级、说出等待状态或结束当前任务。

## 打断必须取消整条链

用户打断时至少取消播放、未完成生成、可取消工具和后续 TTS。不可取消的外部副作用要在执行前确认，执行后进入结果播报或人工处理，不要把取消当成回滚。

## 怎么测

录制包含停顿、重叠、纠正和打断的语音集，测：

- 首个可听反馈和完整回答的 p50/p95；
- 打断识别率和取消传播延迟；
- 工具副作用在确认前是否被阻止；
- 网络断开、重复输入和用户改口后的状态一致性。

## 参考实现与延伸

参考实现保留了语音事件协议和断线验收说明，见 [voice-agents demo](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/demos/voice-agents.md)（核对日期 2026-09-10）。实时通信基础可对照 [WebRTC overview](https://webrtc.org/getting-started/overview)（访问日期 2026-09-10）。

---

[← 上一课 24](../product-design-ux/README.md) · [下一课 26 →](../system-design-decisions/README.md)
