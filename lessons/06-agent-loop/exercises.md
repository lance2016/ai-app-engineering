# 06 Agent 循环与控制流｜练习

## 练习 1：显式的退出工具

给正文那个最小循环加一个 `finish` 工具，参数是 `summary: str`。模型调用它时，循环以 `FINISHED` 结束，答案取 `summary`，而不是取模型的自由文本。写出这个分支该插在循环的哪一行、为什么。

<details><summary>答案与讨论</summary>

插在工具执行之前：

```python
for call in reply.tool_calls:
    if call.name == "finish":
        return Result(stop_reason=FINISHED, answer=call.arguments["summary"])
    messages.append(run_tool(call))
```

为什么要这样做：有些模型在工具模式下不太愿意「直接回答」，会一直找工具用。给它一个结构化的「我做完了」出口，比等它自然停下可靠。语音机器人项目的退出工具就是这个思路。

注意 `finish` 不走 `run_tool`——它不是工具，是一个借工具协议表达的控制信号。

</details>

## 练习 2：让时间预算真正生效

正文的 `Budget.charge` 是在每轮结束后检查的。如果一次模型调用本身就卡了 30 秒，这一轮结束前谁也拦不住。怎么改？

<details><summary>答案</summary>

给单次模型调用套一个超时，超时时间是预算的剩余量：

```python
remaining = budget.max_seconds - (time.monotonic() - budget.started)
try:
    reply = await asyncio.wait_for(model.complete(messages, tools=tools),
                                   timeout=max(remaining, 0.01))
except TimeoutError:
    return Result(stop_reason=TIME_BUDGET)
```

`remaining` 要每轮重新算。

这也是第 07 课的一个伏笔：被超时取消的那次调用，如果已经在服务端产生了费用或副作用，运行时是不知道的。取消一个请求不等于它没发生。

</details>

## 练习 3：跑偏检测的窗口

正文用一个 `set` 记住所有出现过的调用签名。这意味着一个合法的「每小时查一次订单状态」的长任务，第二次查询就会被当成重复。把检测改成只看最近 N 步。

验收标准：`lookup o_1 → lookup o_2 → lookup o_3 → lookup o_1` 不该触发警告；`lookup o_1 → lookup o_1` 该触发。

<details><summary>答案</summary>

用 `collections.deque(maxlen=3)` 代替 `set`，判断 `sig in recent`。

窗口大小是一个需要按任务调的参数，没有通用值。查询密集的任务窗口要小，长流程任务窗口要大。

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

第 2 步就应该以跑偏检测结束，或者至少发出警告。四次完全相同的调用是明确的循环信号，等到 token 预算耗尽才停，白烧了三轮的钱。

这说明停止条件有优先级：跑偏检测应该比预算更早触发，因为它是「这条路走不通」的信号，预算只是「钱花完了」的兜底。运行时应该同时装着这几种条件，而不是只靠最后那一道。

</details>
