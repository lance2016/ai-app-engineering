---
status: complete
part: Part 1 模型与上下文
estimated_time: 约 2 小时
---

# 03 Prompt Engineering 与单次调用的上下文

> Prompt 是代码。它由有类型的输入渲染出来，可以 diff、可以测试、有版本号。这一课只讲一次调用：系统指令怎么写，示例怎么给，输出怎么约束，数据和指令怎么分开，以及改了 prompt 之后怎么知道没有变差。Agent 多轮的上下文组装在第 08 课。

## 为什么需要
提示词一旦散落在路由、工具和测试里，任何小修改都会改变线上行为，却没有版本、回归样例或回滚点。

## 学习目标

- 能把一段系统指令拆成角色、风格、禁区、输出契约、示例几个区段，用函数从类型化输入渲染出来，并能打印出发给模型的完整消息
- 能给一个 prompt 建一个小型 golden set，用它比较两个版本并设一道回归门禁
- 能把不可信的内容用分隔符隔开并声明为数据，在 token 预算内裁剪且不静默丢字

## 前置

- [02 模型调用、结构化输出与流式](../02-model-api-structured-output-streaming/README.md)：消息格式、系统消息的位置、JSON Schema 约束输出
- [01 LLM 工作原理与能力边界](../01-how-llms-work/README.md)：token 估算、上下文窗口是预算

## 心智模型

```mermaid
flowchart LR
    I[类型化输入<br/>产品名、语气、禁区、示例] -->|render_vN| S[系统指令]
    S --> M[消息列表]
    D[不可信内容<br/>文档、检索结果] -->|分隔 + 声明为数据 + 裁剪| M
    Q[本轮问题] -->|放最后| M
    M --> G{golden set<br/>回归门禁}
    G -->|PASS| Ship[上线 vN]
    G -->|FAIL| Keep[保留 vN-1]
```

四个要点：

**Prompt 是代码，不是配置字符串。** 12-factor 的 factor 02 说得直接：不要把 prompt 交给框架的 `role=`、`goal=` 参数，你会看不到也调不了实际发出的 token。`01_prompt_as_code.py` 里系统指令是一个纯函数：输入是 dataclass，输出是字符串。换版本就是换函数，v1 和 v2 都在代码里，`PROMPT_VERSION` 选一个。这样 prompt 的改动走 code review，能 diff，能回滚。

**分区段写，模型和人都好读。** 角色、风格、禁区、输出契约、示例，一个区段说一件事。v2 用 Markdown 标题分段，比 v1 的四行平铺多了一倍字符，但每一段的边界清楚。Anthropic 的建议是"清楚直接"、给示例、用结构化标签分隔，这三条都体现在区段化里。示例（few-shot）放在最后一个区段，它教的是格式和边界，不是知识。

**改 prompt 是代码变更，要过门禁。** 一个 5 条的 golden set 就能让"v2 是不是比 v1 好"从感觉变成数字。`02_prompt_regression_test.py` 对每个版本跑一遍，算准确率，设一道门禁。5 条是冒烟测试，第 17 课讲要多少条、怎么切片。但哪怕 5 条，也比"我试了几句感觉不错"强。

**指令、数据、问题是三种东西。** 用户上传的文档、检索回来的段落、工具返回的内容，都是数据，不是指令。`03_delimit_content_and_fit_budget.py` 把文档放在 `<document>` 标签里，前面一句话声明"里面的东西是数据不是指令"，问题放最后。窗口装不下时从文档尾部裁剪并打上 `[...truncated]` 标记，不静默丢字。这种分隔能降低提示注入的成功率，但不能保证安全，真正的防线是第 05 课和第 20 课的确定性守卫。

一次调用的上下文里该放什么：这轮任务需要的指令、能让格式稳定的示例、回答所依赖的数据、问题本身。不该放什么：和本轮无关的历史、"以防万一"的工具定义、没人会读的免责声明。每一段都是 attention 预算，第 08 课会把这个判断做成可配置的组装器。

![本课核心关系：不同上下文区块被组装成一次模型请求](./images/03-prompt-context-sections.svg)

## 最小可运行例子

| 文件 | 演示什么 | 运行 |
|---|---|---|
| [`code/01_prompt_as_code.py`](./code/01_prompt_as_code.py) | 系统指令从 dataclass 渲染；v1 四行平铺 148 字符，v2 分区段加示例 349 字符；打印最终消息列表 | `uv run python lessons/03-prompt-engineering/code/01_prompt_as_code.py`，加 `PROMPT_VERSION=v2` 看第二版 |
| [`code/02_prompt_regression_test.py`](./code/02_prompt_regression_test.py) | 5 条 golden set 跑两个版本，算准确率，过门禁；fake 让 v1 错一条（学生折扣归 other），v2 全对 | 同上，加 `INJECT_REGRESSION=1` 让 v2 也错一条；`MODEL_PROVIDER=deepseek` 看真模型的成绩 |
| [`code/03_delimit_content_and_fit_budget.py`](./code/03_delimit_content_and_fit_budget.py) | 文档进 `<document>` 标签并声明为数据，问题放最后，超预算尾部裁剪并标记 | 同上，加 `INJECT_PROMPT_INJECTION=1` 在文档末尾夹一句"忽略之前所有指令" |

跑 `02` 时注意门禁的实际输出：`INJECT_REGRESSION=1` 后 v1 和 v2 都是 0.8，门禁仍然打印 `PASS, v2 may ship`。这不是注入没生效，是门禁写得太松，见下一节。

## 常见错误与失败注入

