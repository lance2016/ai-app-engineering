---
status: complete
structure: narrative
part: Part 2 Tool 与 Agent
topic: capability-ecosystem
tier: deep-dive
estimated_time: 约 25 分钟
---

# 13 Skill 与能力生态分层

> Tool、MCP、Skill、Plugin 和 A2A 都能被叫作“能力”，但它们负责的层次不同。混在一起会让权限、版本和故障边界消失。

<details class="case" markdown="1">
<summary>例子：把 Skill 当成权限配置，模型按 Skill 里的说明调用了当前用户没有权限的工具</summary>

Skill 通常是教模型如何使用能力的说明，不是安全边界。工具白名单、身份和授权仍由运行时绑定。

!!! note "构造的例子"
    Skill 内容和调用用于说明“说明不等于权限”；真实能力包需要按来源和版本审计。

</details>

## 五层能力各管什么

| 层 | 它是什么 | 谁负责安全 |
|---|---|---|
| Tool | 当前运行时可执行的函数 | 运行时 |
| MCP | 跨进程发现和调用工具的协议 | host 与运行时 |
| Skill | 教模型完成一类工作的说明和资源 | 宿主加载器与运行时 |
| Plugin | 宿主软件的扩展包 | 宿主平台 |
| A2A / Handoff | Agent 之间的任务交接 | 调度器与双方运行时 |

它们可以组合，但不能互相替代。尤其是 Skill 不提供租户隔离，MCP 不自动提供业务幂等。

## 能力包的生命周期

加载时验证来源、版本和哈希；注册时生成可见工具清单；执行时按当前身份和风险重新授权；升级时重新跑评测和安全样本。不要按名字从网络直接拉取最新版。

## 怎么测

建立一份能力清单，测试新增、删除、升级、权限变化和 server 断开。检查：

- 模型能看到的能力是否等于当前允许的能力；
- 能力描述变化是否触发回归；
- Skill 是否能诱导越权工具调用；
- 每一层失败能否定位到加载、发现、授权或执行。

## 参考实现与延伸

参考实现把 Skill、MCP 和工具注册放在 [Framework Lab](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/framework-lab) 与 [M3 Tool Workflow](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m3-tool-workflow)（核对日期 2026-09-10）。协议边界可对照 [MCP specification](https://modelcontextprotocol.io/specification/2025-11-25)（访问日期 2026-09-10）。

---

[← 上一课 12](../mcp/README.md) · [下一课 14 →](../agent-harness/README.md)
