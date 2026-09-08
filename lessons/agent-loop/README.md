---
status: complete
structure: narrative
part: Part 2 Tool 与 Agent
estimated_time: 约 1.5 小时
---

# 06 Agent 循环与控制流

> Agent 就是一个循环：模型决定下一步，运行时执行，把结果放回去，再问模型。这一课讲这个循环里哪些事归模型、哪些事归运行时，尤其是「什么时候停」——那件事模型做不了。

## 用户反复说「不聊了」，它还在找话说

一个语音机器人项目早期把「什么时候结束对话」整个交给了模型：提示词里写着「用户说再见时结束」，然后指望它聊完自己停。

模型不会故意不停。它的倾向是一直找话说：用户说「不聊了」，它答应一声，紧接着又起了个新话题。用户要反复说好几遍才能真的结束一次对话。

提示词那一行为什么不管用，看运行时这一侧就明白了。它压根没有「结束」这个概念——每一轮它只看到模型又生成了一段文本，于是又播了出去。「该不该结束」这个判断只存在于模型的输出里，没有任何代码在接它。

修法是加一个显式的退出工具。模型判断用户想结束时调用它，运行时收到这个调用就静默终止本轮会话。模型仍然负责判断，但停不停由代码决定，而这比把提示词写得更严稳定得多。

这就是这一课的全部内容：给模型一个表达「我想停」的结构化出口，然后把「停」这个动作握在自己手里。下面那张图里，只有一个菱形归模型。

## 学习目标

- 能说清循环里每一步是模型的责任还是运行时的责任
- 能设计步数、token、时间三种预算，并让循环停止时报告是哪一种耗尽了
- 能给工具失败分类，并为每一类指定一种确定性的恢复动作

## 前置

- [05 Tool Calling](../tool-calling/README.md)：工具契约和四个守卫，本课的循环建立在它们之上

## 循环里只有一个菱形归模型

```mermaid
flowchart LR
    classDef model stroke:#7c6ee6,stroke-width:2.2px
    classDef runtime stroke:#0d806b,stroke-width:2px
    classDef data stroke:#4e83a3,stroke-width:1.8px
    classDef human stroke:#b88428,stroke-width:2px
    classDef risk stroke:#b5472d,stroke-width:2px
    G([目标]) --> D{模型：下一步？}
    D -- 工具调用 --> A[运行时：执行工具]
    A --> O[(结果追加到消息)]
    O --> B{运行时：预算还够？<br/>是否跑偏？}
    B -- 够 --> D
    B -- 不够 --> S1([停止：报告原因])
    D -- 直接回答 --> S2([停止：完成])
    D -- 需要人 --> S3([跳出：等待人工])
    class D model
    class A,B runtime
    class O data
    class S3 human
    class S1 risk
    class S2 runtime
```

那个菱形问的是「下一步做什么」。其余全归运行时：执行、记账、判断该不该继续、决定怎么处理失败。这条边界画清楚之后，Agent 的可靠性就是普通软件的可靠性问题了。

这个「模型想一步、运行时做一步、结果再回给模型」的形状有个名字：**ReAct**。它出自 2022 年的同名论文（见延伸阅读），今天几乎所有 Agent 框架的默认循环都是它的变体。知道这个名字，读别家文档时能一眼认出自己在看什么。

### 停止条件全部由运行时持有

模型「自然停下」是一种停止方式，但不能是唯一的。至少还要有步数上限、token 预算、时间预算，以及跑偏检测。

开头那个案例里连「自然停下」都不成立：模型的倾向是接着聊，所以那条路径根本不会走到。退出工具补上的是一条**模型能主动走、但由运行时执行**的停止路径，它和上面那几条预算是并列关系，不是替代关系。

每种停止都要有名字，让用户和日志知道为什么停的。

### 失败要分类，恢复要确定

网络抖动重试就行；参数错了回给模型让它改；模型反复调同一个工具，再问它一次只会得到同样的结果，应该警告一次然后升级给人。三种情况用同一招「再问模型」，结果是烧钱、绕圈、然后超时。

### 一个 Agent 管 3～10 步

上下文越长模型越容易跑偏，这是 12-factor 的 factor 10 反复强调的经验。任务大就拆成多个小 Agent，让确定性代码把它们串起来。这一点第 09 课和第 11 课展开。

拆不开的长任务还有另一条路：循环不动，给它一份每轮重新念一遍的清单，再逐项验收。第 10 课讲这条路，以及两条路各自适合什么。

还有一条来自 factor 08 的观察：循环不一定要一口气跑完。模型请求「问用户一个问题」或「部署到生产」时，正确做法是跳出循环，把状态存下来，等人回来再续。本课的循环还是单进程内的，怎么跨请求暂停和恢复是第 07 课的内容。

