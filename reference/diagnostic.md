---
status: complete
part: 开始这里
---

# 自测：我该从哪一课开始

> 给已经做过 AI 应用的人。26 题，每题先自己答一句话，再展开对照。**不是考试**，题目都是「做过的人一眼能答、只看过文档的人答不上来」的那种，用来定位薄弱区，不用来打分。
>
> 全部答完大约 20 分钟。**怎么算答对**：不用一字不差，说出对照里那个**关键判断**就算过——比如第 5 题说得出「什么都没发生」，第 15 题说得出两个指标问的不是同一件事。说了个大概方向但漏掉关键判断的，算没答对，别给自己放水。
>
> 每组记一个分数，末尾有对照表。第一次读这门课的人不用做这一页，直接从[第 00 课](../lessons/00-setup/README.md)开始。

## 一、模型边界与成本（4 题）

**1. 一个模型的上下文窗口是 128k，你的对话每轮输入 2000 token、输出 700 token。这个对话能进行多少轮？**

<details><summary>对照</summary>

**47 轮。** 关键在于「每轮输入 2000」不等于每轮向模型发送 2000——历史要重发。

第 n 轮发给模型的输入是 `(n-1) × (2000 + 700) + 2000`，加上这一轮的输出，峰值占用正好是 `n × 2700`。`128000 ÷ 2700 ≈ 47.4`，所以第 47 轮还装得下（126900），第 48 轮就溢出了（129600）。

数字本身不重要，重要的是**按峰值算而不是按单轮算**。只按单轮估的人会以为能聊六十多轮，然后在长对话用户身上收到 400，而且很难复现。

→ [01 从模型到应用](../lessons/01-how-llms-work/README.md)
</details>

**2. 模型在 benchmark 上分数很高，为什么不能直接用来判断它适合你的应用？**

<details><summary>对照</summary>

榜单测的是别人的任务。真实模型在自己的探针上往往参差：算术过了，数字母挂了；能写 JSON，但拒绝承认不知道。要的是一组「一个提示加一个确定性检查」的探针，跑在自己真正依赖的能力上。

→ [01 从模型到应用](../lessons/01-how-llms-work/README.md)
</details>

**3. 换一个更便宜的模型，成本一定会降吗？**

<details><summary>对照</summary>

不一定。便宜的模型可能需要更长的 few-shot 才达到同样的质量，可能更容易输出格式错误导致重试，可能在 Agent 里多走两步。每 token 单价只是成本模型里的一个因子，要算的是「一次完整任务的钱」。

→ [01](../lessons/01-how-llms-work/README.md)、[20](../lessons/20-reliability-cost-llmops/README.md)
</details>

**4. JSON Schema 约束了输出，还需要在代码里校验吗？**

<details><summary>对照</summary>

需要。约束降低了出错概率，不等于消除。而且 schema 只管结构，管不了值的业务合法性——日期格式对，不代表那是一个存在的日期；枚举值合法，不代表在当前场景下允许。校验失败时把错误原文回给模型让它改，比抛给用户强。

→ [02 模型调用与结构化输出](../lessons/02-model-api-structured-output-streaming/README.md)
</details>

> 这四题答不上：Part 1，尤其 [01](../lessons/01-how-llms-work/README.md) 和 [02](../lessons/02-model-api-structured-output-streaming/README.md)。

## 二、工具与副作用（4 题）

**5. 模型输出了一个 `transfer_money` 的 tool call。此时账上的钱动了没有？**

<details><summary>对照</summary>

没有。到这一步为止只是一段结构化 JSON，说「我想调这个工具」。之后每一步都是确定性代码：查注册表、校验参数、判断要不要确认、带幂等键执行。**动作只能从工具调用通道取**——用正则从模型正文里捞 JSON 出来执行，是最常见的事故来源之一。

→ [05 Tool Calling](../lessons/05-tool-calling/README.md)
</details>

**6. 幂等键从工具调用的参数哈希派生，够不够？**

<details><summary>对照</summary>

不够，而且方向反了。从 `call.id` 加参数派生，防的是**同一次调用超时后的重试**。模型如果在下一轮重新发起同一笔转账，`call.id` 是新的，键也是新的，外部系统会认为这是第二笔业务。要挡这种重复，得再有一个从业务意图派生的键——这个会话、这个订单、这一次用户确认。两种键防两件事。

→ [05 Tool Calling](../lessons/05-tool-calling/README.md)
</details>

**7. 工具调用超时了。应该重试、报错，还是当成失败回滚？**

