---
status: complete
part: Part 5 产品与技术决策
estimated_time: 约 2 小时
---

# 23 AI 产品设计与交互

> 前面二十一课在让 Agent 可靠。这一课问的是另一件事：用户凭什么相信它、什么时候该把决定权还给用户、怎么知道产品有没有变好。答案大多不在模型里，在交互设计和反馈闭环里。

## 为什么需要

Agent 的不确定性如果没有映射成清楚的界面状态，用户只会看到卡住、误执行或断线丢字。产品体验要把控制权和反馈做成系统状态。

## 学习目标

- 能用人工基线和 ROI 判断一个功能该不该上 AI，并说出三种「不该用」的信号
- 能把流式回答建模成显式的 UI 状态机，说清每个状态用户能做什么、看到什么
- 能按可逆性给动作分级，正确选择确认、撤销窗口或直接执行
- 能设计带原因码和切片的反馈闭环

## 前置

- [05 Tool Calling](../05-tool-calling/README.md)：确认门。本课的「撤销窗口」是它的另一半
- [07 Agent State 与 Runtime](../07-agent-state-and-runtime/README.md)：事件流。本课 UI 状态机消费的就是那份事件

## 心智模型

```mermaid
flowchart LR
    Q[该不该用 AI？] -->|人工基线 / ROI| D[设计交互]
    D --> S[状态机：用户此刻能做什么]
    D --> C[控制权：确认 / 撤销 / 转人工]
    D --> E[解释：引用与来源]
    S & C & E --> F[反馈闭环：信号 + 原因 + 切片]
    F -->|指标| Q
```

**先问要不要。** 人工基线是「现在人怎么做、多久、错多少」。AI 方案只有在成本或质量上明显好于这条线、且失败后果可承受时才值得做。三个「不该用」的信号：

1. 任务有唯一正确答案且已有确定性方案
2. 错误不可逆且无法验证
3. 用户需要的是速度而不是判断

**流式回答是一个状态机。** 等待、流式输出、工具执行中、需要确认、完成、失败，每个状态的渲染和可用操作都不同。

```mermaid
stateDiagram-v2
    waiting: 等待
    streaming: 流式输出
    tooling: 工具执行中
    confirming: 需要确认
    done: 完成
    failed: 失败
    cancelled: 已取消

    [*] --> waiting
    waiting --> streaming: 首块到达
    streaming --> tooling: 模型要调工具
    tooling --> streaming: 结果回填
    tooling --> confirming: 动作不可逆
    confirming --> tooling: 用户批准
    confirming --> cancelled: 用户拒绝
    streaming --> done
    waiting --> failed: 超时
    tooling --> failed: 工具失败 / 预算耗尽
    failed --> waiting: 重试
    done --> [*]
    cancelled --> [*]
```

每个状态要回答同一个问题：用户此刻看到什么、能点什么。

**控制权按可逆性分级。** 分级由运行时按动作的**声明**决定，不由模型判断。这和第 05 课确认门是同一条原则的两面。

**反馈要能定位问题。** 一个总体的「点赞率 85%」什么都说明不了。

## 机制拆解

### 一、UI 状态机：先写转移表

```python
class UIState(StrEnum):
    IDLE               = "idle"
    WAITING            = "waiting"              # 请求发出，还没回 -> 转圈，可取消
    STREAMING          = "streaming"            # 文本在来 -> 追加，可停止
    TOOL_RUNNING       = "tool_running"         # 在用工具 -> 说明用哪个，之前的文字保持可见
    NEEDS_CONFIRMATION = "needs_confirmation"   # 副作用待批 -> 显示批准 / 拒绝
    DONE               = "done"
    FAILED             = "failed"

TRANSITIONS: dict[UIState, set[UIState]] = {
    UIState.IDLE:      {UIState.WAITING},
    UIState.WAITING:   {UIState.STREAMING, UIState.TOOL_RUNNING,
                        UIState.NEEDS_CONFIRMATION, UIState.DONE, UIState.FAILED},
    UIState.STREAMING: {UIState.STREAMING,       # ← 自转移，这就是增量文本
                        UIState.TOOL_RUNNING, UIState.NEEDS_CONFIRMATION,
                        UIState.DONE, UIState.FAILED},
    UIState.TOOL_RUNNING:       {UIState.STREAMING, UIState.NEEDS_CONFIRMATION,
                                 UIState.DONE, UIState.FAILED},
    UIState.NEEDS_CONFIRMATION: {UIState.TOOL_RUNNING, UIState.STREAMING,
                                 UIState.DONE, UIState.FAILED},
    UIState.DONE:   {UIState.WAITING},           # 只能由用户发起下一轮
    UIState.FAILED: {UIState.WAITING},
}
```

