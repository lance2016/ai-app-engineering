<p align="center">
  <img src=".github/assets/banner.png" alt="AI Application Engineering：From LLM Calls to Production Agent Systems" width="100%">
</p>

# AI 应用开发工程师：从入门到精通

> 面向有后端开发经验的工程师。用一个贯穿全程的真实项目，讲清楚怎样把 LLM 从「能调用」做成「可上线的 Agent 系统」。
> 中文写作。主线不绑定任何 Agent 框架，先用普通 Python 看清机制，再在 Framework Lab 里用三个主流框架对照。正文里的事故案例，一部分来自作者的语音机器人生产项目。

**状态：第一版正文已就位，正在补实践闭环。** 各部分的完成度见 [进展与待办](#进展与待办)，具体待办见 [TODO.md](./TODO.md)。

## 快速上手

四种跑法，由浅到深。前三种不需要任何 API Key。

**1. 五分钟离线跑通**：只要 uv 和 Python 3.12，所有课程代码和主项目都用内置的 fake 模型。

```bash
git clone <this-repo> && cd ai-app-engineering
uv sync
uv run python lessons/00-setup/code/01_hello_fake_adapter.py   # 第一课的第一个例子
uv run pytest tests/project/m1 -q                               # 主项目 M1 的验收测试，16 passed
uv run pytest -q                                                # 全部课程代码 + 项目测试，不需要数据库的部分
```

**2. 一条命令起 Playground**：只想点点看效果、不改代码，用这条。Docker 把 PostgreSQL、Redis、Phoenix 和服务本身一起起来，数据落在真实数据库里，重启不丢。

```bash
docker compose --profile full up -d --build --wait
open http://localhost:8000/playground        # 新建对话、看事件流、批准工具、导入文档、查记忆
open http://localhost:6006                   # Phoenix：看这次请求的 trace
docker compose --profile full down           # 用完清理；加 -v 连数据卷一起删
```

默认用离线的 fake 模型，Token 用开发模式默认值 `dev-token`。要接真实模型，`cp .env.example .env` 填好 `DEEPSEEK_API_KEY` 后再执行第一条命令，`MODEL_PROVIDER=deepseek` 会从 `.env` 里读到。这个 profile 默认不随 `docker compose up` 启动，不会和下面第 3 种跑法抢 8000 端口。

**3. 起依赖，本机跑代码**：要改 `project/src/` 就用这种，改完直接重启本机进程，不用重新 build 镜像。

```bash
cp .env.example .env                       # MODEL_PROVIDER 默认 fake；要接真实模型就填 DEEPSEEK_API_KEY
docker compose up -d --wait                # postgres(pgvector) + redis + phoenix
export DATABASE_URL=postgresql+asyncpg://aiapp:aiapp@localhost:5432/aiapp
export REDIS_URL=redis://localhost:6379/0
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:6006
uv run alembic -c project/src/aiapp/storage/alembic.ini upgrade head
uv run uvicorn aiapp.api.app:create_app --factory --port 8000
```

打开 [http://localhost:8000/playground](http://localhost:8000/playground) 用页面对话，或者另开一个终端用 curl：

```bash
curl -s -X POST localhost:8000/v1/threads -H "Authorization: Bearer dev-token" -H "Content-Type: application/json" -d '{}'
curl -N -X POST localhost:8000/v1/threads/<thread_id>/messages -H "Authorization: Bearer dev-token" \
     -H "Content-Type: application/json" -d '{"content": "hello"}'          # SSE 事件流
```

完整接口和每个里程碑的运行步骤见 [project/README.md](./project/README.md)。

**4. 一条命令起生产形态**：镜像里没有密钥，token 从环境变量来，生产模式拒绝默认 token 和内存存储。

```bash
AIAPP_TOKENS=mytoken:tenant-a docker compose -f docker-compose.prod.yml up --build
```

想看生产工程那几课的效果，有两个现成脚本：`uv run python scripts/eval_run.py` 跑评测门禁，`uv run python scripts/chaos.py --all` 跑六个故障演练。都不需要 key。

## 这门课和别的有什么不同

| 已有资源 | 它的侧重 | 本课补什么 |
|---|---|---|
| [12-factor-agents](https://github.com/humanlayer/12-factor-agents) | 12 条 Agent 工程原则 | 原则怎么落到一个真实项目里 |
| [ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) | Agent 知识地图，示例绑 Azure | 不绑云厂商，加评测、可观测、成本、安全的生产视角 |
| [langchain-academy](https://github.com/langchain-ai/langchain-academy) | LangGraph 的 State / Graph / Checkpoint | 用普通 Python 讲同样的机制，读者再选框架 |
| [generative-ai-for-beginners](https://github.com/microsoft/generative-ai-for-beginners) | GenAI 应用通识 | 通识压进前置，主线直接从应用工程切入 |
| [llm-course](https://github.com/mlabonne/llm-course)、[LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) | 模型原理与训练 | 只取应用工程师需要的那一层，作为前置 F 组 |

## 学习路线

<p align="center">
  <img src=".github/assets/roadmap.png" alt="AI Application Engineering 学习路线图：前置基础、AI 应用主线、生产工程、架构与决策、框架与选型、实战项目" width="100%">
</p>

整门课就是一条线：**学一段课，往同一个项目里加一块能力**。六个阶段按顺序走，每个阶段学什么、做什么、做完的标志是什么，都在这一张表里。

| 阶段 | 学（课程） | 做（主项目） | 做完的标志 |
|---|---|---|---|
| 1 前置基础 | [prerequisites/](./prerequisites/README.md)：Python 语言与后端工程 P00～P07、B00～B04、算法 A00～A06、LLM 原理 F00～F07 | M0 并发实验（学到 P07 asyncio 时做） | 前置 README 里的自检全部能打勾 |
| 2 AI 应用主线 | 第 00～04 课 模型与上下文 | M1 API 骨架 | 服务能接一个模型，流式返回，错误有结构 |
|  | 第 05～12 课 Tool 与 Agent | M2 数据与状态、M3 Tool Workflow | Agent 能调工具、能停下等人确认、kill 掉能续跑 |
|  | 第 13～15 课 知识与记忆 | M4 RAG 与 Memory | 回答带引用，Recall@k 有数字，记忆能提取能删除 |
| 3 生产工程 | 第 16～21 课 | M5 生产化 | 评测门禁、trace、限流与 fallback、容器化全部就位 |
| 4 架构与决策 | 第 22～23 课 | M6 综合设计 | 写出一份多租户平台的 RFC |
| 5 框架与选型 | [Framework Lab](./project/framework-lab/README.md)：同一需求用纯 Python、LangGraph、OpenAI Agents SDK、Claude Agent SDK 各做一遍 | 三个框架实现通过同一套一致性测试 | 十二维评分卡填满，能说清选某个框架的理由 |
| 6 实战项目 | [Capstone](./project/capstones/README.md) 四选一 | 一个完整系统 | 过验收清单，评分量表拿到分 |

几点说明：

- 第 05～12 课和第 13～15 课没有硬依赖，可以先学任一段。阶段 3 需要两段都学完。
- Framework Lab 在 M3 之后就能开始，那时你刚用普通 Python 写过同样的东西，对照最清楚。但评分卡里 Observability、Deployment 两格要学完第 18、19 课才打得出来，所以默认放在阶段 5 一次做完。
- 评测、安全、可观测、成本四件事不是等到阶段 3 才碰，从 M1 起每个里程碑都带最小版本。
- [principles/](./principles/README.md) 的 12 条原则不占阶段，它是贯穿全课的对照清单，每课的正文都会指回其中一两条。

**三种起点**

| 你是 | 从哪开始 |
|---|---|
| 零基础 | 阶段 1 从 P00 开始按顺序学 |
| 有后端经验，没碰过 LLM | 做一遍 [前置自检](./prerequisites/README.md#自检)，通常只需要补 F 组，然后进第 00 课 |
| 已经在做 Agent 项目 | 直接从第 05 课进，把 12 条原则当对照清单，主项目从 M2 开始补 |

阶段依赖图和 L0～L5 能力阶梯的自评标准见 [ROADMAP.md](./ROADMAP.md)。

## 仓库结构

学习者只需要关心前两组目录。第三组是查资料用的，第四组只有维护者和贡献者才会碰。

```text
.
│  ── 学 ──────────────────────────────────────────────────────────
├── prerequisites/          前置，零基础读者的起点，独立于主线
│   ├── python/             P00–P07 Python 语言
│   ├── backend/            B00–B04 后端工程：HTTP 与 FastAPI、SQL、测试、Git 与 Docker、Redis
│   ├── algorithms/         A00–A06 算法，每篇从一个真实工程问题进入
│   └── llm-foundations/    F00–F07 LLM 原理，只到应用工程师能做决策的深度
├── lessons/                主线 24 课 00–23，每课 README + code/ + exercises.md
├── principles/             12 条工程原则，一条一个文件，贯穿全课的对照清单
│
│  ── 做 ──────────────────────────────────────────────────────────
├── project/                贯穿全程的主项目，一个 AI 应用服务
│   ├── src/aiapp/          全部服务代码都在这里，按 adapters / runtime / tools / knowledge / storage / api / ops 分包
│   ├── m0-concurrency/ … m6-platform-design/   七个里程碑，每个目录只有说明、运行步骤和验收证据
│   ├── framework-lab/      阶段 5：baseline 与三个框架实现，加一致性测试
│   ├── capstones/          阶段 6：四个实战题目
│   ├── eval/               评测数据：golden set、判分校准、阈值与基线
│   └── skills/             项目用到的 Skill 示例
│
│  ── 查 ──────────────────────────────────────────────────────────
├── reference/              术语表、技术选型、外部资料
├── ROADMAP.md              阶段依赖图与 L0～L5 能力阶梯
│
│  ── 维护 ────────────────────────────────────────────────────────
├── tests/                  所有 code/ 的 smoke test，和按里程碑组织的验收测试
├── scripts/                状态同步、链接与模板检查、评测门禁、故障演练
├── templates/              课程 README 的写作模板
├── TODO.md · AGENTS.md · CONTRIBUTING.md   待办、AI 协作者说明、贡献方式
└── .github/                CI 配置与 README 用到的图片
```

编号只表示学习顺序：`P` / `B` / `A` / `F` 是四组前置模块，`00～23` 是主线课，`M0～M6` 是项目里程碑，课程总表里的 `Part 0～5` 只是把 24 课分成六组方便对照。它们都不会在末尾追加编号塞新主题。

本地跑起来只需要 uv 和 Python 3.12，依赖 PostgreSQL 与 Redis 的部分用 `docker compose up -d` 起。所有示例默认走离线的 fake 模型，接真实模型的方法见 [第 00 课](./lessons/00-setup/README.md)。

## 课程总表

前置模块见 [prerequisites/README.md](./prerequisites/README.md)，有后端经验的人做完那里的自检可以直接跳过。

状态：`outline` 只有目标和心智模型 · `draft` 有代码，缺练习、反例或项目落点 · `complete` 正文完整、代码能跑、有失败注入、练习有答案、有项目落点、CI 能验证。

| # | 课程 | 一句话 | 状态 |
|---|---|---|---|
| **Part 0 起步** | | | |
| 00 | [环境与模型接入](./lessons/00-setup/README.md) | 搭好 uv + Python 3.12 环境，接入一个真实模型和一个 fake adapter，让后面每一课的代码都能离线跑 | complete |
| **Part 1 模型与上下文** | | | |
| 01 | [从模型到应用：能力边界、成本模型与选型](./lessons/01-how-llms-work/README.md) | 把模型当有规格书的部件：硬约束过滤、能力探针、每段对话的成本模型、幻觉的应用层对策、可替换性 | complete |
| 02 | [模型调用、结构化输出与流式](./lessons/02-model-api-structured-output-streaming/README.md) | 把一次模型调用拆开：消息格式、参数、JSON Schema 约束输出、流式增量、重试与成本记录 | complete |
| 03 | [Prompt Engineering 与单次调用的上下文](./lessons/03-prompt-engineering/README.md) | 系统指令、few-shot、输出约束、prompt 版本化与测试；一次调用的上下文里该放什么、不该放什么 | complete |
| 04 | [Embedding 与向量检索基础](./lessons/04-embeddings-and-vector-search/README.md) | 选 embedding 模型和维度、暴力检索到什么规模换索引、切块怎样改变召回、pgvector 建表建索引 | complete |
| **Part 2 Tool 与 Agent** | | | |
| 05 | [Tool Calling：从 Schema 到副作用](./lessons/05-tool-calling/README.md) | 工具调用成功包含三件事：模型选对工具、参数有效、外部系统真的完成 | complete |
| 06 | [Agent 循环与控制流](./lessons/06-agent-loop/README.md) | 观察、决策、行动的最小循环；停止条件、步数与预算、失败分类与对应的恢复动作 | complete |
| 07 | [Agent State 与 Runtime：持久化、暂停恢复与人工介入](./lessons/07-agent-state-and-runtime/README.md) | 状态模型（对话、任务、业务、记忆）、checkpoint 与持久化、launch / pause / resume、人工确认与中断、事件流、重复消息与并发、幂等重入 | complete |
| 08 | [Agent 的 Context Engineering](./lessons/08-context-engineering-for-agents/README.md) | 运行时怎样组装每一轮的上下文：系统指令、历史裁剪与压缩、工具结果注入、检索结果、渐进式披露、子 Agent 上下文隔离、缓存友好的布局 | complete |
| 09 | [Workflow 还是 Agent：架构模式](./lessons/09-workflow-vs-agent/README.md) | Prompt chaining、Routing、Parallelization、Orchestrator-Workers、Evaluator-Optimizer 五种模式，Planner / Executor，以及什么时候才需要自治 Agent | complete |
| 10 | [多智能体、Handoff 与 Racing](./lessons/10-multi-agent-handoff/README.md) | 多个 Agent 如何分工、交接和并行竞速；状态归谁、历史怎么隔离、失败怎么回退 | complete |
| 11 | [MCP：模型上下文协议](./lessons/11-mcp/README.md) | MCP 解决「能力怎么接入」：初始化、能力发现、resources / tools / prompts、权限与断连处理 | complete |
| 12 | [Skill 与能力生态分层](./lessons/12-skills-and-capability-layers/README.md) | Tool、MCP、Skill、Plugin、Agent 协议各管什么；Skill 如何封装可复用的使用方法 | complete |
| **Part 3 知识与记忆** | | | |
| 13 | [RAG 端到端](./lessons/13-rag-end-to-end/README.md) | 解析、切块、索引、混合检索、重排、生成、引用，七步每步怎么坏、怎么测 | complete |
| 14 | [Memory：提取、整合与检索](./lessons/14-memory/README.md) | 会话记忆、任务记忆、长期记忆的边界；记忆的提取、冲突合并、过期和删除 | complete |
| 15 | [数据工程与数据质量](./lessons/15-data-engineering/README.md) | 文档解析、ETL、版本、新鲜度、权限和删除，决定 RAG 上限的不是模型而是数据 | complete |
| **Part 4 生产工程** | | | |
| 16 | [AI 应用系统架构与端到端数据流](./lessons/16-system-architecture/README.md) | 从客户端到模型再回来的一条完整请求链：网关、会话、状态、工具、检索、流式、持久化、后台任务 | complete |
| 17 | [评测：Golden Set、LLM Judge 与 Agent Eval](./lessons/17-evaluation/README.md) | 没有评测集就没有「变好了」 | complete |
| 18 | [可观测性：从日志到 LLM Trace](./lessons/18-observability/README.md) | 结构化日志、OpenTelemetry GenAI 语义约定、Phoenix / Langfuse 接入，四个故障实验 | complete |
| 19 | [可靠性、成本、部署与 LLMOps](./lessons/19-reliability-cost-llmops/README.md) | 超时、重试、限流、熔断、Fallback、模型路由、成本预算、SLO、故障演练；容器化、CI、配置与密钥、灰度与回滚 | complete |
| 20 | [安全与治理](./lessons/20-security-governance/README.md) | 提示注入、越权、数据泄露、沙箱、供应链、多租户边界、数据生命周期 | complete |
| 21 | [模型适配、微调与推理服务](./lessons/21-model-adaptation-finetuning-inference/README.md) | 什么时候该微调、LoRA 怎么工作、量化和 KV Cache 如何影响延迟显存、vLLM 与本地推理的取舍 | complete |
| **Part 5 架构与产品** | | | |
| 22 | [AI 产品设计与交互](./lessons/22-product-design-ux/README.md) | 何时该用 AI、人工基线、流式 UI、引用展示、确认与撤销、转人工、指标与反馈闭环 | complete |
| 23 | [系统设计与技术决策](./lessons/23-system-design-decisions/README.md) | Build vs Buy、模型 vs RAG、Workflow vs Agent、单体 vs 平台；一道多租户知识库 + 任务 Agent 的综合设计题 | complete |
| **Lab** | | | |
| Lab | [Framework & Architecture Lab](./project/framework-lab/README.md) | 同一个审批型 Agent 需求在 LangGraph、OpenAI Agents SDK、Claude Agent SDK 上各做一遍，一致性测试加十二维评分卡；M3 之后可开始，Part 4 学完再做完整一遍 | draft |
| **Capstone** | | | |
| Cap | [Capstone 实战](./project/capstones/README.md) | Production Agent Service、RAG + Memory Agent、Long-running Durable Agent、Multi-tenant AI Platform 四个实战，各有可执行验收与评分量表 | outline |

## 主项目

<p align="center">
  <img src=".github/assets/architecture.png" alt="AI 应用服务骨架：FastAPI、Agent Runtime、Context Builder、Model Adapter、Tool Runner / MCP、RAG、Memory、PostgreSQL + pgvector、Redis、Observability、Evaluation、Background Jobs、Deployment" width="100%">
</p>

[AI 应用服务骨架](./project/README.md)：一个不绑定模型供应商的 AI 应用后端。从 asyncio 实验开始，七个里程碑，每个只加一个能力簇，最终长成上图这样带工具、RAG、Memory、评测、可观测性、安全护栏和部署的生产级服务。代码全部在 `project/src/aiapp/`，里程碑目录只放说明和验收。

| 里程碑 | 加什么 |
|---|---|
| M0 并发实验 | 串行、并发、限并发、取消、超时五个对照实验 |
| M1 API 骨架 | FastAPI、鉴权、SSE 流式、结构化错误、system prompt 版本化 |
| M2 数据与状态 | PostgreSQL 表与迁移、Redis 状态、checkpoint 与 resume |
| M3 Tool Workflow | 工具契约、确认与幂等、失败恢复、最小 trace、MCP 与 Skill |
| M4 RAG 与 Memory | 混合检索、引用、Recall@k、记忆提取与删除演练 |
| M5 生产化 | Golden set 回归、OpenTelemetry、限流、Fallback、成本统计、故障演练、容器化 |
| M6 综合设计 | 多租户平台的 RFC：容量、威胁模型、模型与推理选型、迁移与退出 |

每课的「对照真实项目」小节都指向这里。哪一课对应哪个里程碑的哪一块，见 project/README.md 里的[课程到项目的映射表](./project/README.md#课程到项目的映射)。

## 原则

[12 条 AI 应用工程原则](./principles/README.md)。前 6 条和 12-factor-agents 重合，后 6 条是生产视角的补充。已经在做 Agent 项目的人可以把它当对照清单。

## 学每一课的固定动作

1. 先跑 `code/`，再读正文。代码默认用离线的 fake 模型，需要真实模型时按第 00 课配一个 DeepSeek key。
2. 做练习，做完再看 `exercises.md` 里折叠的答案。
3. 看「对照真实项目」小节，去 `project/` 里落一个增量。不动手不算学完。

## 参考资料

术语见 [reference/glossary.md](./reference/glossary.md)，工具选型见 [reference/stack.md](./reference/stack.md)，外部资料见 [reference/resources.md](./reference/resources.md)。

## 进展与待办

截至 2026-09-04 的完成度。状态以各单元 README 的 frontmatter 为准，总表的状态列由 `scripts/sync_status.py` 生成。

| 内容 | 现状 |
|---|---|
| 主线 24 课 | 全部 `complete`：正文、可运行代码、失败注入、带答案的练习、项目落点 |
| 12 条原则 | 全部 `complete` |
| 前置 Python P00～P07、后端 B00～B04 | 除 B04 Redis 只有大纲外全部 `complete` |
| 前置 LLM 原理 F00～F07 | 6 篇带实验的 `draft`，F02、F07 还是大纲 |
| 前置算法 A00～A06 | 全部大纲 |
| 主项目 M0～M6 | M0～M5 有代码和 `tests/project/mN` 验收测试；M6 是设计型里程碑，`draft` |
| Framework Lab | baseline 和 LangGraph 实现通过 8 个一致性场景；OpenAI Agents SDK、Claude Agent SDK、spec、评分卡待做 |
| Capstone | 四个题目只有大纲 |

下一步按优先级排在 [TODO.md](./TODO.md)：先补完 Framework Lab，再补 Capstone，然后是前置新内容和模板回填。做完一项删一项。

CI 在每次提交上跑七件事：相对链接检查、`complete` 单元的模板检查、状态列与 frontmatter 一致性、数据库迁移的升级回滚、所有示例代码离线运行加项目验收测试、评测门禁、故障演练；最后构建生产镜像并验证启动守卫。配置见 [.github/workflows/ci.yml](./.github/workflows/ci.yml)。

## 给 AI 协作者

这个仓库的大部分正文会由 AI 在人工指导下逐课生成。**新开一个会话续写内容时，先读 [AGENTS.md](./AGENTS.md)**，它说明了目录约定、每课的写作流程、参考仓库的用法和质量门槛。不读它就动手，多半会破坏编号规则或写出和别的课重复的内容。

## 贡献与许可

贡献方式见 [CONTRIBUTING.md](./CONTRIBUTING.md)。文档采用 CC BY-NC-SA 4.0，代码采用 MIT，见 [LICENSE](./LICENSE)。
