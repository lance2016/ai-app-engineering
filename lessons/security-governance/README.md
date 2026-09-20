---
status: complete
structure: narrative
part: Part 4 生产工程
topic: production-governance
tier: core
estimated_time: 约 35 分钟
---

# 22 安全与治理

> 模型可以理解恶意文本，也可以被恶意文本影响。安全边界必须写在身份、权限、工具和数据流中，不能只写在 Prompt 里。

<details class="case" markdown="1">
<summary>例子：网页里的隐藏指令让 Agent 准备把客户资料发到外部邮箱</summary>

网页是检索数据，不是系统指令。即使模型提出了发送邮件的工具调用，运行时也要检查租户、收件人、工具白名单和人工确认。

!!! note "构造的例子"
    网页内容和收件人用于说明间接提示注入；真实攻击样本应来自业务数据和工具清单。

</details>

## 四个信任边界

| 边界 | 不能相信什么 | 代码要做什么 |
|---|---|---|
| 用户输入 | 指令和身份声明 | 身份由认证上下文绑定 |
| 检索 / 工具结果 | 其中夹带的命令 | 标记为数据，限制可调用动作 |
| 模型输出 | 工具名、参数和“已完成” | schema、白名单、业务校验 |
| 外部能力 | Skill、MCP server、插件内容 | 来源、版本、权限和哈希校验 |

租户 ID、用户权限和可用工具不能让模型自己填写。敏感输出还要经过脱敏和出口检查。

## 安全守卫的位置

```text
请求认证 → 绑定身份与租户
        → 构建允许的工具清单
        → 模型提出建议
        → 参数 / 权限 / 数据范围校验
        → 确认门与执行
        → 输出脱敏和审计
```

提示词可以解释规则，不能承担“绝对不能发生”的保证。不可逆操作要有确认、撤销或人工对账路径。

## 怎么测

建立攻击与误用集，覆盖：间接提示注入、越租户读取、工具参数越权、系统提示泄露、敏感信息外传、恶意 Skill 和无限循环。每条都检查：

- 是否被代码守卫拦住；
- 是否留下足够的审计事件；
- 是否能恢复正常用户任务；
- 更新模型或工具 schema 后是否仍然成立。

安全评测要按身份、租户和工具风险切片，不能只跑一组通用越狱问题。

## 参考实现与延伸

参考实现的租户绑定、工具守卫、确认和安全测试在 [M5 Production](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m5-production)（核对日期 2026-09-10）。威胁类别可对照 [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/)（访问日期 2026-09-10）。

---

[← 上一课 21](../reliability-cost-llmops/README.md) · [下一课 23 →](../model-adaptation-finetuning-inference/README.md)
