# 17 AI 应用系统架构与端到端数据流｜练习

## 练习 1：把工具调用加进请求链

正文的请求链里模型一次就给出了回答。把它扩成两轮：模型先请求 `search_kb`，运行时执行工具（假设 15 毫秒）并把结果记成事件，再调一次模型拿最终回答。

验收：`hop` 事件里多出 `tool` 一跳和第二次 `model`；同步模式下客户端总等待时间相应增加，流式模式下首字节时间也推后了。

<details><summary>提示</summary>

复用第 06 课的循环结构。这题的观察点是：工具调用让"首字节"变晚，因为增量只能在最后一次模型调用时产生。生产里的做法是在工具执行期间给客户端发状态事件（"正在查询知识库"），第 07 课的事件流就是为此准备的。

</details>

## 练习 2：给 SSE 端点加断线重连

正文的 SSE 端点每帧带了 `id:`。浏览器的 `EventSource` 重连时会带 `Last-Event-ID` 请求头。让端点读这个头，从对应位置继续发，而不是从头再发。

验收：用 `TestClient` 先请求一次，只读前两帧就关闭；再带 `Last-Event-ID: 1` 请求，收到的第一帧 id 是 2。

<details><summary>答案</summary>

```python
@app.get("/chat")
async def chat(q: str, request: Request) -> StreamingResponse:
    since = int(request.headers.get("last-event-id", -1)) + 1
    return StreamingResponse(agent_events(q, since=since), media_type="text/event-stream", headers=...)
```

`agent_events` 跳过 `i < since` 的帧。真实系统里增量要能重放，就意味着它们要先存下来（第 07 课的线程），而不是生成后即丢。

</details>

## 练习 3：长任务的结果怎么通知

`01` 的 `task` 模式里客户端拿到 id 后"轮询或订阅"。写出两种方案的接口设计（不用实现）：轮询用什么端点、返回什么状态；订阅用什么机制、客户端断线怎么办。

<details><summary>参考答案</summary>

轮询：`GET /tasks/{id}` 返回 `{status: queued|running|finished|failed, result?, error?}`，客户端按指数退避轮询。简单、无状态、对代理友好，代价是延迟等于轮询间隔。

订阅：`GET /tasks/{id}/events` 返回 SSE，任务的事件线程边写边推。客户端断线后用 `Last-Event-ID` 重连（练习 2）。延迟低，但服务端要维持连接，任务完成后要把最终状态也持久化，以便断线期间完成的任务仍能被查到。

生产里通常两个都提供，订阅做主路径，轮询做兜底。

</details>

## 练习 4：把限流计数器放错地方

正文的边界表里限流计数器放 Redis。如果有人把它放进 PostgreSQL，会发生什么？反过来，如果把审计记录放进 Redis 呢？

<details><summary>答案</summary>

限流计数器放 PostgreSQL：每个请求一次写事务，QPS 高的时候数据库先被限流器打垮。而且计数器丢了只是短暂放宽限制，完全可以接受，不值得付持久化的代价。

审计记录放 Redis：Redis 重启或内存淘汰后审计记录消失，出事时无法举证。审计的价值恰恰在"一定还在"。

两个方向的错误都来自没问那个问题：这个东西丢了能不能重建。

</details>

## 练习 5：在链上找出"每一跳都查一次数据库"

正文里 `gateway_auth` 返回了 `user_id`，后面的跳都收它。假设有人把 `retrieve()` 改成自己再根据 token 查一次用户拿权限标签。这样改的问题是什么？正确做法是什么？

<details><summary>答案</summary>

问题一：多一次数据库往返，而且每个需要权限的跳都会这样做，延迟线性增长。问题二：token 在链路深处传递，扩大了它的暴露面。问题三：网关和检索可能查到不同的结果（比如中间权限变了），链内不一致。

正确做法是网关解析一次，把 `user_id` 和权限标签作为一个请求上下文对象往下传。第 21 课讲多租户时会把这个对象正式化。

</details>
