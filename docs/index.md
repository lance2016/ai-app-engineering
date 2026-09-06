---
hide:
  - navigation
  - toc
---

<div class="home" markdown="1">

<header class="hero" markdown="1">

# AI 应用工程

<p class="hero__en">AI Application Engineering</p>

<p class="hero__tagline">从一次模型调用，到生产级 AI 系统</p>

写给已经会 Python 和后端的开发者：系统学一遍 AI 应用怎么设计、怎么评测、怎么上线。每课都讲**为什么这样设计、什么时候会坏、坏了怎么办**。

<ul class="hero__meta">
<li>26 课</li>
<li>6 个 Part</li>
<li>不绑框架</li>
<li>面向生产</li>
</ul>

<div class="hero__cta" markdown="1">

[从 00 开始学](lessons/setup/README.md){ .md-button .md-button--primary .hero__start }
<a class="md-button md-button--primary hero__cont" data-prog-next href="#" hidden>接着读</a>

</div>

<div class="prog" data-progress markdown="1">
<div class="prog__body" hidden markdown="1">
<p class="prog__count"><strong data-prog-done>0</strong><span class="prog__total" data-prog-total>/ 26 课已掌握</span></p>
<div class="prog__ruler" data-prog-ruler></div>
<p class="prog__last">最近读的 · <a data-prog-last href="#"></a><button type="button" data-prog-reset>清除本机记录</button></p>
<p class="prog__note">进度只存在这台设备的浏览器里，不上传，不用登录，换设备不同步。</p>
</div>
</div>

</header>

<section class="band" id="start" markdown="1">

<p class="eyebrow">从哪开始</p>

## 挑一条路线

<p class="band__lede" markdown="span">三种起点，选最接近的那个，下面直接给入口。不确定底子够不够，先对一下[补充基础](prerequisites/README.md)。</p>

<div class="picker" data-picker>
<button class="picker__opt" type="button" data-path="a" aria-pressed="false">
<span class="picker__key">A</span>
<span class="picker__body">
<span class="picker__name">系统入门</span>
<span class="picker__txt">第一次系统学 AI 应用工程</span>
</span>
</button>
<button class="picker__opt" type="button" data-path="b" aria-pressed="false">
<span class="picker__key">B</span>
<span class="picker__body">
<span class="picker__name">查漏补缺</span>
<span class="picker__txt">做过 RAG / Agent，想知道自己缺什么</span>
</span>
</button>
<button class="picker__opt" type="button" data-path="c" aria-pressed="false">
<span class="picker__key">C</span>
<span class="picker__body">
<span class="picker__name">生产进阶</span>
<span class="picker__txt">手上有线上系统，要评测和可靠性</span>
</span>
</button>
</div>

<div class="paths" markdown="1">

