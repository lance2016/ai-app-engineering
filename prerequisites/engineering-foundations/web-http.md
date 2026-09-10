---
status: complete
part: 背景知识
---

# Web 与 HTTP：把一次调用看成一组消息

> 先看请求和响应怎样组成，再区分 REST、HTTPS、SSE、认证和模板这些经常被混在一起的词。

## 请求、响应与 Web 词汇

HTTP 请求至少有方法、URL、headers 和可选 body；响应有状态码、headers 和可选 body。JSON 只是 body 的一种格式，schema 才说明字段、类型和必填关系。HTTP 本身无状态，应用要用 cookie、token 或自己的 thread id 关联多次请求。

| 概念 | 先理解什么 | 主线落点 |
|---|---|---|
| 方法语义 | `GET` 读取，`POST` 通常创建或触发动作，`PUT` 替换，`DELETE` 删除；是否幂等要看接口语义 | 02、05、17 |
| 状态码 | 4xx 多是请求或权限问题，5xx 多是服务或下游问题；具体语义以接口契约为准 | 02、21 |
| 契约和版本 | schema 是客户端和服务端共同遵守的字段约定；`/v1` 是兼容性边界，新增字段通常比改名或改类型安全 | 02、18 |
| 超时与重试 | 超时只说明客户端没等到结果，不说明服务端没有完成；重试前要确认操作是否可重复 | 05、21 |
| SSE | 服务端在一个 HTTP 响应里连续发送事件；断线恢复需要事件 id 或 checkpoint | 02、07、18 |

### 常见 Web 词汇：知道它解决哪一层问题

这些词经常一起出现在项目文档里，但它们不在同一层。REST 是接口设计风格，HTTPS 是传输安全，Jinja2 是 HTML 模板工具；把它们都叫“后端框架”会混淆排查方向。

| 词 | 先形成的直觉 | 参考实现中的位置 | 优先级 |
|---|---|---|---|
| REST / RESTful | 用资源和 HTTP 方法表达操作的一组设计约束；HTTP API 不一定都满足完整 REST 约束 | `/v1/threads`、`/v1/knowledge` 是资源路径，`human-input` 这类动作接口仍要看契约和幂等性 | 现在理解 |
| HTTPS / TLS | HTTP 在 TLS 加密连接上传输；它保护传输过程并验证服务器身份，不负责判断用户有没有权限 | 本地参考项目用 HTTP 便于调试；公开部署时由入口层提供 HTTPS | 现在理解 |
| Cookie、Session、Bearer token | Cookie 通常由浏览器自动带回；Session 是服务器保存的会话状态；Bearer token 是请求主动携带的凭证 | 参考实现从 `Authorization: Bearer ...` 解析租户，见 [`api/deps.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/deps.py) | 现在理解 |
| CORS / Origin | 浏览器默认限制脚本跨来源读取响应；CORS 用响应头声明允许哪些来源，和服务端之间的调用无关 | Playground 和 API 由同一个 FastAPI 服务提供，不需要额外跨来源配置；拆成两个域名时再配置 | 遇到跨域再学 |
| Jinja2 | 服务端先把变量填进 HTML 模板，再把生成后的页面发给浏览器；它和返回 JSON 的 API 是两条输出路径 | 参考实现的 Playground 是静态 [`playground.html`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/static/playground.html)，没有使用 Jinja2 | 知道名字 |
| OpenAPI / Swagger | OpenAPI 用机器可读的格式描述路径、参数和响应；Swagger UI 只是把这份描述变成可点击的文档 | FastAPI 默认提供 `/openapi.json` 和 `/docs`，方便检查接口契约 | 现在理解 |
| JWT、OAuth 2.0、OIDC | JWT 是令牌格式；OAuth 2.0 处理委托授权；OIDC 在此基础上描述登录身份，三者不是同一个东西 | 参考实现用配置里的简单 Bearer token，没有接外部身份提供商 | 遇到登录再学 |
| 反向代理 / 网关 | 站在应用前面接收域名和 HTTPS，再把请求转给应用；常放证书、压缩、限流和访问日志 | 参考实现本地直接运行 FastAPI；生产部署再看 M5 的[容器与部署说明](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/m5-production/README.md) | 遇到部署再学 |
| SSE 和 WebSocket | SSE 是服务器到浏览器的单向事件流；WebSocket 是双方都能持续发送消息的连接 | 文本 Playground 使用 SSE；语音方案只在[协议说明](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/demos/voice-agents.md)里讨论 WebSocket | 现在理解差异 |

官方资料访问日期均为 2026-09-10：[REST](https://developer.mozilla.org/en-US/docs/Glossary/REST)、[HTTPS](https://developer.mozilla.org/en-US/docs/Glossary/HTTPS)、[CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)、[Jinja 模板](https://jinja.palletsprojects.com/en/stable/templates/)、[WebSocket](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)、[FastAPI 交互式文档](https://fastapi.tiangolo.com/tutorial/first-steps/)、[OAuth 2.0 RFC](https://www.rfc-editor.org/rfc/rfc6749)、[JWT RFC](https://www.rfc-editor.org/rfc/rfc7519)、[OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)。遇到一个词时先判断它属于接口、传输、浏览器、身份还是部署层，再决定去哪里查。

名词的放置也按这个标准：主线需要拿来做判断的，写在工程能力正文；项目没用但读 Web 文档常会遇到的，放在本节表格；只需要查一句定义的，放[术语索引](../../reference/glossary.md)；具体依赖版本和安装方式，放[技术选型](../../reference/stack.md)或参考项目的启动说明。这样不会把工程能力页变成一张没有重点的名词清单。

### 网络底层：出错时先判断停在哪一层

浏览器访问一个地址时，通常先通过 DNS 找到 IP，再建立 TCP 连接；使用 HTTPS 时还要完成 TLS 握手，之后才发送 HTTP 请求。DNS 失败时请求还没到服务器；连接被拒绝通常表示目标端口没有服务在监听；一直超时可能卡在网络、TLS、连接池或下游服务；拿到 4xx 或 5xx 才说明应用已经返回了结果。

这一级只需要知道排查顺序，不要求先学数据包。可以先看 [MDN How the web works](https://developer.mozilla.org/en-US/docs/Learn_web_development/Getting_started/Web_standards/How_the_web_works) 和 [DNS 词条](https://developer.mozilla.org/en-US/docs/Glossary/DNS)，资料访问日期均为 2026-09-10。

### 依赖注入：路由函数不自己创建所有对象

路由函数需要租户、数据库、模型和限流器时，不必在函数体里逐个创建。FastAPI 的 `Depends` 让函数声明它需要什么，框架在每次请求时提供对应对象；测试时可以把真实模型换成 fake，把 PostgreSQL 换成内存实现。它只是对象组装和生命周期管理，不会自动解决业务逻辑。

参考实现的依赖入口在 [`api/deps.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/deps.py)，应用装配在 [`api/app.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/app.py)。官方资料访问日期为 2026-09-10：[FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)。

一个最小请求链是：客户端先发 `POST /v1/threads` 建立线程，再发 `POST /v1/threads/{id}/messages` 发送消息。服务端校验 body 和权限后，以 JSON 或 `text/event-stream` 返回结果。模型输出的每个增量都只是一个事件，只有运行时写入事件存储后，客户端才有恢复依据。

官方资料访问日期均为 2026-09-10：[MDN HTTP 概览](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview)、[HTTP 方法](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods)、[状态码](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)、[Server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)。读完方法和状态码，再看主线第 02 课的流式与错误处理。

---

[工程能力概览](./README.md) · [背景知识总览](../README.md)
