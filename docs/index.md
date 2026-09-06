---
hide:
  - navigation
  - toc
---

<div class="home" markdown="1">

<header class="hero" markdown="1">

<div class="hero__lede" markdown="1">

# AI Application Engineering

<p class="hero__tagline">从一次模型调用，到生产级 AI 系统</p>

讲清楚 LLM、Tool、Agent Runtime、RAG、Memory、评测、可观测性和安全在工程上到底是怎么回事——**为什么这样设计、什么时候会坏、坏了怎么办**。

写给已经会 Python 和后端、能调通模型 API，但不知道离上线还差什么的开发者。

<ul class="hero__meta">
<li>24 Lessons</li>
<li>6 Parts</li>
<li>Framework Agnostic</li>
<li>Production Oriented</li>
</ul>

<div class="hero__cta" markdown="1">

[开始学习](lessons/00-setup/README.md){ .md-button .md-button--primary }

</div>

</div>

<figure class="stackfig">
<figcaption class="stackfig__cap">THE AI APPLICATION STACK</figcaption>
<div class="stackfig__body">
<div class="stackfig__layer"><span class="stackfig__part">Part 5</span><span class="stackfig__name">Product / UX</span></div>
<div class="stackfig__layer"><span class="stackfig__part">Part 4</span><span class="stackfig__name">Production Engineering</span></div>
<div class="stackfig__layer"><span class="stackfig__part">Part 3</span><span class="stackfig__name">Knowledge &amp; Memory</span></div>
<div class="stackfig__layer"><span class="stackfig__part">Part 2</span><span class="stackfig__name">Tool &amp; Agent Runtime</span></div>
<div class="stackfig__layer stackfig__layer--base"><span class="stackfig__part">Part 1</span><span class="stackfig__name">Model &amp; Context</span></div>
</div>
<p class="stackfig__note">一个 AI 应用是一层一层搭起来的。地基在最下面，24 课从地基开始。</p>
</figure>

</header>

<section class="band band--why" markdown="1">

<p class="eyebrow">WHY THIS COURSE</p>

<div class="why">

<article class="why__item">
<p class="why__num">01</p>
<h3 class="why__head">First Principles<span>先理解机制，再理解框架</span></h3>
<p>每课先用普通 Python 把机制讲透，末尾才对照 LangGraph、OpenAI Agents SDK、Claude Agent SDK 各自管这件事叫什么。框架会换，这套判断不会。</p>
</article>

<article class="why__item">
<p class="why__num">02</p>
<h3 class="why__head">Failure Driven<span>不只讲怎么做，也讲怎么坏</span></h3>
<p>每课有一节「常见错误」，讲的是这个机制在生产环境里具体会以什么形态坏掉；还有一节「取舍」，列的是没有标准答案、必须你自己做的判断。</p>
</article>

<article class="why__item">
<p class="why__num">03</p>
<h3 class="why__head">Real Systems<span>案例来自真实系统，不是 Demo</span></h3>
<p>「一线经验」一节来自一个真实的语音机器人项目：踩了什么坑、后来怎么改的、为什么。没有相关经历的课，这一节直接省略，不编。</p>
</article>

</div>

</section>

<section class="band" id="map" markdown="1">

<p class="eyebrow">ARCHITECTURE MAP · 24 LESSONS</p>

## 课程地图

<p class="band__lede">上面那张图是系统建成之后的样子，地基在最下面。下面这张按学习顺序排，从地基开始往上搭：每读完一层，你的应用就多一层能力。</p>

<div class="amap" markdown="1">

<div class="amap__row amap__row--pre" markdown="1">
<div class="amap__idx">00</div>
<div class="amap__body" markdown="1">
<div class="amap__head" markdown="span">
[Setup](lessons/00-setup/README.md){ .amap__title }
<span class="amap__part">Part 0 · 起步</span>
</div>
<div class="amap__detail" markdown="1">
<p class="amap__lessons" markdown="span">[00](lessons/00-setup/README.md){ .amap__lesson data-lesson="00" }</p>
<p class="amap__topics">课程读法 · 最小模型调用</p>
</div>
</div>
</div>

