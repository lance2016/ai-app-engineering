---
status: complete
structure: narrative
part: Part 2 Tool 与 Agent
topic: capability-ecosystem
tier: deep-dive
estimated_time: 约 30 分钟
---

# 12 MCP：模型上下文协议

> MCP 解决的是能力接入的重复工作：server 暴露工具和资源，host 负责发现、授权、调用和记录。它不替你完成安全和业务校验。

<details class="case" markdown="1">
<summary>例子：MCP server 更新了参数，Agent 仍按缓存的旧 schema 调用</summary>

协议连接仍然正常，调用却不断返回参数错误。问题不在“能否连上”，而在能力契约的版本和缓存失效没有设计。

!!! note "构造的例子"
    schema 变化用于说明生命周期问题；真实错误码和传输方式以 server 文档为准。

</details>

## 只记住三个动作

```text
initialize → 建立能力与版本边界
tools/list → 发现工具契约
tools/call → 提交一次调用
```

MCP 传输和消息格式解决互操作；工具是否允许当前用户使用、参数是否安全、结果是否可信，仍然属于你的运行时。

## 接入远端能力要多一层守卫

| 检查 | 为什么需要 |
|---|---|
| 来源与版本 | server 可能被替换或升级 |
| 工具白名单 | “被发现”不等于“可调用” |
| 参数 schema | 远端契约仍需本地校验 |
| 租户与身份 | server 不应从模型参数猜身份 |
| 超时与重连 | 远程进程会断开或变慢 |

错误要分为参数错误、瞬时不可用、权限拒绝和未知副作用。它们的下一步不同，不能都回喂给模型。

## 怎么测

用一个可控 server 回放：首次握手、工具列表变化、参数错误、断开重连、权限拒绝和恶意描述。检查：

- schema 变更是否能被发现；
- 未授权工具是否在执行前被拦截；
- 断线是否有超时和明确终态；
- 每次远端调用是否进入 trace 和审计。

## 参考实现与延伸

参考实现的 MCP client 和运行时接缝在 [M3 Tool Workflow](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m3-tool-workflow)（核对日期 2026-09-10）。协议细节查 [MCP specification](https://modelcontextprotocol.io/specification/2025-11-25)（访问日期 2026-09-10）。

---

[← 上一课 11](../multi-agent-handoff/README.md) · [下一课 13 →](../skills-and-capability-layers/README.md)
