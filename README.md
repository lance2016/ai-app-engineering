<p align="center">
  <img src=".github/assets/banner.png" alt="AI Application Engineering：From LLM Calls to Production Agent Systems" width="100%">
</p>

# AI Application Engineering

## 从模型调用，到生产级 Agent 系统

面向开发者的中文开源系统课程：用普通 Python 看清 LLM、Tool、Runtime、RAG、Memory 和框架的机制，再把它们装进一个可测试、可观测、可恢复的 AI 应用服务。

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![CI](https://github.com/lance2016/ai-app-engineering/actions/workflows/ci.yml/badge.svg)](https://github.com/lance2016/ai-app-engineering/actions/workflows/ci.yml)
[![Lessons](https://img.shields.io/badge/lessons-24-0EA5E9)](./lessons/)
[![中文](https://img.shields.io/badge/language-中文-8B5CF6)](./README.md)
[![License](https://img.shields.io/github/license/lance2016/ai-app-engineering)](./LICENSE)

**Models · Agents · RAG · MCP · Evaluation · Observability · Production**

- **先看机制，再做选型**：主线不绑定 Agent 框架，代码默认走 fake model，离线即可运行。
- **一条项目线贯穿到底**：从 FastAPI 和 SSE，到状态、工具、MCP、RAG、Memory、评测、trace、可靠性和安全。
- **把失败当成课程内容**：每个关键能力都配有测试、evaluation gate、failure injection 或 chaos drill。
- **学习结果可展示**：最终不是一组 notebook，而是一套可以在 Playground 里运行、在 Phoenix 里解释、在 GitHub 上交付的服务。

## 最后你会做出什么

一个带真实工程边界的 Production Agent Service：

```text
用户 → FastAPI / SSE → Agent Runtime → Context Builder → Model Adapter
                         ├─ Tool Calling / MCP → approval → idempotent side effect
                         ├─ RAG + citations / Memory lifecycle
                         ├─ checkpoint / resume / human-in-the-loop
                         └─ Evaluation / OpenTelemetry → Phoenix

PostgreSQL + pgvector · Redis · fallback · cost budget · security · deployment
```

主项目的入口是 [project/README.md](./project/README.md)，可以直接打开 Playground；完整 Demo 录制清单和媒体命名规范见 [reference/demo-recording.md](./reference/demo-recording.md)。当前仓库只提交真实存在的图片，`.github/assets/demo/` 预留给后续录制，不用占位截图冒充成品。

## 你应该从哪里开始

| 入口 | 适合谁 | 第一站 |
|---|---|---|
| **Beginner / 基础不足** | Python、HTTP、SQL 或 asyncio 还不熟 | [Prerequisites 自检](./prerequisites/README.md)，按缺口补 P / B / A / F |
| **Backend Engineer** | 会写后端服务，想系统进入 AI 应用工程 | 做 [Prerequisites 自检](./prerequisites/README.md#自检)，然后从 [00 环境与模型接入](./lessons/00-setup/README.md) 开始 |
| **Existing AI / Agent Developer** | 已经调过模型或写过 Agent | 从 [05 Tool Calling](./lessons/05-tool-calling/README.md)、[19 生产工程](./lessons/19-reliability-cost-llmops/README.md) 或 [Framework Lab](./project/framework-lab/README.md) 选入口 |

## 最短 Quick Start

默认不需要 API Key；四步后应看到 fake adapter 的输出。

如果还没有 `uv`：macOS / Linux 运行 `curl -LsSf https://astral.sh/uv/install.sh | sh`，Windows PowerShell 运行 `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`，然后重新打开终端。

```bash
git clone https://github.com/lance2016/ai-app-engineering.git
cd ai-app-engineering
uv sync
uv run python lessons/00-setup/code/01_hello_fake_adapter.py
```

接着可以运行 `uv run pytest tests/project/m1 -q` 看主项目验收，或查看 [第 00 课](./lessons/00-setup/README.md) 了解如何切换真实模型。完整 Docker / 本机开发 / 生产形态见[完整运行方式](#完整运行方式)。

## 学习路径：八个 Stage

```mermaid
flowchart LR
    S0[Stage 0<br/>Foundation] --> S1[Stage 1<br/>LLM Application]
    S1 --> S2[Stage 2<br/>Agent]
    S2 --> S3[Stage 3<br/>Knowledge & Memory]
    S3 --> S4[Stage 4<br/>Production]
    S4 --> S5[Stage 5<br/>Architecture & Product]
    S5 --> S6[Stage 6<br/>Framework Lab]
    S6 --> S7[Stage 7<br/>Capstone]
    S2 -. M3 后可提前 .-> S6
```

| Stage | 学什么 | 做什么 | 完成信号 |
|---|---|---|---|
| 0 Foundation | Prerequisites + 00 | P / B / A / F 自检，M0 并发实验 | 能独立跑代码，理解 token、窗口、async 和 HTTP |
| 1 LLM Application | 01–04 | M1 API 骨架 | 有 schema、流式、错误、成本和模型适配器 |
| 2 Agent | 05–12 | M2 状态、M3 Tool Workflow | 能暂停、恢复、批准工具，处理失败和重复消息 |
| 3 Knowledge & Memory | 13–15 | M4 RAG 与 Memory | 有引用、Recall@k、版本更新和可审计删除 |
| 4 Production | 16–21 | M5 生产化 | 有评测门禁、trace、限流、fallback、预算、部署和安全护栏 |
| 5 Architecture & Product | 22–23 | M6 综合设计 | 能把交互、容量、威胁模型和退出条件写进 RFC |
| 6 Framework Lab | 同一需求的 baseline / 三框架对照 | 跑一致性测试，填 12 维评分卡 | 能用证据解释框架适配度和 lock-in |
| 7 Capstone | 一个完整交付题 | 先做 Production Agent Service reference capstone | 有代码、测试、eval、trace、runbook 和 demo |

### 两种学习模式

**📖 阅读模式**：心智模型 → 核心机制 → 常见失败 → 生产方案 → 框架映射 → 真实项目。适合已有开发经验、想先搭建全局理解的人。

**🛠 实战模式**：code → failure injection → exercises → project milestone → tests。适合希望留下运行证据、把每课变成项目增量的人。两种模式可以随时切换，不要求做完练习才继续阅读。

后面的每一课都保留这两条路径的提示；课程正文的固定结构见 [templates/lesson-README.md](./templates/lesson-README.md)。

## Playground / Architecture / Trace

主项目已经提供可操作的 Playground：对话、SSE 事件流、工具确认、文档导入、检索和 Memory 都通过同一套 `/v1` 接口完成。架构图见下方，Phoenix trace 在本地启动 full profile 后可查看。

| 你想看什么 | 入口 |
|---|---|
| 可运行的服务与 UI | [project/README.md](./project/README.md) |
| 主项目架构 | [.github/assets/architecture.png](./.github/assets/architecture.png) |
| 课程与能力路径 | [ROADMAP.md](./ROADMAP.md) |
| Demo 录制计划 | [reference/demo-recording.md](./reference/demo-recording.md) |

## 完整运行方式

四种跑法，由浅到深；前三种不需要任何 API Key。

**1. 五分钟离线验收**：

```bash
uv run pytest tests/project/m1 -q
uv run pytest -q
```

**2. 一条命令起 Playground**：Docker 会启动 PostgreSQL、Redis、Phoenix 和服务本身。默认仍是 fake model，Token 是开发模式默认值 `dev-token`。

```bash
docker compose --profile full up -d --build --wait
```

打开 [http://localhost:8000/playground](http://localhost:8000/playground) 操作服务，[http://localhost:6006](http://localhost:6006) 查看 Phoenix。结束时运行 `docker compose --profile full down`；只有确认不要保留本地数据时才加 `-v`。

**3. 起依赖，本机跑代码**：适合修改 `project/src/`。

```bash
cp .env.example .env
docker compose up -d --wait
export DATABASE_URL=postgresql+asyncpg://aiapp:aiapp@localhost:5432/aiapp
export REDIS_URL=redis://localhost:6379/0
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:6006
uv run alembic -c project/src/aiapp/storage/alembic.ini upgrade head
uv run uvicorn aiapp.api.app:create_app --factory --port 8000
```

然后打开 Playground，或按 [project/README.md](./project/README.md) 的 curl 示例调用 SSE 接口。Linux、macOS 和 Windows 的 shell 差异只在 `export` / `open` 这类命令；使用 `.env` 或 PowerShell 环境变量时不影响代码本身。

**4. 生产形态：** 镜像不带密钥，生产模式拒绝默认 token 和内存存储。

```bash
AIAPP_TOKENS=mytoken:tenant-a docker compose -f docker-compose.prod.yml up --build
```

评测门禁和六个故障演练不需要 key：`uv run python scripts/eval_run.py --report eval-report.md`、`uv run python scripts/chaos.py --all`。

## 这门课和别的有什么不同

| 已有资源 | 它的侧重 | 本课补什么 |
|---|---|---|
| [12-factor-agents](https://github.com/humanlayer/12-factor-agents) | 12 条 Agent 工程原则 | 原则怎么落到一个真实项目里 |
| [ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) | Agent 知识地图，示例绑 Azure | 不绑云厂商，加评测、可观测、成本、安全的生产视角 |
| [langchain-academy](https://github.com/langchain-ai/langchain-academy) | LangGraph 的 State / Graph / Checkpoint | 用普通 Python 讲同样的机制，读者再选框架 |
| [generative-ai-for-beginners](https://github.com/microsoft/generative-ai-for-beginners) | GenAI 应用通识 | 通识压进前置，主线直接从应用工程切入 |
| [llm-course](https://github.com/mlabonne/llm-course)、[LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) | 模型原理与训练 | 只取应用工程师需要的那一层，作为前置 F 组 |

## 课程编排与内部编号

普通学习者按上面的 Stage 走；`Part 0–5`、`P / B / A / F`、`M0–M6` 和 `L0–L5` 是为了查找、验收和维护保留的内部编号。它们不代表额外课程，也不会在末尾追加新主题。

主线 00–04、05–12、13–15 可以分别看作模型、Agent、知识三条能力段；17–20 的评测、观测、可靠性和安全从 M1 就开始以小版本出现。详细依赖和晋级门槛见 [ROADMAP.md](./ROADMAP.md)，每课状态见下面的课程总表。

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
│   ├── framework-lab/      Stage 6：baseline 与三个框架实现，加一致性测试
│   ├── capstones/          Stage 7：四个实战题目
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

编号只表示学习顺序：`P` / `B` / `A` / `F` 是四组前置模块，`00～23` 是主线课，`M0～M6` 是项目里程碑，课程总表里的 `Part 0～5` 只是把 24 课分成六组方便对照。普通学习者优先看 Stage 0–7；这些内部编号都不会在末尾追加编号塞新主题。

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

- **阅读模式**：先看心智模型和失败案例，再读生产方案、框架映射和项目落点；适合先建立全局理解，不要求马上做练习。
- **实战模式**：先跑 `code/`（默认 fake model），打开 `INJECT_` 失败开关，做练习并对照折叠答案，再把一个增量落进 `project/`，最后跑对应测试。

需要真实模型时按第 00 课配置 DeepSeek；没有 API Key 也能完成所有离线课程和项目验收。

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
| Framework Lab | baseline 和 LangGraph 实现通过 8 个一致性场景；spec 与评分卡已完成，OpenAI Agents SDK、Claude Agent SDK 适配器待做 |
| Capstone | Production Agent Service 已有 reference-grade 交付标准；其他三个题目保持 outline |

下一步按优先级排在 [TODO.md](./TODO.md)：先完成 Framework Lab 的两个 SDK 适配器和真实 Demo，再补 Capstone 其余题目与前置内容。做完一项删一项。

CI 在每次提交上跑七件事：相对链接检查、`complete` 单元的模板检查、状态列与 frontmatter 一致性、数据库迁移的升级回滚、所有示例代码离线运行加项目验收测试、评测门禁、故障演练；最后构建生产镜像并验证启动守卫。配置见 [.github/workflows/ci.yml](./.github/workflows/ci.yml)。

## 给 AI 协作者

这个仓库的大部分正文会由 AI 在人工指导下逐课生成。**新开一个会话续写内容时，先读 [AGENTS.md](./AGENTS.md)**，它说明了目录约定、每课的写作流程、参考仓库的用法和质量门槛。不读它就动手，多半会破坏编号规则或写出和别的课重复的内容。

## 贡献与许可

贡献方式见 [CONTRIBUTING.md](./CONTRIBUTING.md)。文档采用 CC BY-NC-SA 4.0，代码采用 MIT，见 [LICENSE](./LICENSE)。