<article class="path" data-path="a" markdown="1">
<p class="path__label">路线 A · 系统入门</p>
<p class="path__who" markdown="span">会写后端、能调通模型 API，但没系统学过这一套。整条链从头走一遍，26 课都是给你写的。</p>
<p class="path__pick" markdown="span">推荐章节：[00 起步](lessons/setup/README.md) → Part 1 到 Part 5 顺着读 → [12 条工程原则](principles/README.md)</p>
<p class="path__go" markdown="span">[开始读 00 起步](lessons/setup/README.md){ .md-button .md-button--primary }</p>
<details class="path__more" markdown="1">
<summary>这条路线怎么读</summary>
<ol class="tl" markdown="1">
<li markdown="span">**先花十分钟**读[课程总览](lessons/README.md)，知道六个 Part 各在搭什么。</li>
<li markdown="span">**从 [00 起步](lessons/setup/README.md)顺着读。** 编号是推荐顺序，前一课多半是后一课的地基，顺着读最省力。</li>
<li markdown="span">**卡在模型原理上再回补。** 正文出现「前置 F0x」的引用时，再去读[那八篇](prerequisites/README.md)，不用一开始就啃。</li>
<li markdown="span">**每学完一个 Part，回看[工程原则](principles/README.md)。** 12 条是全课的压缩版，先学机制再读原则，才读得进去。</li>
<li markdown="span">**想要能跑的代码**，去[参考实现仓库](https://github.com/lance2016/ai-app-engineering-ref)，七个里程碑和这门课的 Part 一一对应。</li>
</ol>
</details>
</article>

<article class="path" data-path="b" markdown="1">
<p class="path__label">路线 B · 查漏补缺</p>
<p class="path__who" markdown="span">做过 RAG、Agent 或 Function Calling，但说不清哪里薄。先用能力域清单对照手上的项目，再定点补，不用从头读。</p>
<p class="path__pick" markdown="span">推荐章节：[课程总览](lessons/README.md) → [06 Agent 循环](lessons/agent-loop/README.md) · [07 State 与 Runtime](lessons/agent-state-and-runtime/README.md) · [08 Context Engineering](lessons/context-engineering-for-agents/README.md) · [18 评测](lessons/evaluation/README.md)</p>
<p class="path__go" markdown="span">[对照能力清单找洞](lessons/README.md){ .md-button .md-button--primary }</p>
<details class="path__more" markdown="1">
<summary>这条路线怎么读</summary>
<ol class="tl" markdown="1">
<li markdown="span">**先用[课程总览](lessons/README.md)的能力域清单对照项目。** 十行，空着的那几行就是风险所在。</li>
<li markdown="span">**按结果挑 Part 读。** 每个 Part 开头有三到五题，答得上就跳过。做过 RAG 的人最常缺的是 Part 2 的运行时控制（[06](lessons/agent-loop/README.md) · [07](lessons/agent-state-and-runtime/README.md) · [08](lessons/context-engineering-for-agents/README.md)）和 Part 4 的评测（[18](lessons/evaluation/README.md)）。</li>
<li markdown="span">**用 [12 条工程原则](principles/README.md)对照现有项目。** 每条都有反例和正确形态，对不上的那条就去读它指向的课。</li>
<li markdown="span">**在选框架**，直接看[框架一览与选型标准](reference/frameworks.md)，不必等读完 Part 2。</li>
</ol>
</details>
</article>

<article class="path" data-path="c" markdown="1">
<p class="path__label">路线 C · 生产进阶</p>
<p class="path__who" markdown="span">手上有正在跑的 AI 应用，关心的是评测、trace、可靠性和架构。从生产那一圈骨架切进去。</p>
<p class="path__pick" markdown="span">推荐章节：[17 系统架构](lessons/system-architecture/README.md) → [19 可观测性](lessons/observability/README.md) · [18 评测](lessons/evaluation/README.md) → [20 可靠性与成本](lessons/reliability-cost-llmops/README.md) · [21 安全与治理](lessons/security-governance/README.md)</p>
<p class="path__go" markdown="span">[从 17 系统架构开始](lessons/system-architecture/README.md){ .md-button .md-button--primary }</p>
<details class="path__more" markdown="1">
<summary>这条路线怎么读</summary>
<ol class="tl" markdown="1">
<li markdown="span">**从 [17 系统架构](lessons/system-architecture/README.md)开始**，先把一次请求经过哪些跳、每一跳回答什么问题摆清楚。</li>
<li markdown="span">**先建证据链，再谈优化。** [19 可观测性](lessons/observability/README.md)给 trace，[18 评测](lessons/evaluation/README.md)给「凭什么说变好了」。顺序别反：没有 trace 的评测查不出原因。</li>
<li markdown="span">**再补兜底。** [20 可靠性与成本](lessons/reliability-cost-llmops/README.md)讲限流、熔断、fallback 各挡哪一类失败；[21 安全与治理](lessons/security-governance/README.md)讲边界为什么必须由代码执行。</li>
<li markdown="span">**回头补 [08 Context Engineering](lessons/context-engineering-for-agents/README.md)。** 线上「模型忘事」和成本尖峰，多数是这一层的问题。</li>
<li markdown="span">**最后读 [25 系统设计与决策](lessons/system-design-decisions/README.md)**，把容量估算和 ADR 补齐；原则 [07](principles/07-locate-failures-by-layer.md) · [08](principles/08-no-eval-no-improvement.md) · [09](principles/09-trace-is-first-class.md) · [10](principles/10-cost-and-latency-are-design-constraints.md) 是这条路线的压缩版。</li>
</ol>
</details>
</article>

</div>

</section>

<section class="band" id="map" markdown="1">

<p class="eyebrow">课程目录 · 26 课</p>

## 六个 Part，推荐这个顺序

<p class="band__lede">编号是推荐的学习顺序：先有能调通的模型，再有能执行的工具和能循环的运行时，然后是外部知识和记忆，最后是让它能上线的那一圈骨架。带着具体目标来的，直接挑对应的 Part 读也行。</p>

<div class="parts" markdown="1">

<section class="part" markdown="1">
<p class="part__head" markdown="span">[Part 0 起步](lessons/README.md#part-0-起步){ .part__link }</p>
<p class="part__goal">说清三套主流调用接口的差异，跑通第一次真实调用。</p>
<ul class="part__list" markdown="1">
<li markdown="span">[<span>00</span> 起步与第一次调用](lessons/setup/README.md){ .lsn data-lesson="setup" }</li>
</ul>
</section>

<section class="part" markdown="1">
<p class="part__head" markdown="span">[Part 1 模型与上下文](lessons/README.md#part-1-模型与上下文){ .part__link }</p>
<p class="part__goal">应用能选对模型、拿到可解析的输出、接上语义检索。</p>
<ul class="part__list" markdown="1">
<li markdown="span">[<span>01</span> 模型选型与成本](lessons/how-llms-work/README.md){ .lsn data-lesson="how-llms-work" }</li>
<li markdown="span">[<span>02</span> 结构化输出与流式](lessons/model-api-structured-output-streaming/README.md){ .lsn data-lesson="model-api-structured-output-streaming" }</li>
<li markdown="span">[<span>03</span> Prompt Engineering](lessons/prompt-engineering/README.md){ .lsn data-lesson="prompt-engineering" }</li>
<li markdown="span">[<span>04</span> Embedding 与向量检索](lessons/embeddings-and-vector-search/README.md){ .lsn data-lesson="embeddings-and-vector-search" }</li>
</ul>
</section>

<section class="part" markdown="1">
<p class="part__head" markdown="span">[Part 2 Tool 与 Agent](lessons/README.md#part-2-tool-与-agent){ .part__link }</p>
<p class="part__goal">应用能自己走多步完成一个任务，执行和状态握在确定性代码手里。</p>
<ul class="part__list" markdown="1">
<li markdown="span">[<span>05</span> Tool Calling](lessons/tool-calling/README.md){ .lsn data-lesson="tool-calling" }</li>
<li markdown="span">[<span>06</span> Agent 循环与控制流](lessons/agent-loop/README.md){ .lsn data-lesson="agent-loop" }</li>
<li markdown="span">[<span>07</span> State 与 Runtime](lessons/agent-state-and-runtime/README.md){ .lsn data-lesson="agent-state-and-runtime" }</li>
<li markdown="span">[<span>08</span> Context Engineering](lessons/context-engineering-for-agents/README.md){ .lsn data-lesson="context-engineering-for-agents" }</li>
<li markdown="span">[<span>09</span> Workflow 还是 Agent](lessons/workflow-vs-agent/README.md){ .lsn data-lesson="workflow-vs-agent" }</li>
<li markdown="span">[<span>10</span> 多智能体与 Handoff](lessons/multi-agent-handoff/README.md){ .lsn data-lesson="multi-agent-handoff" }</li>
<li markdown="span">[<span>11</span> MCP](lessons/mcp/README.md){ .lsn data-lesson="mcp" }</li>
<li markdown="span">[<span>12</span> Skill 与能力分层](lessons/skills-and-capability-layers/README.md){ .lsn data-lesson="skills-and-capability-layers" }</li>
<li markdown="span">[<span>13</span> Agent Harness](lessons/agent-harness/README.md){ .lsn data-lesson="agent-harness" }</li>
</ul>
</section>

<section class="part" markdown="1">
<p class="part__head" markdown="span">[Part 3 知识与记忆](lessons/README.md#part-3-知识与记忆){ .part__link }</p>
<p class="part__goal">应用能用上不在模型权重里的知识，也知道怎么管这批数据。</p>
<ul class="part__list" markdown="1">
<li markdown="span">[<span>14</span> RAG 端到端](lessons/rag-end-to-end/README.md){ .lsn data-lesson="rag-end-to-end" }</li>
<li markdown="span">[<span>15</span> Memory](lessons/memory/README.md){ .lsn data-lesson="memory" }</li>
<li markdown="span">[<span>16</span> 数据工程](lessons/data-engineering/README.md){ .lsn data-lesson="data-engineering" }</li>
</ul>
</section>

<section class="part" markdown="1">
<p class="part__head" markdown="span">[Part 4 生产工程](lessons/README.md#part-4-生产工程){ .part__link }</p>
<p class="part__goal">一个 demo 和一个生产系统的差距，全在这一层。</p>
<ul class="part__list" markdown="1">
<li markdown="span">[<span>17</span> 系统架构与数据流](lessons/system-architecture/README.md){ .lsn data-lesson="system-architecture" }</li>
<li markdown="span">[<span>18</span> 评测](lessons/evaluation/README.md){ .lsn data-lesson="evaluation" }</li>
<li markdown="span">[<span>19</span> 可观测性](lessons/observability/README.md){ .lsn data-lesson="observability" }</li>
<li markdown="span">[<span>20</span> 可靠性与成本](lessons/reliability-cost-llmops/README.md){ .lsn data-lesson="reliability-cost-llmops" }</li>
<li markdown="span">[<span>21</span> 安全与治理](lessons/security-governance/README.md){ .lsn data-lesson="security-governance" }</li>
<li markdown="span">[<span>22</span> 微调与推理服务](lessons/model-adaptation-finetuning-inference/README.md){ .lsn data-lesson="model-adaptation-finetuning-inference" }</li>
</ul>
</section>

<section class="part" markdown="1">
<p class="part__head" markdown="span">[Part 5 产品与技术决策](lessons/README.md#part-5-产品与技术决策){ .part__link }</p>
<p class="part__goal">能独立设计一个 AI 应用，写得出一份别人能审的技术决策。</p>
<ul class="part__list" markdown="1">
<li markdown="span">[<span>23</span> 产品设计与交互](lessons/product-design-ux/README.md){ .lsn data-lesson="product-design-ux" }</li>
<li markdown="span">[<span>24</span> 语音应用](lessons/voice-agents/README.md){ .lsn data-lesson="voice-agents" }</li>
<li markdown="span">[<span>25</span> 系统设计与决策](lessons/system-design-decisions/README.md){ .lsn data-lesson="system-design-decisions" }</li>
</ul>
</section>

</div>

<p class="band__foot" markdown="span">每个 Part 的前置、能力域拆解和出师标准，还有这 26 课在搭的那个系统的全貌图，都在[课程总览](lessons/README.md)。[补充基础](prerequisites/README.md)里的 LLM 原理八篇是可选的，主线课需要时会点名引用。打开过哪一课会被记下来，下次回到这一页，顶部就有接着读的入口；每课底部另有一个「标记为已掌握」。</p>

</section>

<section class="band band--text" id="about" markdown="1">

<p class="eyebrow">关于这门课</p>

<div class="about" markdown="1">

### 课程说明

**先讲机制，再讲框架。** 每课先用普通 Python 把机制讲透，末尾才对照 LangGraph、OpenAI Agents SDK、Claude Agent SDK 各自管这件事叫什么。框架会换，这套判断不会。

**也讲怎么坏。** 每课有一节「常见错误」，讲这个机制在生产里会以什么形态坏掉；还有一节「取舍」，列的是没有标准答案、必须你自己做的判断。「一线经验」来自一个真实的语音机器人项目，没有相关经历的课直接省略。

**每课固定九节**，1～2.5 小时。示意代码二三十行，省略 import、日志和错误处理，不能直接运行——代码在这里是插图。想要能跑的项目，看[参考实现仓库](https://github.com/lance2016/ai-app-engineering-ref)。

**三种情况不适合。** 想 `git clone` 就能跑的项目，去参考实现仓库；想学训练或微调模型，这里只讲到应用工程师做决策的深度；不写代码，正文全是机制和示意代码。

**学完之后**，拿到一个线上失败案例，能定位到层：数据、检索、上下文、模型、工具、运行时、基础设施、产品，是哪一层出的问题，用什么证据排除其他层。完整的出师标准见[课程总览](lessons/README.md)。

</div>

</section>

</div>
