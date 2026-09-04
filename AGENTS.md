# AGENTS.md｜给 AI 协作者的续写说明

这份文件的读者是 AI 编码助手（Claude Code、Codex、Cursor 等）。人类维护者会在新会话里说「把第 N 课写出来」或「补一条原则」，你需要靠这份文件独立完成，不需要重新问项目是什么。

## 1. 项目是什么

一门中文开源课程：面向有后端经验的工程师，讲怎样把 LLM 从「能调用」做成「可上线的 Agent 系统」。三层内容：

| 层 | 目录 | 形式 |
|---|---|---|
| 前置 | `prerequisites/` | 四组，面向零基础，独立于主线：`python/` P00–P07 语言、`backend/` B00–B04 后端工程、`algorithms/` A00–A06、`llm-foundations/` F00–F07 |
| 原则 | `principles/` | 12 条，一条一个文件，12-factor-agents 风格 |
| 课程 | `lessons/` | 24 课，编号即顺序，每课 `README.md + code/ + exercises.md + images/` |
| 项目 | `project/` | 一个贯穿全程的服务骨架，7 个里程碑 M0–M6；另有不编号的 `framework-lab/`（同一需求三框架对照）和 `capstones/`（四个实战） |

命名约定：`Part N` 是课程分组，`L0–L5` 是 ROADMAP 里的能力阶段，`P00–P07、B00–B04` / `A00–A06` / `F00–F07` 是前置模块，`M0–M6` 是项目里程碑。

另有 `reference/`（术语、选型、资料）、`templates/`（写作模板）、`scripts/`（状态同步、链接与模板检查）、`tests/`（所有 `code/` 的 smoke test，将来按里程碑放验收测试）。 README 顶部用到的 banner、路线图、架构图放在 `.github/assets/`，它不是内容目录，不受下面第 1 条限制。

课程的历史来源是作者的 Obsidian 笔记（Codex 多轮对话生成的大纲），位于作者本机 `~/Documents/work/Codex 学习沉淀/`。它们只是大纲，没有代码。每课 README 底部的「写作素材」折叠块列出了对应的旧文件和参考仓库章节。

## 2. 硬性目录规则

1. **不新增一级目录。** 新内容只能进现有的 `prerequisites/ principles/ lessons/ project/ reference/`。
2. **`prerequisites/` 四组、`lessons/` 和 `project/mN` 的编号严格等于学习顺序。** 不允许在末尾追加编号来塞新主题。真的需要新课，要么放进最相关那课的 `bonus/` 子目录，要么和维护者确认后整体重排编号。历史：2026-09-04 公开前做过一次整体重排，在原 06 之后插入了 07 State/Runtime 和 08 Context Engineering，22 课变 24 课；同日的架构优化把 `tracks/llm-internals` 迁入 `prerequisites/llm-foundations/` 重排为 F00–F07，新建 `prerequisites/algorithms/` A00–A06，并在 `prerequisites/python/` 末尾追加了 P12 Redis（它依赖 P11 的 compose，学习顺序成立，这是唯一一次追加）。lessons 编号自重排后没有再动过。同日晚上把 `python/` 的后端工程部分 P08–P12 拆成独立的 `backend/` B00–B04，并删除了 `tracks/`（两条方向选修，与主题不够聚焦）。
3. **`project/framework-lab/`、`project/capstones/` 不编号进主线**，内部文件可以用 `NN-topic` 排序。
4. **目录名英文 kebab-case，标题中文。** 不改已有目录名，改名会断所有链接。
5. **不创建 Dashboard、周计划、学习记录、复盘之类的文件。** 那是读者自己的事，参考仓库都没有。
6. **不改 `README.md` 课程总表的结构**，只改状态列。2026-09-04 加过 Lab 和 Capstone 两个分组行，之后不再改结构。

## 3. 写一课的流程

以「写第 05 课」为例。

### 3.1 读

- 读 `lessons/05-tool-calling/README.md` 现有内容和底部「写作素材」块。
- 读 `templates/lesson-README.md` 确认小节结构。
- 读前一课和后一课的 README，确认边界，不要重复讲、也不要留空档。
- 读 `principles/README.md`，找到本课要落地的原则。

