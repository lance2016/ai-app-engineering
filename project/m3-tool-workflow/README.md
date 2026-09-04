---
status: draft
kind: impl
depends_on: lessons/05, 06, 07, 08, 09, 11, 12；可选 10
---

# M3 Tool Workflow

> 把第 05 课的四个守卫、第 06 课的循环与预算、第 07 课的暂停恢复合成一个 `ToolRunner`，接到 M2 的存储上。然后从外部接入能力：一个只读 MCP Server 和一个 Skill。这一步做完，服务就是一个能干活、能停、能续的 Agent。

## 这一步加什么

分四个子阶段，每个子阶段独立可验收：

- **M3.1 Tool contract**：`ToolRegistry`（第 05 课 `02`），Pydantic schema 校验，请求级白名单，工具结果统一为 `Message(role="tool", is_error=...)`；最小 trace，每次工具执行记一条带耗时的事件
- **M3.2 确认与幂等**：有副作用的工具走 `request_human_input` 暂停（第 07 课），幂等键从 `ToolCall` 派生并经 M2 的 `IdempotencyStore` 认领；失败路由（第 06 课 `03`）：瞬时重试、参数回喂、跑偏升级
- **M3.3 MCP 与 Skill**：`MCPToolSource` 把一个 MCP Server 的 `tools/list` 结果注册进 `ToolRegistry`，先接只读 Server（文件系统只读或文档搜索）；`SkillLoader` 读 `skills/<name>/SKILL.md`，按第 08 课的按需加载策略把说明注入上下文
- **M3.4（可选）Handoff**：把 workflow 拆成 router Agent 和 worker Agent，交接时只传摘要，对应第 10 课

目标目录：

```text
project/src/aiapp/runtime/
├── registry.py     # ToolRegistry, Tool, allowlist
├── runner.py       # ToolRunner.run(call, ctx) -> Message；校验、权限、确认、幂等、重试、trace
├── loop.py         # run_agent(thread, model, runner, budget) -> StopReason；含 pending 处理与暂停
├── budget.py       # Budget（步数 / token / 时间）
├── context.py      # build_messages(thread, skills) —— 第 08 课的上下文组装
├── mcp_source.py   # MCPToolSource(server_url).register_into(registry)
└── skills.py       # SkillLoader(root).available(), load(name)
skills/
└── expense-report/SKILL.md
```

关键接口：

```python
class ToolRunner:
    async def run(self, call: ToolCall, ctx: RunContext) -> Message:
        """validate -> authorize -> (pause if side effect and not confirmed) -> execute with idempotency key -> record."""

async def run_agent(thread: Thread, model: ModelAdapter, runner: ToolRunner, budget: Budget) -> StopReason: ...

@dataclass
class RunContext:
    tenant_id: str
    allowlist: frozenset[str]
    confirmed_call_ids: frozenset[str]
```

## 运行步骤

```bash
docker compose up -d postgres redis
uv run uvicorn aiapp.api.app:create_app --factory
# 发一条会触发工具的消息，观察 SSE 里的 tool_call / tool_result 事件
# 发一条会触发有副作用工具的消息，观察 human_input_requested 事件，再用确认端点恢复
uv run pytest tests/runtime
```

## 验收证据

- [ ] `tests/runtime` 覆盖：未知工具、非法参数、白名单外、需确认、幂等重放、瞬时错误重试、跑偏升级，七种路径各至少一个测试
- [ ] 工具准确率测试：一组 20 条"用户说 X 应该调用 Y"的用例用 fake adapter 跑通；换成真实模型后记录准确率作为基线
- [ ] 失败注入：在工具执行后、记录结果前杀进程，恢复后同一幂等键不产生第二次副作用
- [ ] MCP Server 断开时，工具调用返回 `is_error` 结果而不是 500，模型能换别的办法
- [ ] Skill 只在触发条件满足时被加载，trace 里能看到加载事件和注入的 token 数
- [ ] 每一步都有 trace 事件，能从事件线程重建"这次运行调了哪些工具、各花了多久"

## 依赖的课程

lessons/05, 06, 07, 08, 09, 11, 12；可选 10

---

[← 项目总览](../README.md)