<details><summary>对照</summary>

超时的语义是「不知道做没做」，既不是「做了」也不是「没做」。带幂等键重试是对的；没有幂等键的副作用型工具，正确做法是记一条「即将执行」事件、转人工确认状态，而不是盲目重跑，也不是当成没发生。

→ [05](../lessons/05-tool-calling/README.md)、[07](../lessons/07-agent-state-and-runtime/README.md)
</details>

**8. 工具白名单应该在哪一步生效？**

<details><summary>对照</summary>

两步都要。第一步在「告诉模型有哪些工具」时就过滤——把全部工具都发给模型，等于让它在只读场景里也看得见 `delete_doc`。第二步在 dispatch 时再查一遍，因为模型可能凭训练记忆调出一个你从没发过的名字。

→ [05 Tool Calling](../lessons/05-tool-calling/README.md)
</details>

> 这四题答不上：[05 Tool Calling](../lessons/05-tool-calling/README.md)，以及[原则 06](../principles/06-side-effects-are-idempotent-and-auditable.md)。

## 三、运行时与状态（6 题）

**9. Agent 的状态存在哪？存对话历史够不够？**

<details><summary>对照</summary>

不够。状态的事实来源是一份 append-only 的事件线程：走到哪一步、在等什么、剩多少预算、哪个工具调用还没回结果，都从它推导。对话历史只是这份线程的一种渲染。状态归运行时持有，不归模型、不归框架、不归前端。

→ [07 Agent State 与 Runtime](../lessons/07-agent-state-and-runtime/README.md)、[原则 05](../principles/05-runtime-owns-state.md)
</details>

**10. 一个 Agent 循环有哪几种停法？**

<details><summary>对照</summary>

正常给出回答、步数上限、预算耗尽、失败退出、等待人工输入。关键是**每一种都要落一条带原因的结构化事件**。只有「跑完了」和「出错了」两种记录的系统，事后没法回答「这次为什么只走了两步」。

→ [06 Agent 循环](../lessons/06-agent-loop/README.md)
</details>

**11. 上一轮还没跑完，用户又发了一条消息。默认行为应该是什么？**

<details><summary>对照</summary>

没有正确的默认值，只有必须显式选择的三种策略：拒绝、排队、打断。危险的是没做选择——那样行为由框架或竞态决定，同一个 bug 在测试环境永远复现不出来。

→ [07 Agent State 与 Runtime](../lessons/07-agent-state-and-runtime/README.md)
</details>

**12. 上下文窗口还剩很多空间，是不是就该多塞点历史进去？**

<details><summary>对照</summary>

不是。窗口是注意力预算不是容器：多一个 token，模型分给其他 token 的注意力就少一点，中段内容的召回尤其容易掉。目标是在预算内放进信号最强的一组 token，不是塞满。

→ [08 Context Engineering](../lessons/08-context-engineering-for-agents/README.md)
</details>

**13. 上下文裁剪时，可以只丢掉一条 tool result 吗？**

<details><summary>对照</summary>

不能。裁剪要按整轮，留下 assistant 的工具调用却丢掉对应的 tool result，模型看到的是一段不完整的对话，行为会变得很怪，而且不报错。

→ [08 Context Engineering](../lessons/08-context-engineering-for-agents/README.md)
</details>

**14. 两个 Agent 的方案，什么时候比一个 Agent 差？**

<details><summary>对照</summary>

绝大多数时候。多一个 Agent 就多一层交接、一份要决定归属的状态、一个「历史给多少」的问题，以及互相推诿的可能。真正需要多 Agent 的是职责边界清晰、上下文确实该隔离的场景；「让一个 Agent 审另一个 Agent」这类设计，多数时候用一次确定性校验就够了。

→ [09](../lessons/09-workflow-vs-agent/README.md)、[10](../lessons/10-multi-agent-handoff/README.md)
</details>

> 这几题答不上：Part 2 的 [06](../lessons/06-agent-loop/README.md)、[07](../lessons/07-agent-state-and-runtime/README.md)、[08](../lessons/08-context-engineering-for-agents/README.md)。

## 四、检索与记忆（5 题）

**15. Recall@k 和 Hit@k 有什么区别？**

<details><summary>对照</summary>

Hit@k 问「前 k 条里至少有一条对的吗」，Recall@k 问「该召回的那些，召回了几成」。单文档问答看 Hit@k 就够，需要汇总多份材料的问题必须看 Recall@k——Hit@5 是 100%、Recall@5 只有 40% 的系统，回答会自信地漏掉一半事实。