**先写表，再写渲染。** 「工具跑了十秒界面卡住」和「断线后文字全没了」这类问题会在转移表上暴露出来，而不是在用户投诉里。想加一个「用户打断」状态？先改表。

视图对象是一个 reducer 的产物，关键是 `text` 独立于 `state`：

```python
@dataclass
class ReplyView:
    state: UIState = UIState.IDLE
    text: str = ""                   # ← 不随状态清空
    tool_label: str = ""
    pending_action: str = ""
    error: str = ""
    citations: list[str] = field(default_factory=list)

    def go(self, new: UIState) -> None:
        if new not in TRANSITIONS[self.state]:
            raise RuntimeError(f"非法状态转移 {self.state} -> {new}")
        self.state = new
```

渲染每个状态的头部，正文永远是 `self.text`：

```python
head = {
    UIState.WAITING:      "[ 思考中...            (取消) ]",
    UIState.STREAMING:    "[ 回答中...            (停止) ]",
    UIState.TOOL_RUNNING: f"[ 正在使用 {self.tool_label}...  (取消) ]",
    UIState.NEEDS_CONFIRMATION: f"[ 确认执行 {self.pending_action}？ (批准) (拒绝) ]",
    UIState.FAILED:       f"[ 失败：{self.error} ] (重试) —— 以下是已生成的部分",
}[self.state]
return f"{head}\n  {self.text or '(还没有内容)'}"
```

断线时进入 `FAILED`，但 `text` 保留，界面明确说「以下是部分回答」。**不要用一个不断变长的字符串代表回答**——断线时它被清空重来，用户看到已经出现的文字消失了，这比什么都没有更让人困惑。

### 二、撤销窗口：可逆动作不必确认

```python
@dataclass(frozen=True)
class Action:
    name: str
    reversible: bool          # ← 运行时按这个字段选路径，不问模型
    undo_name: str = ""

UNDO_WINDOW_S = 5.0

async def perform(action: Action, approve_fn) -> Outcome:
    if action.reversible:
        do(action)                                  # 先做
        show(f"{action.name} 完成。[撤销] 可用 {UNDO_WINDOW_S:.0f} 秒")
        try:
            await asyncio.wait_for(user_pressed_undo(), timeout=UNDO_WINDOW_S)
        except TimeoutError:
            return Outcome(action, committed=True)  # 窗口过了，真正提交
        do(action.undo_name)
        return Outcome(action, committed=False)

    # 不可逆：先问
    if not await approve_fn(action):
        return Outcome(action, committed=False, note="用户拒绝")
    do(action)
    return Outcome(action, committed=True)
```

**确认是稀缺资源。** 每个动作都弹确认，用户很快学会无脑点确定，确认就失效了。归档对话直接做加撤销窗口；支付必须确认。

有外部副作用的动作（发邮件）**窗口结束前根本不该发出去**——这要求后端支持延迟提交，不是前端假装等一下。

### 三、反馈：信号 + 原因码 + 切片键

```python
class Signal(StrEnum):
    ACCEPT   = "accept"      # 原样用了
    EDIT     = "edit"        # 改了再用
    REJECT   = "reject"      # 点踩 / 重新生成
    ESCALATE = "escalate"    # 转人工

class Reason(StrEnum):
    WRONG_FACT    = "wrong_fact"
    TOO_LONG      = "too_long"
    MISSED_INTENT = "missed_intent"
    UNSAFE_ACTION = "unsafe_action"

@dataclass(frozen=True)
class Feedback:
    thread_id: str
    event_index: int      # 指向具体哪条 assistant_message
    intent: str           # 切片键，由运行时的路由填
    signal: Signal
    reason: Reason | None = None
```

三个字段各有用处：

- **`event_index`** 让反馈挂在**具体的一次回答**上，能回溯到那次的 trace 和检索结果。
- **`reason`** 让负反馈可归因。「不好」没法改，「事实错误」能改。
- **`intent`** 让你能切片。

切片有多重要，看这张表：

| slice | n | accept | edit | reject | escalate | 主要原因 |
|---|---:|---:|---:|---:|---:|---|
| **ALL** | 88 | **75%** | 6% | 9% | 10% | |
| faq | 45 | 89% | 11% | 0% | 0% | too_long |
| order_status | 23 | 87% | 0% | 13% | 0% | wrong_fact |
| **refund** | 20 | **30%** | 0% | 25% | **45%** | unsafe_action |

总体 75% 的接受率看着还行。`refund` 场景 45% 在转人工——**这是产品的一个洞，被总体数字盖住了**。

### 四、引用要能点开

引用列表放在回答末尾、点不开、和正文没有对应关系，等于没有。引用要能回到原文的具体位置——第 14 课讲了怎么在检索层保留 `chunk_id` 和位置信息，本课只是把它带到界面：

