# 06 Agent 循环与控制流｜练习

## 练习 1：显式的退出工具

给 `01_minimal_loop.py` 加一个 `finish` 工具，参数是 `summary: str`。模型调用它时循环以 `StopReason.FINISHED` 结束，`answer` 取 `summary`。剧本改成最后一步调用 `finish` 而不是直接回答。

验收：输出 `stop_reason=finished`，`answer` 来自工具参数而不是 `reply.content`。

<details><summary>答案与讨论</summary>

在 `run_agent` 的工具循环里加一个分支：`if call.name == "finish": return RunResult(StopReason.FINISHED, answer=call.arguments["summary"], ...)`。

为什么要这样做：有些模型在工具模式下不太愿意"直接回答"，会一直找工具用。给它一个结构化的"我做完了"出口，比等它自然停下可靠。语音机器人项目的退出工具就是这个思路。

</details>

## 练习 2：让时间预算真正生效

`02_budgets.py` 的时间预算是在每轮结束后检查的。如果一次模型调用本身就卡了 30 秒，这一轮结束前谁也拦不住。用 `asyncio.wait_for` 给单次 `model.complete` 加超时，超时后以 `StopReason.TIME_BUDGET` 结束。

验收：`INJECT_SLOW_MODEL=1` 时，把 `max_seconds` 改成 0.1，运行应在第一轮就停止，而不是等慢模型返回。

<details><summary>答案</summary>

```python
remaining = budget.max_seconds - (time.monotonic() - budget.started)
try:
    reply = await asyncio.wait_for(model.complete(messages, tools=[SEARCH]), timeout=max(remaining, 0.01))
except TimeoutError:
    return StopReason.TIME_BUDGET, ""
```

注意 `remaining` 要每轮重新算。这也是第 07 课的一个伏笔：被 `wait_for` 取消的那次调用，如果已经在服务端产生了费用或副作用，运行时是不知道的。

</details>

## 练习 3：跑偏检测的窗口

`03_failure_routing.py` 用一个 `set` 记住所有出现过的调用签名。这意味着一个合法的"每小时查一次订单状态"的长任务，第二次查询就会被当成重复。把检测改成只看**最近 N 步**（比如 3 步）内是否重复。

验收：剧本里放入 `lookup o_1 → lookup o_2 → lookup o_3 → lookup o_1`，不应触发警告；`lookup o_1 → lookup o_1` 应触发。

<details><summary>答案</summary>

用 `collections.deque(maxlen=3)` 代替 `set`，判断 `sig in recent`。窗口大小是一个需要按任务调的参数，没有通用值。

</details>

## 练习 4：为什么是 3～10 步

不写代码。用你自己的话解释：为什么 12-factor 建议一个 Agent 管 3～10 步，而不是相信模型能处理 50 步？如果模型能力提升了，这条建议还成立吗？

<details><summary>参考答案</summary>

步数多意味着上下文长，上下文长模型更容易丢失焦点或被中间某个工具结果带偏。而且步数多的任务，中间任何一步出错都会污染后续所有步骤，调试时也很难定位。

模型变强会让这个边界外移，但边界始终存在。小而专的 Agent 让你今天就能拿到稳定的结果，等模型变强了再逐步扩大每个 Agent 的范围。这和重构大型确定性代码的经验是一样的：先拆小，再按需合并。

</details>

## 练习 5：读一段记录，判断哪个停止条件该先触发

```text
step 1: search({"q": "flight to Tokyo"})   tokens so far 900
step 2: search({"q": "flight to Tokyo"})   tokens so far 1900
step 3: search({"q": "flight to Tokyo"})   tokens so far 2900
step 4: search({"q": "flight to Tokyo"})   tokens so far 3900
stop_reason=token_budget
```

这次运行以 token 预算耗尽结束。它本来应该在哪一步、以什么理由结束？

<details><summary>答案</summary>

第 2 步就应该以跑偏检测结束，或者至少发出警告。四次完全相同的调用是明确的循环信号，等到 token 预算耗尽才停，浪费了三轮的钱。

这说明停止条件有优先级：跑偏检测应该比预算更早触发，因为它是"这条路走不通"的信号，预算只是"钱花完了"的兜底。运行时应该同时装着这几种条件，而不是只靠最后那一道。

</details>
