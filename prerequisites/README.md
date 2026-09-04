# 前置｜Python、算法、后端与 LLM 原理

> 主线课程默认你已经掌握这里的全部内容，不会在课里回头补 Python 语法、数据结构、asyncio 或 Transformer 是什么。四组模块：Python 语言、算法、后端工程、LLM 原理。零基础按顺序学；有经验的人做一遍自检，缺哪个补哪个。

## 自检

每一条都能做到，就直接去 [主线第 00 课](../lessons/00-setup/README.md)。

**Python 语言**

- [ ] 会用 uv 建虚拟环境、装依赖、跑脚本
- [ ] 能读懂并写出带类型注解的函数、dataclass 和 Pydantic 模型
- [ ] 能解释 coroutine、Task、事件循环的关系；知道同步 I/O 为什么会阻塞整个服务；用过 `TaskGroup` 和 `timeout`

**算法**

- [ ] 能说出一段代码的时间复杂度，并解释多轮对话的总输入 token 为什么近似平方增长
- [ ] 知道字典为什么是 O(1)、什么对象可哈希，能给一个工具调用生成稳定的幂等键
- [ ] 能用堆取 top-k、用队列做 BFS、对一张 DAG 做拓扑排序并找出能并行的节点
- [ ] 能解释线程、进程、协程的区别和 GIL 限制了什么，能写出一个竞态条件的例子并修复它

**后端工程**

- [ ] 写过 FastAPI 接口，知道状态码语义、鉴权头、依赖注入
- [ ] 会建表、加索引、写 JOIN；能解释一种事务隔离级别；用过 SQLAlchemy 2.0 和 Alembic
- [ ] 用过 Redis 的 `SET NX EX`，能说出为什么 Redis 不该当事实来源
- [ ] 用 pytest 写过 fixture 和参数化测试
- [ ] 会 Git 分支、rebase、解决冲突；会 Docker Compose 起依赖

**LLM 原理**

- [ ] 能用一句话说清 LLM 在做什么，并推出"没有记忆"、"不是数据库"、"输出是抽样"三个后果
- [ ] 能解释 token 和字的关系、为什么中文更贵、上下文窗口为什么是每轮都在花的预算
- [ ] 能说清 attention 为什么 O(n²)、KV cache 是什么、GQA 和量化各省了什么
- [ ] 能说出预训练、SFT、偏好对齐各给了模型什么，以及一个质量问题该改提示、加检索还是微调

## 四组模块

### Python 语言（P00～P07）

| # | 模块 | 一句话 | 主线落点 | 状态 |
|---|---|---|---|---|
| P00 | [环境与工具链](./python/00-setup-and-tooling/README.md) | 装好 Python 3.12 和 uv，会用终端、虚拟环境、REPL 和编辑器，能跑第一个脚本 | lessons/00 | complete |
| P01 | [Python 基础语法](./python/01-python-basics/README.md) | 变量、数字与字符串、条件与循环、函数与作用域 | 全部 | complete |
| P02 | [容器与迭代](./python/02-collections-and-iteration/README.md) | list / dict / set / tuple、切片、推导式、生成器、`enumerate` / `zip` | lessons/02 | complete |
| P03 | [模块、异常与日志](./python/03-modules-errors-and-logging/README.md) | 把代码拆成模块和包；用异常表达失败并正确捕获；用 logging 而不是 print | lessons/05, 19 | complete |
| P04 | [类、dataclass 与 Protocol](./python/04-oop-and-dataclasses/README.md) | 类和实例、`@dataclass`、`Protocol` 鸭子类型 | lessons/05, 06, 07 | complete |
| P05 | [类型注解](./python/05-typing/README.md) | 为什么 AI 应用代码离不开类型：注解语法、Optional、泛型、TypedDict、Literal，用 pyright 检查 | lessons/02, 05 | complete |
| P06 | [Pydantic v2](./python/06-pydantic/README.md) | 用模型定义数据、校验输入、序列化输出、导出 JSON Schema | lessons/02, 05 | complete |
| P07 | [asyncio 并发](./python/07-asyncio/README.md) | coroutine、Task、事件循环；`gather` 与 `TaskGroup`；超时、取消与资源清理；Semaphore 限并发 | lessons/02, 10；project/m0 | complete |

### 算法（A00～A06）

只讲 AI 应用工程真正会碰到的七个主题，不是刷题课。总览见 [algorithms/README.md](./algorithms/README.md)。

| # | 模块 | 一句话 | 主线落点 | 状态 |
|---|---|---|---|---|
| A00 | [复杂度](./algorithms/00-complexity/README.md) | 用 token、延迟和钱来度量增长；对话为什么平方增长 | lessons/01, 08, 23 | outline |
| A01 | [Hash](./algorithms/01-hashing/README.md) | 字典与集合的原理、内容哈希、幂等键的规范化、LRU | lessons/05, 08, 15 | outline |
| A02 | [栈、队列与 Deque](./algorithms/02-stacks-queues/README.md) | 事件队列、有界缓冲、backpressure 的三种策略 | lessons/02, 07, 16 | outline |
| A03 | [堆与 Top-K](./algorithms/03-heaps-topk/README.md) | top-k、多路合并、RRF、优先级调度 | lessons/04, 13, 19 | outline |
| A04 | [树](./algorithms/04-trees/README.md) | Markdown 标题树切块、JSON Schema 遍历、Trie、决策树路由 | lessons/09, 13, 15, 20 | outline |
| A05 | [图、BFS/DFS 与拓扑排序](./algorithms/05-graphs/README.md) | Workflow DAG、并行度、环检测、框架里的 State Graph | lessons/06, 09, 10 | outline |
| A06 | [并发模型](./algorithms/06-concurrency-models/README.md) | 线程、进程、协程；GIL；竞态、锁与死锁；单写者 | P07, lessons/07；project/m0, m2 | outline |