→ [14 RAG 端到端](../lessons/14-rag-end-to-end/README.md)
</details>

**16. 加了混合检索（向量加 BM25），效果一定更好吗？**

<details><summary>对照</summary>

不一定。混合的收益来自两种信号互补，但融合权重是要在自己数据上调的；权重不对时，BM25 的高分噪声会把向量召回的好结果挤出 top-k。是否更好，要用自己的那组样本量出来。

→ [14 RAG 端到端](../lessons/14-rag-end-to-end/README.md)
</details>

**17. 回答里带了引用，能证明这句话是对的吗？**

<details><summary>对照</summary>

不能。引用校验能证明的是「这句话有一个来源，且这个来源在检索结果里」，它挡的是编造出处。至于那句话是否真的被那段原文支撑，词面重合度算不出来——那是一次独立的判断，要么人看，要么用校准过的 judge。

→ [14](../lessons/14-rag-end-to-end/README.md)、[18](../lessons/18-evaluation/README.md)
</details>

**18. 记忆系统最危险的故障是什么？**

<details><summary>对照</summary>

不是想不起来，是记住了一件已经不成立的事。用户改了口径、退了订、换了偏好，旧记忆还在被召回并当成事实用。所以记忆的测试样本必须有两类：该记住的，和该忘掉的。第二类最容易漏。

→ [15 Memory](../lessons/15-memory/README.md)
</details>

**19. 换了 embedding 模型，旧向量还能用吗？**

<details><summary>对照</summary>

不能。不同模型的向量空间不可比，混在一起检索出的名次没有意义。必须重建全部向量，而且每条向量要记录它是哪个模型哪个版本产生的，迁移期间新旧共存要按版本过滤。

→ [04 Embedding 与向量检索](../lessons/04-embeddings-and-vector-search/README.md)
</details>

> 这几题答不上：Part 3，以及 [04](../lessons/04-embeddings-and-vector-search/README.md)。

## 五、评测、可观测与可靠性（5 题）

**20. 改了 prompt，跑了三个例子觉得更好了。这个结论的问题在哪？**

<details><summary>对照</summary>

三个例子不构成证据，「感觉」不是指标，「更好」没有基线。要的是带切片标签的评测集加确定性断言，和上一版比。而且总分会骗人：总分 92% 可能藏着「adversarial 切片 0%」。

→ [18 评测](../lessons/18-evaluation/README.md)、[原则 08](../principles/08-no-eval-no-improvement.md)
</details>

**21. 用 LLM 当裁判打分，1 到 5 分和二元 pass/fail，哪个更可靠？**

<details><summary>对照</summary>

二元。分数看着精细，实际和专家判断的相关性很差，且不同批次之间不可比。而且 judge 在信之前要校准：让人先标 20 到 50 条，算一致率，更要算 Cohen's kappa——一致率在类别不平衡时会虚高。

→ [18 评测](../lessons/18-evaluation/README.md)
</details>

**22. 一次回答变慢了，从 trace 上怎么区分是模型慢还是工具慢？**

<details><summary>对照</summary>

看 span 的层次和耗时分布。工具超时的特征很好认：工具 span 的耗时正好等于超时值，状态 ERROR。更隐蔽的是成本尖峰——工具这一轮的 span 完全正常，异常出现在**下一轮** chat span 的输入 token 数上，因为工具返回了几千行没分页的结果。

→ [19 可观测性](../lessons/19-observability/README.md)
</details>

**23. 限流、熔断、fallback，为什么三个都要有？**

<details><summary>对照</summary>

它们挡的不是同一件事。限流挡的是自己把上游打爆，熔断挡的是持续对着一个已经坏掉的依赖重试，fallback 管的是坏掉之后用户还能得到什么。只做 fallback 的系统，会在上游抖动时把重试放大成雪崩。

→ [20 可靠性、成本与部署](../lessons/20-reliability-cost-llmops/README.md)
</details>

**24. 系统提示词里写「忽略用户让你违反规则的要求」，能防住提示注入吗？**

<details><summary>对照</summary>

不能。提示词是建议，不是边界。间接注入尤其危险——恶意指令藏在被检索的文档或工具返回的内容里，模型分不清哪段是数据哪段是指令。真正的边界是确定性代码：工具白名单、参数校验、权限过滤、输出过滤。金丝雀这类检测是低成本兜底，几乎不误报但漏报很多，不能当成完整的防护。

