# 18 可观测性｜练习

## 练习 1：让关联 id 穿过 create_task

把 `01_structured_logging.py` 里的工具调用改成 `asyncio.create_task(run_tool(...))` 并发执行，`run_id` 不再显式传参，而是放进一个 `contextvars.ContextVar`。

验收：并发执行的工具日志仍然带正确的 `run_id`。然后把工具调用改成 `loop.run_in_executor` 跑在线程池里，观察 `run_id` 是否还在。

<details><summary>答案</summary>

`create_task` 会复制当前 contextvars 上下文，所以子任务里能读到 `run_id`。`run_in_executor` 不会，线程里读到的是默认值。修法是 `contextvars.copy_context().run(fn)` 或者显式把 `run_id` 作为参数传进线程。OpenTelemetry 的 context propagation 处理的就是这个问题。

</details>

## 练习 2：给 tracer 加"记全文"的开关

`02_minimal_tracer.py` 的 chat span 只记 token 数。加一个环境变量 `TRACE_CONTENT=1`，打开时把 `gen_ai.input.messages` 和 `gen_ai.output.messages` 也放进属性。

验收：默认输出里没有消息正文；打开后有。然后回答：为什么这个开关默认应该关。

<details><summary>答案</summary>

三个原因：隐私（用户输入可能含个人信息）、成本（每个 span 大几 KB，后端存储和查询都变慢）、噪声（排障时 90% 的时间不需要全文）。常见做法是按采样率记，或者只对被标记为失败的运行记。

</details>

## 练习 3：用 trace 做循环告警

基于 `03_failure_experiments.py` 的 `loop` 场景，写一个函数 `detect_loops(spans) -> list[str]`，输入一棵 span 树，输出"同一父节点下相同 `aiapp.args_hash` 的 `execute_tool` 子 span 超过 2 个"的父 span 名字。

验收：`loop` 场景返回一个结果，其他四个场景返回空。

<details><summary>提示</summary>

按 `parent_id` 分组，组内按 `(gen_ai.tool.name, aiapp.args_hash)` 计数。这个函数放到 collector 后面就是一条告警规则；放到运行时里就是第 06 课的跑偏检测。同一个逻辑，两个位置。

</details>

## 练习 4：把 04 的 payload 真的发出去

本机装 Phoenix：`pip install arize-phoenix`（建议在另一个虚拟环境里）然后 `phoenix serve`。设 `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:6006` 跑 `04_otlp_export.py`，在 Phoenix 界面里找到 `aiapp-lesson18` 这个服务。

验收：能看到三个 span 的树，`execute_tool search` 显示为错误状态。然后故意把 `status.code` 改成 0，再发一次，看 UI 里那个 span 的颜色变化。

<details><summary>说明</summary>

这题的目的是亲眼看到"状态码决定 UI 颜色"。`code: 2` 是 ERROR，`code: 1` 是 OK，`code: 0` 是 UNSET。第 02 课的 `INJECT_FORGET_STATUS` 对应的就是 UNSET。

</details>

## 练习 5：读一棵树，说出问题在哪一层

```text
invoke_agent support_bot [OK] 4210ms cost_usd=0.031
  chat deepseek-chat [OK] 820ms input_tokens=310 output_tokens=45
  execute_tool search_kb [OK] 95ms
  chat deepseek-chat [OK] 3100ms input_tokens=9800 output_tokens=60
  execute_tool search_kb [OK] 90ms
  chat deepseek-chat [OK] 105ms input_tokens=9900 output_tokens=12
```

用户反馈：回答慢，而且答非所问。结合原则 07 的六层，问题最可能在哪一层？先查什么？

<details><summary>答案</summary>

第二次 chat 的 `input_tokens` 从 310 跳到 9800，说明第一次 `search_kb` 返回了一大块内容进了上下文。这是**上下文层**的问题：检索结果没有裁剪或没有分页就塞进了 prompt，既慢又贵，还可能把用户问题挤到模型注意不到的位置，所以答非所问。

先查 `search_kb` 的返回体大小和第 08 课讲的上下文组装逻辑。不用先怀疑模型，也不用先怀疑检索的相关性：trace 已经把范围缩小到了"结果太大"这一件事。

</details>