### 后端工程（P08～P12）

| # | 模块 | 一句话 | 主线落点 | 状态 |
|---|---|---|---|---|
| P08 | [HTTP 与 FastAPI](./python/08-http-and-fastapi/README.md) | HTTP 请求响应、状态码、JSON、鉴权头；httpx 发请求；FastAPI 写最小 API、路径参数、依赖注入、SSE 流式 | lessons/02, 16；project/m1 | complete |
| P09 | [SQL、PostgreSQL 与 SQLAlchemy](./python/09-sql-and-sqlalchemy/README.md) | 建表、索引、JOIN、事务；SQLAlchemy 2.0 的 ORM 与 session；Alembic 迁移 | lessons/14, 16；project/m2 | complete |
| P10 | [pytest 与测试思维](./python/10-testing/README.md) | fixture、参数化、mock、断言异常；先写测试再写实现；怎样给不确定的模型输出写测试 | lessons/17；project 全部 | complete |
| P11 | [Git、命令行与 Docker Compose](./python/11-git-cli-and-docker/README.md) | 分支、提交、rebase、解决冲突；常用 shell 命令；用 Docker Compose 一条命令起 PostgreSQL 和 Redis | project/m2 起 | complete |
| P12 | [Redis](./python/12-redis/README.md) | TTL、`SET NX` 幂等键与运行锁、令牌桶限流；Redis 为什么不当事实来源 | lessons/05, 07, 19；project/m2, m5 | outline |

### LLM 原理（F00～F07）

到"能做技术决策"为止，不训练模型。总览见 [llm-foundations/README.md](./llm-foundations/README.md)。

| # | 模块 | 一句话 | 主线落点 | 状态 |
|---|---|---|---|---|
| F00 | [LLM 是什么](./llm-foundations/00-what-an-llm-is/README.md) | Next Token Prediction 及其三个直接后果；能力从哪来 | lessons/01, 07, 13 | draft |
| F01 | [Tokenization](./llm-foundations/01-tokenization/README.md) | BPE、token 效率、embedding 层、特殊 token | lessons/01, 02, 08 | draft |
| F02 | [Embedding 与向量空间](./llm-foundations/02-embeddings/README.md) | 文本 embedding 模型是什么、余弦与归一化、维度与模型绑定 | lessons/04, 13, 14 | outline |
| F03 | [Attention 与 Transformer](./llm-foundations/03-attention-and-transformer/README.md) | 一次 attention 在算什么、O(n²)、GQA；block 结构与参数量 | lessons/08, 21 | draft |
| F04 | [Context Window 与 Sampling](./llm-foundations/04-context-window-and-sampling/README.md) | 窗口是每轮都在花的预算；temperature 与 top-p 改了什么 | lessons/01, 02, 08 | draft |
| F05 | [训练与对齐](./llm-foundations/05-training-and-alignment/README.md) | 预训练、SFT、RLHF / DPO 各给了什么；对话模板；分类微调与 LoRA | lessons/03, 05, 21 | draft |
| F06 | [KV Cache 与推理](./llm-foundations/06-kv-cache-and-inference/README.md) | prefill 与 decode、KV cache 显存、量化、批处理、prompt caching | lessons/08, 19, 21 | draft |
| F07 | [模型地图](./llm-foundations/07-model-landscape/README.md) | 五类模型、开放权重与托管、怎么读模型卡 | lessons/01, 21 | outline |

## 学法

1. 推荐顺序：P00～P06 → A00～A05 → P07 与 A06 一起 → P08～P12 → F00～F07。Python 语言和后端工程之间没有捷径；算法组不长，放在中间正好给 P07 的并发打底。
2. 每个模块先跑 `code/`，再读正文，再做 `exercises.md`。
3. 「它在 AI 应用里用在哪」这一节告诉你这个知识点将来在哪会用到。看不懂没关系，知道有这回事就行。
4. 学到 P07 asyncio 时同步做 [project/m0](../project/m0-concurrency/README.md)，这是主项目的第一个里程碑。
5. 有后端经验但没碰过 LLM 的人，只学 F 组就能进主线。

## 不在这里讲的

- 排序、动态规划、字符串匹配这类面试算法：AI 应用开发几乎不手写，需要时看 [Hello 算法](https://www.hello-algo.com/)。
- 前端：主线第 22 课会讲 AI 产品的交互设计，但不教写页面。
- 训练代码与分布式训练：F 组只到应用工程师需要的那一层，往下看 LLMs-from-scratch。