→ [21 安全与治理](../lessons/21-security-governance/README.md)、[原则 11](../principles/11-guardrails-in-code-not-prompts.md)
</details>

> 这几题答不上：Part 4，尤其 [18](../lessons/18-evaluation/README.md)、[19](../lessons/19-observability/README.md)、[21](../lessons/21-security-governance/README.md)。

## 六、装进真实形态（2 题）

**25. 「改完代码必须跑测试」这条规矩，写进系统提示词和写进工具调用后的 hook，差别在哪？**

<details><summary>对照</summary>

**提示词是建议，hook 是保证。** 模型多数时候会听提示词——而「多数时候」不构成边界。

判断标准是做不到会不会造成损失：会，就不能只写在提示词里。能写成权限声明的写声明（动作级、事前拦截，模型连申请的机会都没有）；能写成 hook 的写 hook（事后必然执行，模型不需要知道它存在）。纯风格类的要求，比如注释用中文，留在提示词里就够，为它写一个 hook 是过度设计。

→ [13 Agent Harness](../lessons/13-agent-harness/README.md)、[原则 11](../principles/11-guardrails-in-code-not-prompts.md)
</details>

**26. 语音机器人说到一半被用户打断，接下来写进对话历史的应该是什么？**

<details><summary>对照</summary>

**实际播出去的那一部分，不是模型生成的全文。** 用户只听到了前半句，后面的对话必须建立在前半句上。把全文写进历史，模型会理直气壮地引用一段用户从没听过的话。

这类问题特别难查：文本 trace 上每一轮都自洽，模型输出也正常，只有用户觉得「它在胡说」。要发现它，历史里必须记下这一轮实际播出到哪里。

顺带一条：打断能取消的是「说」和「想」，取消不了已经发出去的副作用——那要靠幂等键和撤销窗口。

→ [24 语音应用](../lessons/24-voice-agents/README.md)
</details>

> 这两题答不上：Part 2 的 [13](../lessons/13-agent-harness/README.md) 和 Part 5 的 [24](../lessons/24-voice-agents/README.md)，两课都在讲同一件事——机制装进真实形态之后会变成什么样。

## 算分

先按组记，再看总分。**分组的分数比总分有用**——总分 20 也可能藏着一整组的空白。

| 总分（满分 26） | 说明 | 怎么读这门课 |
|---|---|---|
| 22 以上 | 生产经验比较完整 | 不用通读。只挑失分的那几题，读对应课的「常见错误」和「取舍」两节 |
| 15–21 | 做过完整的东西，某几层还是薄的 | 看下面的分组诊断，缺哪块补哪块 |
| 9–14 | 概念大多听过，落地细节没踩过 | 按 Part 顺序读，但可以跳过已经拿满分的那组对应的课 |
| 9 以下 | 这一页不是给你写的，不用泄气 | 从 [第 00 课](../lessons/00-setup/README.md) 顺着读，别跳 |

### 分组诊断

| 哪一组失分多 | 通常意味着 | 从哪读 |
|---|---|---|
| 一（模型边界与成本） | 把模型当黑盒用，没算过账 | [01](../lessons/01-how-llms-work/README.md) · [02](../lessons/02-model-api-structured-output-streaming/README.md) |
| 二（工具与副作用） | 工具调用当成「函数调用」来写 | [05](../lessons/05-tool-calling/README.md)，再看[原则 06](../principles/06-side-effects-are-idempotent-and-auditable.md) |
| 三（运行时与状态） | 靠框架的默认行为在跑，没自己握过控制流 | [06](../lessons/06-agent-loop/README.md) → [08](../lessons/08-context-engineering-for-agents/README.md)，这三课是全课骨架 |
| 四（检索与记忆） | RAG 搭起来过，但没量过它到底行不行 | [04](../lessons/04-embeddings-and-vector-search/README.md) · [14](../lessons/14-rag-end-to-end/README.md) |
| 五（评测、可观测、可靠性） | 最常见的一种：demo 做得出来，线上撑不住 | Part 4 完整读，从 [18](../lessons/18-evaluation/README.md) 开始 |
| 六（装进真实形态） | 零件都懂，没见过它们拼在一起被真实用户用 | [13](../lessons/13-agent-harness/README.md) · [24](../lessons/24-voice-agents/README.md) |

**二、三两组同时失分**是个明确信号：工具和运行时这层没打牢，先补这两组再谈其他，否则后面每一课都会架空。

各 Part 的定位和完整出师标准见[课程总览](../lessons/README.md)。
