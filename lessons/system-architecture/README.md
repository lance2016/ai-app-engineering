---
status: complete
structure: narrative
part: Part 4 生产工程
topic: production-governance
tier: core
estimated_time: 约 30 分钟
---

# 18 AI 应用系统架构与端到端数据流

> 架构图的价值不是展示组件数量，而是说明每一跳由谁负责、数据从哪里来、状态在哪里落盘，以及失败后如何继续。

<details class="case" markdown="1">
<summary>例子：模型响应很快，但用户等待了十秒，最后还拿到旧数据</summary>

请求链里包含鉴权、会话读取、检索、模型、工具和写回。日志只记录了模型耗时，所以团队误以为模型慢；缓存又没有带版本，导致答案使用了旧文档。

!!! note "构造的例子"
    延迟和旧数据用于说明端到端链路；具体数值需要用 trace 测量。

</details>

## 用一条请求链看系统

```text
客户端 → 网关 / 鉴权 → 线程存储 → Context Builder
      → 模型 → 工具 / 检索 → 业务系统
      → 事件与 trace → 客户端
```

模型不是系统中心的唯一组件。运行时连接状态、权限和外部事实，业务系统决定动作是否真的发生。

## 同步和异步要分开

用户必须立刻看到的内容走同步路径：鉴权、上下文、模型首块、短工具。文档解析、索引重建、长任务和报表走事件或队列。把所有事塞进一次 HTTP 请求，会让取消、重试和恢复都变难。

## 每类状态只由一个地方负责

| 状态 | 权威来源 |
|---|---|
| 身份和租户 | 请求上下文 / 鉴权系统 |
| 任务进度 | 事件线程和运行时 |
| 订单、文件、权限 | 业务数据库 |
| 检索索引 | 数据管线和索引存储 |
| token、耗时、错误 | trace 与成本记录 |

缓存是加速层，不应成为唯一事实来源。每个缓存键要包含租户、版本和失效策略。

## 怎么测

用一次真实请求生成完整 trace，检查：

- 每个阶段的输入、输出、耗时和失败原因是否可见；
- 同步路径是否有明确超时和取消；
- 重试是否可能重复外部副作用；
- 业务写入、事件和用户看到的终态是否一致。

先画数据流，再决定要不要加框架或服务。

## 参考实现与延伸

参考实现的 API、事件线程、运行时和存储在 [M5 Production](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m5-production)（核对日期 2026-09-10）。可对照 [OpenTelemetry traces](https://opentelemetry.io/docs/concepts/signals/traces/)（访问日期 2026-09-10）理解跨组件关联。

---

[← 上一课 17](../data-engineering/README.md) · [下一课 19 →](../evaluation/README.md)