## 循环、预算、失败路由

三段代码是一层层加上去的：先让循环能跑起来，再让它一定停得下来，最后决定停不下来的时候怎么办。
只为说明机制，省略了适配器、日志和类型定义，不能直接运行。标题写的是[参考实现](#参考实现)里对应的模块，方便对照着读。

### 一、循环本身很短

```python title="runtime/loop.py" hl_lines="14"
async def run_agent(model, goal, tools, max_steps):
    messages = [Message(role="user", content=goal)]

    for step in range(1, max_steps + 1):
        reply = await model.complete(messages, tools=tools)

        if not reply.tool_calls:      # (1)!
            return Result(stop_reason=FINISHED, answer=reply.content)

        messages.append(Message(role="assistant", tool_calls=reply.tool_calls))
        for call in reply.tool_calls:
            messages.append(run_tool(call))     # (2)!

    return Result(stop_reason=STEP_LIMIT)
```

1.  模型不再要工具，只说明它认为任务做完了。结束循环的是这个 `return`，不是模型。
2.  模型只提出调用请求，执行永远在运行时这一侧。

十几行。复杂度不在循环本身，在循环外面的预算和路由。注意最后那个 `return`：走到它说明模型一直在要工具，运行时替它踩了刹车。它是整段代码里最重要的一行，因为它是唯一保证进程能结束的东西。

开头那个退出工具装进来就是多一个分支：`run_tool` 认出这个工具名，不执行任何副作用，直接让 `run_agent` 带着 `stop_reason=USER_ENDED` 返回。它和 `STEP_LIMIT` 一样是运行时的一条停止路径，只是触发它的信号来自模型。

### 二、预算要在每轮结算之后检查

```python title="runtime/budget.py"
@dataclass
class Budget:
    max_steps: int
    max_tokens: int
    max_seconds: float
    steps: int = 0
    tokens: int = 0
    started: float = 0.0

    def charge(self, tokens: int) -> StopReason | None:
        """记一轮账，返回第一个耗尽的预算；都没耗尽返回 None。"""
        self.steps += 1
        self.tokens += tokens
        if self.tokens > self.max_tokens:
            return StopReason.TOKEN_BUDGET
        if time.monotonic() - self.started > self.max_seconds:
            return StopReason.TIME_BUDGET
        if self.steps >= self.max_steps:
            return StopReason.STEP_LIMIT
        return None
```

循环里的用法是：模型返回后先 `charge(输入 token + 输出 token)`，拿到非 `None` 就带着这个原因停下。三种预算共用一个返回值，调用方不需要写三个 `if`。

`tokens` 要算输入加输出。只算输出是常见错误——历史随着轮次增长，输入才是主要开销。

### 三、失败分类决定恢复动作

```python title="runtime/errors.py"
ROUTES = {
    Failure.TRANSIENT:     Route.RETRY,      # 网络抖动、限流、超时
    Failure.INVALID_INPUT: Route.FEEDBACK,   # 参数错了，模型能自己改
    Failure.OFF_TRACK:     Route.ESCALATE,   # 重复同一个调用，再问也没用
}

async def execute(call, tool, max_retries=2):
    for attempt in range(1, max_retries + 2):
        try:
            return ok(call, tool(call.arguments))
        except TransientError:
            await asyncio.sleep(0.05 * attempt)   # RETRY：退避后重来
        except ValueError as exc:
            return error(call, str(exc))          # FEEDBACK：把错误回喂给模型
    return error(call, "tool unavailable after retries")
```

跑偏检测放在循环里，不放在 `execute` 里，因为它要看的是跨轮次的历史：

```python
sig = f"{call.name}:{json.dumps(call.arguments, sort_keys=True)}"
if sig in seen:
    if warned:
        return "needs_human"          # 警告过一次还重复，升级给人
    warned = True
    messages.append(error(call, "你已经用同样的参数调过它了，换个做法"))
else:
    seen.add(sig)
    messages.append(await execute(call, tool))
```

签名用「工具名 + 规范化参数」。只看工具名会误判：一个正常的「读三个文件」任务会被当成死循环。

## 常见错误

**`while True` 加一个「模型总会停」的假设。** 真实模型不会故意不停，但会因为工具结果里的某句话进入循环——比如工具返回「请重试」。没有 `max_steps`，这个进程会一直跑到 API 额度耗尽。

**把「什么时候停」写在提示词里，没有对应的代码分支。** 就是开头那个案例。提示词里的停止条件是一句建议，运行时那边得真的有一条路径在接它。

**预算只在进入循环时检查一次。** 一轮里模型返回一个超长回答就直接突破预算。检查必须在每轮结算之后。

**把所有异常都 catch 成「工具失败，重试」。** 参数错误重试一百次结果一样；瞬时错误回给模型让它「修参数」，是让它修一个不存在的问题。异常类型不同，恢复路径就该不同。

**跑偏检测太敏感。** 只看工具名、或者用一个永不过期的 `set` 记全部历史，都会把合法的重复查询判成死循环。

## 上限设多少，重试的代价谁付

- **步数上限设多少。** 太小任务做不完，太大失控成本高。经验值按任务类型分档：查询类 3～5，多工具协作 8～12，超过 15 步的任务应该拆。上限是安全网，不是目标。开头那个项目里还有一层：任务型 Agent 的上限要比聊天型小得多，因为每一步都伴随一次设备动作，跑偏的代价是物理的。
- **重试的代价谁付。** 重试是拿延迟换成功率。给用户的实时对话里，一次重试可能就超出可接受的等待时间；后台任务则可以多重试几次。所以重试次数要做成循环的参数，不要写成常量。
- **升级给人，还是直接放弃。** 升级需要有人接，有人接就要有第 07 课的暂停机制。没有这个机制时，诚实的「我做不到」比假装完成好，也比无限等待好。

## 从十几行到能上线

- **每一次停止都要落一条结构化事件**，带上停止原因和当时的预算快照。事后排查「这次为什么只跑了两步」，靠的是这条记录，不是日志里的一句话。
- **停止原因要够细。** `FINISHED`、`STEP_LIMIT`、`TOKEN_BUDGET`、`TIME_BUDGET`、`USER_ENDED`、`NEEDS_HUMAN` 是六种不同的结局，混成一个「结束了」就没法按原因统计。第 20 课那棵 trace 树上，根 span 的 `stop_reason` 就是这个字段。
- **预算要分层**：单次运行有预算，单个用户每天有预算，整个服务每月有预算。只做最里面那层，一个死循环的用户就能把整月账单打穿。
- **重试要带上幂等键**，否则「瞬时错误」的重试会把已经生效的副作用做第二遍。这是第 05 课工具契约的延续。
- **跑偏检测的窗口要可配**，不同任务类型的合理重复度差很多。
- **怎么测。** 每次运行记下停止原因和走了几步，按版本统计分布。改提示词或换模型之后，「平均步数从 3 涨到 7」「预算耗尽的比例从 2% 涨到 15%」这类退化只有这两个数字看得见——最终回答往往还是对的。开头那个案例的回归断言也在这里：给一段「用户说不聊了」的对话，断言 `stop_reason` 是 `USER_ENDED` 而不是 `STEP_LIMIT`。

## 框架映射

| 本课概念 | LangGraph | OpenAI Agents SDK | Claude Agent SDK |
|---|---|---|---|
| 循环本身 | 图的 conditional edges | `Runner` | SDK 内部托管 |
| 步数上限 | `recursion_limit` | `max_turns` | `max_turns` |
| 停止原因 | 自己在 state 里记 | `RunResult` | 结果消息的 `subtype` |
| 失败路由 | 自己写节点 | 自己写 | 自己写 |

三个框架都不替你做失败分类和预算记账，这部分永远是你自己的代码。官方文档：[LangGraph](https://langchain-ai.github.io/langgraph/) · [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) · [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk/overview)（核对日期 2026-09-05）。

## 参考实现

循环是 [`runtime/loop.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/loop.py) 的 `run_agent()`，步数、token 和时间三种预算在 [`budget.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/budget.py)，失败怎么分类和路由在 [`errors.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/errors.py)。停止条件和跑偏检测的用例在 [`m3/test_loop.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/tests/project/m3/test_loop.py)，装配见 [M3 Tool Workflow](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/m3-tool-workflow/README.md)。

## 延伸阅读

- [12-factor-agents · factor 08 Own your control flow](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-08-own-your-control-flow.md)（访问日期 2026-09-04）：三种控制流形态的代码示例，「跳出循环等人」就出自这里。
- [12-factor-agents · factor 10 Small, focused agents](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-10-small-focused-agents.md)（访问日期 2026-09-04）：为什么一个 Agent 管 3～10 步，以及「模型变强了这条还成立吗」的回答。
- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)（访问日期 2026-09-08）：本课这个循环的原始论文，读摘要和图 1 就够。
- [Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)（访问日期 2026-09-05）：循环与工作流的边界，第 09 课会详细展开。

---

[← 上一课 05](../tool-calling/README.md) · [下一课 07 →](../agent-state-and-runtime/README.md)
