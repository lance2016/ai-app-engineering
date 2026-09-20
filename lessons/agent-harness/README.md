---
status: complete
structure: narrative
part: Part 2 Tool 与 Agent
topic: capability-ecosystem
tier: deep-dive
estimated_time: 约 30 分钟
---

# 14 Agent Harness：把 Tool 与 Agent 零件装进一个真实系统

> Coding Agent 的核心不是“会写代码”，而是一个受权限、工作区、检查点和验收约束的运行时。

<details class="case" markdown="1">
<summary>例子：模型生成了看似正确的补丁，却覆盖了用户未要求修改的文件</summary>

如果编辑工具只提供“重写整个文件”，模型的一个误判就会扩大影响。Harness 要把修改范围、命令权限、确认门和测试结果都变成显式边界。

!!! note "构造的例子"
    补丁事故用于说明 Harness 的权限和验收职责；工具实现随宿主环境变化。

</details>

## Harness 负责四件事

| 责任 | 例子 |
|---|---|
| 工具界面 | 读文件、精确替换、运行命令 |
| 权限 | 哪些目录可写、哪些命令需确认 |
| 循环控制 | 步数、超时、取消、恢复 |
| 验收 | 测试、diff、格式和用户确认 |

模型提出修改建议，Harness 决定是否执行。命令返回 0 也不等于任务完成，还要检查产物和用户目标。

## 编辑工具要让错误变小

优先提供“替换唯一片段”“新增文件”“显示 diff”等可定位操作，而不是让模型整文件重写。每次修改前后保存 diff，失败时可以恢复。

## 怎么测

给 Harness 一组真实任务，加入：文件不存在、匹配不唯一、测试失败、命令超时、权限拒绝和中途取消。检查：

- 未授权命令是否执行；
- 补丁是否只影响目标范围；
- 测试失败后是否停止而不是强行报告完成；
- 恢复后是否能识别已经发生的修改。

## 参考实现与延伸

参考项目把工具、权限和验收场景放在 [Capstones](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/capstones) 和 [Framework Lab](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/framework-lab)（核对日期 2026-09-10）。可对照 [OpenAI Codex security](https://openai.com/index/codex-security/)（访问日期 2026-09-10）思考执行边界。

---

[← 上一课 13](../skills-and-capability-layers/README.md) · [下一课 15 →](../rag-end-to-end/README.md)
