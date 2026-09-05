# 11 MCP｜练习

## 练习 1：加一个 resources/read 的权限边界

假设一个 MCP server 的 `resources/read` 对任何存在的 uri 都放行。给 client 加一个资源白名单（比如只允许 `notes://todo`），在 host 侧拦截对 `notes://ideas` 的读取。

验收标准：读 `notes://ideas` 时得到一条 host 侧的错误，请求根本没发到 server。

<details><summary>答案</summary>

和工具白名单一样，加在 `request("resources/read", ...)` 之前，不要等 server 拒绝。资源和工具在 MCP 里是两类能力，但对 host 来说权限逻辑是一样的：先决定能不能碰，再发请求。

</details>

## 练习 2：分辨两条错误通道

不看代码，判断下面四种情况各走哪条通道，为什么：

1. 模型给 `search_notes` 传了 `{"q": "milk"}`（字段名错了）
2. 模型调用 `search_notes`，server 里搜索时数据库超时
3. host 在 `initialize` 之前发了 `tools/list`
4. 模型调用 `delete_note`，笔记不存在

<details><summary>答案</summary>

1 和 3 是 JSON-RPC `error`：一个是 `-32602` 参数无效，一个是 `-32600` 未初始化。它们说明 host 侧代码有问题（没按 schema 校验就发出去、没等握手完成）。

2 和 4 是 `result.isError = true`：工具正常收到了合法请求，但没能完成。这是模型需要知道的信息。

判断标准：请求本身合法吗？合法但没做成，走 `isError`；请求就不合法，走 `error`。

</details>

## 练习 3：加超时

`client.request()` 在 server 挂起（不退出也不响应）时会永远阻塞。用 `select` 或线程给 `readline` 加一个超时，超时后抛 `ServerGone`。

验收：给玩具 server 加一个 `--hang-on tools/call` 参数（收到后 `time.sleep(60)`），client 在 2 秒内报错并清理子进程。

<details><summary>提示</summary>

最简单的做法是 `selectors` 模块监听 `proc.stdout` 的可读事件，带 timeout。或者把 `readline` 放进线程用 `queue.get(timeout=...)`。真实 SDK 用的是 asyncio 加 `asyncio.wait_for`，思路一样。

</details>

## 练习 4：listChanged

玩具 server 的 capabilities 里 `tools.listChanged` 是 `false`。如果改成 `true`，server 在工具列表变化时要发 `notifications/tools/list_changed`。设计一下：host 收到这个通知后该做什么？缓存的 `ToolSpec` 怎么办？正在进行的一次 tools/call 怎么办？

<details><summary>参考答案</summary>

收到通知后标记缓存失效，下一轮给模型工具之前重新 `tools/list`。正在进行的调用不受影响，它用的是调用时的 schema，server 有义务处理完。

真正的难点是白名单：新出现的工具默认不在白名单里，所以"server 加了一个工具"不会自动让模型看到它。这是正确的默认值。

</details>

## 练习 5：读一段记录，判断问题在哪一层

```text
-> initialize                      <- ok, protocol 2026-07-28
-> notifications/initialized
-> tools/list                      <- [search_notes, delete_note]
-> tools/call delete_note {uri: notes://todo}   <- result isError=false "deleted notes://todo"
assistant: 已经帮你清理了待办。
```

用户说他只是问"我的待办里有什么"。问题出在哪里？MCP 协议层、host 的白名单、还是模型？

<details><summary>答案</summary>

协议层完全正常，server 也没做错任何事。问题在 host：一个只读的问答请求，白名单里不该有 `delete_note`。模型选错工具是概率事件，会发生；让它有机会选到写工具是 host 的确定性错误。

顺带一提，这条记录里也看不到确认门（第 05 课守卫③）。有副作用的 MCP 工具和本地工具一样要过确认。

</details>