<div class="amap__row" markdown="1">
<div class="amap__idx">01</div>
<div class="amap__body" markdown="1">
<div class="amap__head" markdown="span">
[Model &amp; Context](lessons/README.md#part-1-模型与上下文){ .amap__title }
<span class="amap__part">Part 1 · 模型与上下文</span>
</div>
<div class="amap__detail" markdown="1">
<p class="amap__lessons" markdown="span">[01](lessons/01-how-llms-work/README.md){ .amap__lesson data-lesson="01" } [02](lessons/02-model-api-structured-output-streaming/README.md){ .amap__lesson data-lesson="02" } [03](lessons/03-prompt-engineering/README.md){ .amap__lesson data-lesson="03" } [04](lessons/04-embeddings-and-vector-search/README.md){ .amap__lesson data-lesson="04" }</p>
<p class="amap__topics">模型选型 · 结构化输出与流式 · Prompt 与版本化 · Embedding 与向量检索</p>
<p class="amap__gain">应用能选对模型、拿到可解析的输出、接上语义检索。</p>
</div>
</div>
</div>

<div class="amap__row" markdown="1">
<div class="amap__idx">02</div>
<div class="amap__body" markdown="1">
<div class="amap__head" markdown="span">
[Tool &amp; Agent Runtime](lessons/README.md#part-2-tool-与-agent){ .amap__title }
<span class="amap__part">Part 2 · Tool 与 Agent</span>
</div>
<div class="amap__detail" markdown="1">
<p class="amap__lessons" markdown="span">[05](lessons/05-tool-calling/README.md){ .amap__lesson data-lesson="05" } [06](lessons/06-agent-loop/README.md){ .amap__lesson data-lesson="06" } [07](lessons/07-agent-state-and-runtime/README.md){ .amap__lesson data-lesson="07" } [08](lessons/08-context-engineering-for-agents/README.md){ .amap__lesson data-lesson="08" } [09](lessons/09-workflow-vs-agent/README.md){ .amap__lesson data-lesson="09" } [10](lessons/10-multi-agent-handoff/README.md){ .amap__lesson data-lesson="10" } [11](lessons/11-mcp/README.md){ .amap__lesson data-lesson="11" } [12](lessons/12-skills-and-capability-layers/README.md){ .amap__lesson data-lesson="12" }</p>
<p class="amap__topics">工具契约与幂等 · Agent 循环 · 状态与运行时 · 上下文组装 · Workflow 还是 Agent · 多智能体交接 · MCP · Skill 分层</p>
<p class="amap__gain">应用能自己走多步完成一个任务，执行和状态握在确定性代码手里。</p>
</div>
</div>
</div>

<div class="amap__row" markdown="1">
<div class="amap__idx">03</div>
<div class="amap__body" markdown="1">
<div class="amap__head" markdown="span">
[Knowledge &amp; Memory](lessons/README.md#part-3-知识与记忆){ .amap__title }
<span class="amap__part">Part 3 · 知识与记忆</span>
</div>
<div class="amap__detail" markdown="1">
<p class="amap__lessons" markdown="span">[13](lessons/13-rag-end-to-end/README.md){ .amap__lesson data-lesson="13" } [14](lessons/14-memory/README.md){ .amap__lesson data-lesson="14" } [15](lessons/15-data-engineering/README.md){ .amap__lesson data-lesson="15" }</p>
<p class="amap__topics">RAG 端到端 · 记忆的提取与合并 · 数据版本与新鲜度</p>
<p class="amap__gain">应用能用上不在模型权重里的知识，并且知道怎么管这批数据。</p>
</div>
</div>
</div>

<div class="amap__row" markdown="1">
<div class="amap__idx">04</div>
<div class="amap__body" markdown="1">
<div class="amap__head" markdown="span">
[Production Engineering](lessons/README.md#part-4-生产工程){ .amap__title }
<span class="amap__part">Part 4 · 生产工程</span>
</div>
<div class="amap__detail" markdown="1">
<p class="amap__lessons" markdown="span">[16](lessons/16-system-architecture/README.md){ .amap__lesson data-lesson="16" } [17](lessons/17-evaluation/README.md){ .amap__lesson data-lesson="17" } [18](lessons/18-observability/README.md){ .amap__lesson data-lesson="18" } [19](lessons/19-reliability-cost-llmops/README.md){ .amap__lesson data-lesson="19" } [20](lessons/20-security-governance/README.md){ .amap__lesson data-lesson="20" } [21](lessons/21-model-adaptation-finetuning-inference/README.md){ .amap__lesson data-lesson="21" }</p>
<p class="amap__topics">系统架构与数据流 · 评测与回归门禁 · Trace 与可观测性 · 可靠性与成本 · 安全与治理 · 微调与推理服务</p>
<p class="amap__gain">一个 demo 和一个生产系统的差距，全在这一层。</p>
</div>
</div>
</div>

<div class="amap__row" markdown="1">
<div class="amap__idx">05</div>
<div class="amap__body" markdown="1">
<div class="amap__head" markdown="span">
[Product &amp; Decisions](lessons/README.md#part-5-产品与技术决策){ .amap__title }
<span class="amap__part">Part 5 · 产品与技术决策</span>
</div>
<div class="amap__detail" markdown="1">
<p class="amap__lessons" markdown="span">[22](lessons/22-product-design-ux/README.md){ .amap__lesson data-lesson="22" } [23](lessons/23-system-design-decisions/README.md){ .amap__lesson data-lesson="23" }</p>
<p class="amap__topics">流式交互与确认撤销 · 容量估算 · 带退出条件的 ADR</p>
<p class="amap__gain">能独立设计一个 AI 应用，写得出一份别人能审的技术决策。</p>
</div>
</div>
</div>

</div>

<p class="band__foot" markdown="1">每个 Part 的前置、能力域拆解和出师标准，见[课程总览](lessons/README.md)。[前置 · LLM 原理](prerequisites/README.md)八篇是可选补充，主线课在需要时会点名引用。</p>

</section>

<section class="band" id="journey" markdown="1">

<p class="eyebrow">LEARNING JOURNEY</p>

## 你现在在哪

<p class="band__lede">选一个最接近的，下面会给出对应的推荐路线。</p>

<div class="picker" data-picker>
<button class="picker__opt" type="button" data-path="a" aria-pressed="false">
<span class="picker__key">A</span>
<span class="picker__txt">会 Python 和后端，刚开始系统学 AI Application Engineering</span>
</button>
<button class="picker__opt" type="button" data-path="b" aria-pressed="false">
<span class="picker__key">B</span>
<span class="picker__txt">已经做过 RAG / Agent / Function Calling</span>
</button>
<button class="picker__opt" type="button" data-path="c" aria-pressed="false">
<span class="picker__key">C</span>
<span class="picker__txt">正在做实际 AI 产品，更关心 Eval / Trace / Reliability / Architecture</span>
</button>
</div>

<div class="paths" markdown="1">

<article class="path" data-path="a" markdown="1">
<p class="path__label">RECOMMENDED PATH · 从地基开始，整条链走一遍</p>
<ol class="tl" markdown="1">
<li markdown="span">**先花十分钟**，读[课程总览](lessons/README.md)，知道六个 Part 各在搭什么。不确定底子够不够，对一下[能力清单](reference/foundations.md)。</li>
<li markdown="span">**从 [00 起步](lessons/00-setup/README.md)顺着读**，别跳。Part 1 到 Part 5 的顺序就是依赖顺序，前一个 Part 是后一个的地基。</li>
<li markdown="span">**卡在模型原理上再回补。** 正文出现「前置 F0x」的引用时，再去读[那八篇](prerequisites/README.md)，不用一开始就啃。</li>
<li markdown="span">**每学完一个 Part，回看[工程原则](principles/README.md)。** 12 条是全课的压缩版，先学机制再读原则，才读得进去。</li>
<li markdown="span">**想要能跑的代码**，去[参考实现仓库](https://github.com/lance2016/ai-app-engineering-ref)，七个里程碑和这门课的 Part 一一对应。</li>
</ol>
</article>

<article class="path" data-path="b" markdown="1">
<p class="path__label">RECOMMENDED PATH · 先找洞，再补课</p>
<ol class="tl" markdown="1">
<li markdown="span">**先做 [24 题自测](reference/diagnostic.md)**，二十分钟。题目按 Part 分组，答不上的那几组就是你的洞。</li>
<li markdown="span">**按结果挑 Part 读**，不用从头。做过 RAG 的人最常缺的是 Part 2 的运行时控制（[06](lessons/06-agent-loop/README.md) · [07](lessons/07-agent-state-and-runtime/README.md) · [08](lessons/08-context-engineering-for-agents/README.md)）和 Part 4 的评测（[17](lessons/17-evaluation/README.md)）。</li>
<li markdown="span">**用 [12 条工程原则](principles/README.md)对照现有项目。** 每条都有反例和正确形态，对不上的那条就去读它指向的课。</li>
<li markdown="span">**在选框架**，直接看[框架一览与选型标准](reference/frameworks.md)，不必等读完 Part 2。</li>
</ol>
</article>

<article class="path" data-path="c" markdown="1">
<p class="path__label">RECOMMENDED PATH · PRODUCTION TRACK</p>
<ol class="tl" markdown="1">
<li markdown="span">**从 [16 系统架构](lessons/16-system-architecture/README.md)开始**，先把一次请求经过哪些跳、每一跳回答什么问题摆清楚。</li>
<li markdown="span">**先建证据链，再谈优化。** [18 可观测性](lessons/18-observability/README.md)给 trace，[17 评测](lessons/17-evaluation/README.md)给「凭什么说变好了」。顺序别反：没有 trace 的评测查不出原因。</li>
<li markdown="span">**再补兜底。** [19 可靠性与成本](lessons/19-reliability-cost-llmops/README.md)讲限流、熔断、fallback 各挡哪一类失败；[20 安全与治理](lessons/20-security-governance/README.md)讲边界为什么必须由代码执行。</li>
<li markdown="span">**回头补 [08 上下文工程](lessons/08-context-engineering-for-agents/README.md)。** 线上「模型忘事」和成本尖峰，多数是这一层的问题。</li>
<li markdown="span">**最后读 [23 系统设计与技术决策](lessons/23-system-design-decisions/README.md)**，把容量估算和 ADR 补齐；原则 [07](principles/07-locate-failures-by-layer.md) · [08](principles/08-no-eval-no-improvement.md) · [09](principles/09-trace-is-first-class.md) · [10](principles/10-cost-and-latency-are-design-constraints.md) 是这条路线的压缩版。</li>
</ol>
</article>

</div>

</section>

<section class="band" id="progress" markdown="1">

<p class="eyebrow">YOUR PROGRESS</p>

<div class="prog" data-progress>
<p class="prog__empty">还没有标记过任何一课。每一课页面的底部有一个「标记为已掌握」，记录只存在这台设备的浏览器里——不上传，不需要登录，换设备不同步。</p>
<div class="prog__body" hidden>
<p class="prog__count"><strong data-prog-done>0</strong><span class="prog__total">/ 24 Lessons</span></p>
<div class="prog__ruler" data-prog-ruler></div>
<p class="prog__last">LAST · <a data-prog-last href="#"></a></p>
<p class="prog__next"><a class="md-button md-button--primary" data-prog-next href="#">Continue Learning →</a></p>
<p class="prog__reset"><button type="button" data-prog-reset>清除本机记录</button></p>
</div>
</div>

</section>

<section class="band" id="system" markdown="1">

<p class="eyebrow">BUILD THE SYSTEM</p>

## 24 课在搭同一个系统

<p class="band__lede">这不是 24 个孤立的知识点。下面是一个生产级 AI 应用的全貌，每个组件后面标着它属于哪个 Part——学完一个 Part，这张图上就多亮一块。</p>

<div class="sys" markdown="1">

<div class="sys__band" markdown="1">
<p class="sys__bandname">01<span>请求入口</span></p>
<div class="sys__nodes" markdown="span">
[User<span>P5 · 22</span>](lessons/22-product-design-ux/README.md){ .sysnode }<span class="sys__arrow" aria-hidden="true"></span>[API<span>P4 · 16</span>](lessons/16-system-architecture/README.md){ .sysnode }<span class="sys__arrow" aria-hidden="true"></span>[Session<span>P2 · 07</span>](lessons/07-agent-state-and-runtime/README.md){ .sysnode }
</div>
</div>

<div class="sys__band" markdown="1">
<p class="sys__bandname">02<span>运行时</span></p>
<div class="sys__nodes" markdown="span">
[Context Builder<span>P2 · 08</span>](lessons/08-context-engineering-for-agents/README.md){ .sysnode }<span class="sys__arrow" aria-hidden="true"></span>[Agent Runtime<span>P2 · 06 07 09</span>](lessons/06-agent-loop/README.md){ .sysnode .sysnode--core }<span class="sys__arrow" aria-hidden="true"></span>[Tool Registry<span>P2 · 05 11 12</span>](lessons/05-tool-calling/README.md){ .sysnode }<span class="sys__arrow" aria-hidden="true"></span>[Model Gateway<span>P1 · 01 02</span>](lessons/02-model-api-structured-output-streaming/README.md){ .sysnode }
</div>
<div class="sys__aside" markdown="span">
[Fallback / Degrade<span>P4 · 19</span>](lessons/19-reliability-cost-llmops/README.md){ .sysnode .sysnode--risk }
<span class="sys__asidenote">下游超时、限流、模型不可用，走这条线</span>
</div>
</div>

<div class="sys__band sys__band--async" markdown="1">
<p class="sys__bandname">03<span>知识与记忆</span></p>
<div class="sys__nodes" markdown="span">
[RAG<span>P3 · 13</span>](lessons/13-rag-end-to-end/README.md){ .sysnode .sysnode--async }<span class="sys__dot" aria-hidden="true"></span>[Memory<span>P3 · 14</span>](lessons/14-memory/README.md){ .sysnode .sysnode--async }<span class="sys__dot" aria-hidden="true"></span>[Data Pipeline<span>P3 · 15</span>](lessons/15-data-engineering/README.md){ .sysnode .sysnode--async }<span class="sys__dot" aria-hidden="true"></span>[Vector Index<span>P1 · 04</span>](lessons/04-embeddings-and-vector-search/README.md){ .sysnode .sysnode--async }
</div>
<p class="sys__bandnote">虚线：被运行时按需调用，或者离线跑。它们不在主请求链上，但决定了回答的上限。</p>
</div>

<div class="sys__band sys__band--base" markdown="1">
<p class="sys__bandname">04<span>平台底座</span></p>
<div class="sys__nodes" markdown="span">
[Evaluation<span>P4 · 17</span>](lessons/17-evaluation/README.md){ .sysnode }<span class="sys__dot" aria-hidden="true"></span>[Trace<span>P4 · 18</span>](lessons/18-observability/README.md){ .sysnode }<span class="sys__dot" aria-hidden="true"></span>[Observability<span>P4 · 18</span>](lessons/18-observability/README.md){ .sysnode }<span class="sys__dot" aria-hidden="true"></span>[Security<span>P4 · 20</span>](lessons/20-security-governance/README.md){ .sysnode }<span class="sys__dot" aria-hidden="true"></span>[Infrastructure<span>P4 · 19 21</span>](lessons/21-model-adaptation-finetuning-inference/README.md){ .sysnode }
</div>
<p class="sys__bandnote">横切：每一层都要用到。缺了它，上面三层出了问题你只能看到最后那句错误回答。</p>
</div>

</div>

<div class="legend" markdown="1">
<p class="eyebrow eyebrow--sub">VISUAL LANGUAGE</p>
<p class="legend__lede">全站的示意图共用一套约定，看图之前不用先读图例。</p>
<ul class="legend__list">
<li><span class="lg lg--celadon"></span>青瓷色：当前路径、正常流程</li>
<li><span class="lg lg--rust"></span>铁锈色：失败、风险、降级</li>
<li><span class="lg lg--solid"></span>实线：运行时的同步流</li>
<li><span class="lg lg--dashed"></span>虚线：可选调用、异步或离线</li>
<li><span class="lg lg--rect"></span>矩形：一个组件</li>
<li><span class="lg lg--circle"></span>圆形：一个概念</li>
<li><span class="lg lg--diamond"></span>菱形：一次判断</li>
</ul>
</div>

</section>

<section class="band band--text" markdown="1">

<div class="cols" markdown="1">

<div class="cols__col" markdown="1">

### 每一课长什么样

固定九节：**为什么需要** → **心智模型** → **机制拆解** → **常见错误** → **取舍** → **工程落地** → **框架映射** → **一线经验** → **练习**。每课 1～2.5 小时。

**代码是插图。** 示意代码二三十行，省略 import、日志和错误处理，不能直接运行。想要能跑的，看[参考实现仓库](https://github.com/lance2016/ai-app-engineering-ref)。

**每课都留一块能进评测集的东西。** 「工程落地」的最后一条固定是「怎么测」，评测不是第 17 课才开始的事。

</div>

<div class="cols__col" markdown="1">

### 这门课适合谁

停在「demo 能跑」，不知道离上线还差什么——缺的那一圈骨架就是 Part 4。

在用 LangChain 或 LangGraph，说不清框架替你做了什么——每课用普通 Python 讲同一个机制，末尾对照三个框架的叫法。

要做架构评审或技术选型——[课程总览](lessons/README.md)的能力域清单加 [12 条工程原则](principles/README.md)就是判断依据。

**三种情况不适合。** 想要 `git clone` 就能跑的项目，去[参考实现仓库](https://github.com/lance2016/ai-app-engineering-ref)；想学训练或微调模型，这里只讲到应用工程师做决策的深度；不写代码，正文全是机制和示意代码。

</div>

</div>

<div class="outcome" markdown="1">

### 学完之后

拿到一个需求，能独立走完从「该不该用 AI 做」到「用户看到什么」的整条链。拿到一个线上失败案例，能定位到层：数据、检索、上下文、模型、工具、运行时、基础设施、产品，是哪一层出的问题，用什么证据排除其他层。

完整的出师标准见[课程总览](lessons/README.md)。

</div>

</section>

</div>