```python
citations: list[str]     # ["refund-policy#0", "shipping#2"]
```

界面上每条引用是可点的，点开显示那个 chunk 的原文和它在文档里的位置。用户要能**验证**，不只是被告知有来源。

## 常见错误

**用一个不断变长的字符串代表回答。** 见第一节。

**每个动作都弹确认。** 见第二节。

**引用做成装饰。** 见第四节。

**只收点赞点踩。** 没有原因码，负反馈无法归因；没有切片键，看不出哪个场景在坏。

## 取舍

- **透明 vs 简洁。** 显示模型正在用什么工具、引用来自哪里，会增加界面噪音。原则是**默认折叠、可展开，关键动作前展开**。
- **撤销窗口的长度。** 太短用户来不及反应，太长动作迟迟不生效。多数界面用 5～10 秒。
- **转人工的时机。** 早转浪费人力，晚转用户已经生气。信号可以是连续两次负反馈、用户重复同一个问题、或者模型自己请求（第 07 课的 `request_human_input`）。把阈值做成配置，按场景调。

## 工程落地

- **状态机的定义前后端共享。** 后端事件类型和前端状态一一对应，加状态时两边同步改。定义分叉是这类 bug 的主要来源。
- **反馈要能反查 trace。** 用户点踩的那一刻，你要能拿到那次运行的完整 trace 和检索结果，否则改不了。
- **「部分完成」要有明确表达。** Agent 做了三步中的两步就失败了，界面要说清哪两步做了、哪一步没做。「失败」两个字会让用户不知道要不要重来。
- **A/B 的粒度是场景，不是全局。** 新提示词在 faq 上更好、在 refund 上更差是常态。按切片看，不按总体看。

## 框架映射

| 本课概念 | LangGraph | OpenAI Agents SDK | Claude Agent SDK |
|---|---|---|---|
| 事件流 → UI 状态 | `astream_events` 的事件类型 | `run_streamed` 的 stream events | 消息流 |
| 审批交互 | `interrupt` 的 payload 驱动 UI | `needs_approval` 的中断 | 权限回调 |

框架给的是事件，**状态机是你自己的**。事件类型到 UI 状态的映射表，是这一层唯一需要认真设计的东西。官方文档：[LangGraph](https://langchain-ai.github.io/langgraph/) · [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) · [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk/overview)（核对日期 2026-09-05）。

## 一线经验

语音场景没有屏幕，**状态机的每个状态都要用声音表达**。等待用一个短音效，工具执行中用一句「我看一下」，需要确认时必须完整复述要做的事。

第一版没有「工具执行中」的反馈，用户以为机器人没听见，反复重复指令，**触发了双重执行**。修法就是给 `TOOL_RUNNING` 状态一个可感知的表达，问题消失。这件事说明状态机不是界面装饰，它直接影响系统的正确性。

另一个和撤销相关的经验：物理动作（移动、播放）几乎都不可逆或代价高，所以语音场景的确认比屏幕场景多得多。但确认的话术要短，否则用户会打断它——**用户打断确认本身又是一个需要处理的状态**。

## 练习

见 [exercises.md](./exercises.md)。

想看这一课的机制装进一个真实服务是什么样：参考实现的 [M6 综合设计](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/m6-platform-design/README.md)（还是草稿），交互与反馈闭环的设计。

## 延伸阅读

- [Google PAIR · People + AI Guidebook](https://pair.withgoogle.com/guidebook)（访问日期 2026-09-04）：按用户需求、心智模型、解释与信任、反馈与控制、错误与优雅失败组织，每章有可直接用的设计模式。
- [Microsoft HAX Toolkit](https://www.microsoft.com/en-us/haxtoolkit/)（访问日期 2026-09-04）：18 条人机交互指南加设计模式库，「make clear what the system can do」和「support efficient correction」两条对应本课的状态机和撤销。
- [generative-ai-for-beginners · 12 Designing UX for AI Applications](https://github.com/microsoft/generative-ai-for-beginners/blob/main/12-designing-ux-for-ai-applications/README.md)（访问日期 2026-09-04）：可用性、可靠性、可访问性、愉悦四个维度，加信任与透明、协作与反馈两节。
- [ai-agents-for-beginners · 06 Building Trustworthy AI Agents](https://github.com/microsoft/ai-agents-for-beginners/blob/main/06-building-trustworthy-agents/README.md)（访问日期 2026-09-04）：系统提示框架、五类威胁与缓解、人工介入。

---

[← 上一课 22](../22-model-adaptation-finetuning-inference/README.md) · [下一课 24 →](../24-voice-agents/README.md)