### 3.2 研究

- **参考仓库**：按「写作素材」块列出的章节，去 GitHub 读原文。这些仓库的用法各不相同：

  | 仓库 | 借什么 | 不借什么 |
  |---|---|---|
  | [12-factor-agents](https://github.com/humanlayer/12-factor-agents) | 观点的切入角度、反例的设计 | 它的代码是 TypeScript，不照搬 |
  | [ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) | 章节的知识覆盖面、小节顺序 | Azure / Semantic Kernel 绑定的部分 |
  | [langchain-academy](https://github.com/langchain-ai/langchain-academy) | 每个 notebook 只讲一个机制的粒度 | LangGraph API，我们用普通 Python 讲同样的机制 |
  | [generative-ai-for-beginners](https://github.com/microsoft/generative-ai-for-beginners) | 通识部分的讲法 | 低代码、特定厂商模型的课 |
  | [openai-cookbook](https://github.com/openai/openai-cookbook) | 具体技术点的可运行示例 | 只保留能迁移到 fake adapter 的部分 |
  | [llm-course](https://github.com/mlabonne/llm-course)、[LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) | 原理部分的取舍标准 | 训练和研究路线 |

- **一手资料**：官方文档、协议规范、原始论文优先。每条引用标访问日期。模型价格、上下文长度、API 参数这类时间敏感信息必须标日期和版本。
- **联网搜索**：用来核对参考仓库有没有更新章节、找最新的官方文档。搜到的二手文章只用来建立直觉，结论回到一手来源。
- **版权**：只借结构和思路。不复制参考仓库的段落和图片。代码要重写成本课自己的例子。

### 3.3 写

按模板填满每个小节，具体要求：

- **为什么需要** 一段话，写不做这件事会出什么问题，最好是一个真实事故的形态。放在学习目标之前。
- **学习目标** 3 条以内，动词开头，可验证。「理解 X」不算，「能解释 X 为什么会 Y」才算。
- **心智模型** 一张图加一段话。图用 mermaid（GitHub 原生渲染）或放 `images/`。
- **最小可运行例子** 放 `code/`，一个文件只演示一个机制，文件名说明机制（如 `01_schema_validation.py`、`02_idempotency_key.py`）。每个文件顶部一行 docstring 说明运行命令和预期输出。默认用 `project/src` 里的 fake adapter，不依赖真实 API Key 也能跑。
- **常见错误与失败注入** 至少一个读者能复现的反例，最好就是 `code/` 里某个文件的一个开关。
- **取舍** 只写和本课相关的，不要每课都把质量、延迟、成本、安全四个词抄一遍。
- **生产方案** 最小实现到生产之间差什么，指向 `project/` 里落地它的里程碑或文件，不在课里重复实现。
- **框架映射** 一张表，本课概念在 LangGraph、OpenAI Agents SDK、Claude Agent SDK 里各叫什么、藏在哪一层。只放表不放代码，标核对日期。和本课无关就写「本课概念在框架层没有对应」，不硬凑。三个框架是 Framework Lab 选定的，不换。
- **练习** 3～5 题，每题写清任务和验收标准。答案和提示放 `exercises.md`，用 `<details>` 折叠。
- **对照真实项目** 指向 `project/` 里哪个里程碑落地这个概念；里程碑有代码后改成指向具体文件和测试。第 07、08、10、15、17 课可以用语音机器人案例，但只保留架构模式和取舍，不出现业务细节、内部接口名、任何标识信息。
- **延伸阅读** 每条一句话说为什么值得读。

写完后删除底部的「写作素材」折叠块，或把它压缩成延伸阅读的一部分。

### 3.4 收尾

1. 把 README 顶部 frontmatter 的 `status` 改成实际状态（见第 5 节），填 `estimated_time`。
2. 运行 `uv run python scripts/sync_status.py`，它会按 frontmatter 同步 `README.md`、`principles/README.md`、`prerequisites/README.md`、`project/README.md` 里的状态列。不要手改状态列。
3. 检查 `principles/` 里对应原则的「相关课程」和 `project/README.md` 的课程到项目映射表是否还准确，不准就改。
4. 跑 `uv run pytest`，它会执行所有 `code/` 文件；需要真实模型的脚本在没有 key 时必须打印提示后正常退出，不能报错。有 key 时再手动用 `MODEL_PROVIDER=deepseek` 跑一遍。
5. 跑 `uv run python scripts/check_links.py` 和 `uv run python scripts/check_lesson_template.py`。前者检查相对链接，后者检查标 `complete` 的单元是否真的满足模板（小节齐全、`code/` 有文件、练习有折叠答案）。CI 会跑同样的四个检查，本地没过就不要提交。

## 4. 写作规范

- **中文，说人话。** 短句，先结论再解释。不写「进行 + 动词」「对于……来说」「通过……实现」这类翻译腔。
- **术语**：常见术语直接用中文（缓存、事务、幂等）。中文比英文更生硬的保留英文（backpressure、fallback、trace）。不常见术语第一次出现用一句话解释。不生造术语。
- **代码全英文**：变量名、函数名、注释、docstring、日志。
- **不绑框架。** 讲机制用普通 Python。框架代码只出现在 `project/framework-lab/`；课程正文里提框架只在「框架映射」小节的表里。
- **模型可替换。** 任何示例都通过 `aiapp.get_adapter()` 调模型，默认 fake adapter。需要真实模型时用 `MODEL_PROVIDER=deepseek`：课程的真实模型示范默认 DeepSeek，因为国内可直接访问；它走 OpenAI 兼容协议，DashScope 和 OpenAI 是同一个 adapter 的不同预设。正文里不写死任何一家的 SDK 调用。
- **新依赖要说明。** 某课需要新包时，`uv add` 之后在那课 README 的「安装」或「最小可运行例子」里写清为什么需要它。当前基础依赖是 pydantic、openai、python-dotenv、fastapi、uvicorn、httpx。框架依赖只进 `frameworks` 依赖组，钉版本并标日期。
- **`.py` 是唯一的代码源文件。** `code/` 下只放 `.py`，用 `# %%` 分隔符写成 cell 风格，VS Code / PyCharm 能逐格运行，`jupytext --to ipynb` 能转给想用 Jupyter 的读者；pytest 只跑 `.py`。notebook 只允许用于"看数据"的场景（分布、相似度、评测曲线、模型输出对比），放在该课 `notebooks/` 目录，提交前清空输出。不要把 Agent 循环、状态、副作用类的示例写成 notebook，它们的价值在于可测试、可 import、无隐藏状态。
- **不放密钥、内部地址、账号。** 需要 key 的地方读环境变量并在 `00-setup` 说明。
- **不夸大。** 没有跑过的代码不写「验证通过」；有争议的判断写「一种常见做法是」而不是「必须」。

## 5. 状态定义

| 状态 | 含义 |
|---|---|
| `outline` | 只有学习目标和心智模型，或连这两个都还是占位 |
| `draft` | 有能跑的 `code/`，但缺练习、反例或对照项目中的至少一项 |
| `complete` | 六条全满足：正文每个小节有实质内容；`code/` 能离线跑；至少一个 `INJECT_` 失败注入开关；练习有折叠答案；「对照真实项目」指向 `project/` 里存在的落点；CI 四个检查通过 |

frontmatter 是唯一事实来源，各总表的状态列由 `scripts/sync_status.py` 生成。宁可标低，不要标高。「项目落点存在」和三个新模板小节在 M1～M5 落地前由 `check_lesson_template.py` 只报告不阻断；落地后转为门禁并做一次状态审计。

## 6. 优先顺序

24 课正文已经齐了，当前最大的缺口是实现。具体待办在 [TODO.md](./TODO.md)，做完一项删一项。大方向：

1. M1～M5 已落地（2026-09-04），每个有 `tests/project/mN`；改运行时代码时同步更新对应课的「对照真实项目」和里程碑 README 的验收证据。
2. `project/framework-lab/`：先 `spec.md` 和一致性测试，再三个实现，最后评分卡。同步给 05～14 课补「框架映射」。
3. `project/capstones/` 四个 README 补全，能自动化的验收进 `tests/capstones/`。
4. 前置新内容：`algorithms/` A00～A06、`backend/04-redis`、`llm-foundations/` 的 F02、F04、F07 正文与代码，其余 F 模块补练习。
5. 24 课回填「为什么需要」「生产方案」，然后做一次状态审计。

维护者说了具体要做哪一课，以维护者为准。

## 7. 写前置模块、原则、项目的差异

- **前置模块**（`prerequisites/python/NN-*/`、`prerequisites/backend/NN-*/`）：读者是零基础，先给能跑的例子再解释概念，每段代码不超过 15 行，不用主线里的术语。「常见错误」小节要贴真实的报错信息。「它在 AI 应用里用在哪」写一个具体场景把它连到主线某一课，让初学者知道为什么学。P07 asyncio 的五个对照实验直接对应 `project/m0`，两边要一致。

- **前置 F 组**（`prerequisites/llm-foundations/NN-*/`）：同前置模块的写法，另加两条：不训练、不依赖 torch，每篇一到两个纯 Python 实验；只写到应用工程师能做决策的深度，训练细节一句话带过并链接 LLMs-from-scratch。

- **前置 A 组**（`prerequisites/algorithms/NN-*/`）：每篇必须从一个真实的工程问题进入（幂等键、检索合并、DAG 并行、竞态），「它在 AI 应用里用在哪」至少指向两课。不出 LeetCode 题，不手写红黑树。标准库够用。

- **Framework Lab 实现**（`project/framework-lab/NN-<framework>/`）：固定四样东西：README（概念映射表、顺手处、别扭处、锁定点）、`agent.py`、实现共同 `AgentRuntime` 协议的 `adapter.py`、十二维自评。离线可跑是硬要求，每个框架都要有回放 fake 剧本的办法。先写映射表再写代码。评分卡每格附代码行链接，不打总分不排名。

- **Capstone**（`project/capstones/NN-*/README.md`）：六段固定结构：需求、约束、验收清单、评分量表、交付物、常见失败。验收清单里能自动化的放 `tests/capstones/<name>/`；评分量表七个维度各三档。

- **原则**（`principles/NN-*.md`）：主张 → 违反它会怎样 → 最小做法 → 对照。整篇不超过 150 行，代码不超过 30 行。先读 12-factor-agents 对应 factor 的写法，但用自己的反例。
- **项目里程碑**（`project/mN-*/README.md`）：这一步加什么 → 运行步骤 → 验收证据 → 依赖的课程。代码放 `project/src`，里程碑目录只放说明和该阶段特有的脚本。验收证据必须包括一次失败注入。

## 8. 不要做的事

- 不要把参考仓库的内容翻译过来当正文。
- 不要为了显得完整给每课都塞上多智能体、微调、机器人。它们各有自己的位置。
- 不要在 `lessons/` 里回头补 Python、算法、Transformer 基础。需要就链接到前置模块。第 01 课只讲应用层的能力边界、成本模型与选型，原理归 F 组；第 04 课只讲 embedding 的工程选型与索引，embedding 是什么归 F02；第 21 课只讲决策树与计算器，LoRA、KV cache 机制归 F05、F06。
- 不要把框架代码放进 `lessons/*/code/`。
- 课程边界，写课前先读相邻课的 README：
  - 03 只讲单次调用的 prompt 和上下文；08 讲 runtime 每一轮怎么组装上下文窗口。
  - 06 是机制课，讲 runtime 怎么执行一个 loop；09 是架构决策课，讲面对需求时在 Workflow、Router、Parallelization、Agent 之间怎么选。两课不要重复实现同一个循环。
  - 07 讲 state schema、runtime 生命周期、checkpoint、pause / resume、人工介入、事件流、重复消息策略。工具幂等归 05，并发控制归前置 P07，多租户状态隔离归 20。
  - 08 只讲一个 Agent 每轮的上下文构造；10 讲多个 Agent 之间怎么隔离和交接；12 讲能力说明怎么封装和按需加载。
- 不要在正文里写「本课和第 X 课的区别是」这类元说明。边界靠内容本身体现。
- 不要新建「知识地图」「学习路线」「能力盘点」类的总览文件。总览只有 `README.md` 和 `ROADMAP.md` 两个。
- 不要一次改很多课。一课写完、状态改对、链接检查完，再开下一课。