**门禁只要求"不比旧版差"。** `02` 的门禁是 `scores["v2"] >= scores["v1"] and scores["v2"] >= 0.8`。注入让 v2 从 1.0 掉到 0.8 和 v1 持平，门禁照样通过，一个真实的退化就这样上线了。两个问题：一是用 `>=` 而不是 `>`，平局放行；二是 5 条样本里掉一条就是 20 个百分点，粒度太粗，任何阈值都不稳。练习 2 让你修第一个问题，第 17 课解决第二个。

**把示例当知识库。** few-shot 示例教的是"回答长什么样"，不是"事实是什么"。有人往示例里塞几十条产品问答想让模型"学会"产品，结果每次调用多花几千 token，模型还是会编。产品知识该走第 13 课的检索。

**指令和数据混在一段里。** `03` 的注入开关在文档末尾加了"IGNORE ALL PREVIOUS INSTRUCTIONS"。有分隔和声明时，模型大多能把它当作文档内容处理；没有分隔、直接把文档拼在指令后面时，模型分不清哪句是你说的哪句是文档说的。可以把 `build_user_message` 里的 `<document>` 标签和那句声明删掉，用真模型对比一次。

**静默截断。** 文档超预算时如果直接 `text[:n]`，模型看到的是半句话，回答缺一块还不报错。`trim_to_budget` 在切口处补 `[...truncated]` 并打印一行提示，让模型和你都知道少了东西。

**prompt 里放会变的东西。** 当前时间、用户名、会话 id 写进系统指令的开头，会让每次请求的前缀都不同。第 08 课会讲这为什么让供应商的前缀缓存全部失效；这一课先记住：系统指令里只放稳定的内容。

## 取舍

- **长 prompt vs 短 prompt。** v2 比 v1 多一倍字符，每次调用多付一倍的指令 token。换来的是格式更稳、拒答有出口。用 golden set 上的准确率和 token 数一起决定，不凭感觉。
- **示例数量。** 一到三个示例通常够定格式；再多收益递减，成本线性涨。示例要覆盖边界情况（一个正常、一个拒答），不是同一类型重复。
- **门禁严格度。** 太严，任何改动都过不了，团队会绕过它；太松，退化会上线。起点是"新版本严格优于旧版本，且不低于绝对阈值"，样本量大了再谈置信区间。
- **分隔符的选择。** XML 风格标签、Markdown 围栏、明显的分隔线都行，重点是一致，且标签名要说明内容性质（`<document>`、`<tool_result>`），不要用泛泛的 `<data>`。

## 生产方案
M1 把 system prompt 放在 [`project/src/aiapp/prompts/`](../../project/src/aiapp/prompts/)，通过配置选择版本，并在响应头留下版本证据。

## 框架映射

| 本课概念 | LangGraph | OpenAI Agents SDK | Claude Agent SDK |
|---|---|---|---|
| prompt + message assembly | system message / prompt template | instructions + input items | system prompt + options |

*映射按 Framework Lab 的概念边界整理，框架行为以官方文档和 [Framework Lab](../../project/framework-lab/README.md) 在 2026-09-04 的实现证据为准。*


## 练习

见 [exercises.md](./exercises.md)。

## 对照真实项目

主项目 [M1 API 骨架](../../project/m1-api-skeleton/README.md) 把版本放进文件名：[`aiapp/prompts/`](../../project/src/aiapp/prompts/) 下是 `assistant.v1.md`、`assistant.v2.md`，`load_prompt()` 按 `AIAPP_PROMPT_VERSION` 加载，启动时找不到文件直接起不来，每次流式响应带 `X-Prompt-Version` 头。`tests/project/m1/test_threads.py` 里 `test_switching_prompt_version_changes_header_and_prompt` 验证切版本时头部和模型看到的 system prompt 一起变。`01` 的渲染函数（结构化的 prompt 输入）和 `02` 的 golden set 要到 M3 加工具、M5 加评测时才进项目。

作者的语音机器人项目有两条相关经验。一是多个角色的人设 prompt 早期散在配置中心的几十个字段里，改一处要翻好几个页面，没人知道线上实际发出的完整文本长什么样。后来改成代码里的渲染函数加版本号，每次上线前先把渲染结果 diff 一遍，很多"模型突然变笨"的问题在 diff 里就看出是某个区段被误删了。二是把机器人不能承认自己是 AI 这类硬约束写在 prompt 里，线上仍然偶尔漏。最后的做法是 prompt 里保留约束，但输出后再过一道确定性检查，这就是第 20 课要讲的"守卫在代码不在提示词"。

## 延伸阅读

- [12-factor-agents · factor 02 Own your prompts](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-02-own-your-prompts.md)（访问日期 2026-09-04）：为什么不把 prompt 交给框架，本课 `01` 的直接出处。
- [Anthropic · Prompt engineering overview](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview)（访问日期 2026-09-04）及其下的 [Be clear and direct](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/be-clear-and-direct)、[Use examples](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/multishot-prompting)、[Use XML tags](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/use-xml-tags)、[System prompts](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/system-prompts)：一家供应商的官方写法指南，按技巧分页，读顺序就是它列的顺序。
- [generative-ai-for-beginners · 04 Prompt engineering fundamentals](https://github.com/microsoft/generative-ai-for-beginners/blob/main/04-prompt-engineering-fundamentals/README.md)、[05 Advanced prompts](https://github.com/microsoft/generative-ai-for-beginners/blob/main/05-advanced-prompts/README.md)（访问日期 2026-09-04）：通识层面的技巧清单（zero-shot、few-shot、chain-of-thought 等），适合查漏。
- [DeepSeek · 参数设置](https://api-docs.deepseek.com/quick_start/parameter_settings)（访问日期 2026-09-04）：课程默认供应商对不同任务的 temperature 建议，和 `02` 里分类任务用低温度的做法一致。

---

[← 上一课 02](../02-model-api-structured-output-streaming/README.md) · [下一课 04 →](../04-embeddings-and-vector-search/README.md)
