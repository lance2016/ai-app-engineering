# 背景知识：要会什么，模型为什么这样工作

> 这里的东西**都不是必修**，分两类：**工程能力**回答「读这门课的代码需要会什么」，**算法基础**回答「模型和检索为什么这样工作」。完全没写过程序，先从工程能力目录的“零基础与开工”开始；其他人缺哪块补哪块，不用通读。
>
> 这些都清楚的人直接去 [第 00 课](../lessons/setup/README.md)；主线课点到哪一篇，再回来看哪一篇。

## 一、工程能力

工程能力分成两条入口。基础目录按“读懂一条请求 → 能启动和排查服务”的顺序展开；进阶目录按“长期运行的服务会怎样坏”展开。两个目录都可以只读其中一页，不要求从头通读。

| 目录 | 适合谁 | 页面 |
|---|---|---|
| [工程能力](./engineering-foundations/README.md) | 第一次系统做后端或 AI 应用的人 | [零基础与开工](./engineering-foundations/getting-started.md) · [Python 运行时](./engineering-foundations/python-runtime.md) · [Web 与 HTTP](./engineering-foundations/web-http.md) · [数据与存储](./engineering-foundations/data-storage.md) · [可靠性与测试](./engineering-foundations/reliability-testing.md) · [观测、容器与部署](./engineering-foundations/observability-deployment.md) · [工具链与安全](./engineering-foundations/tooling-security.md) |
| [工程能力进阶](./engineering-advanced/README.md) | 已经做过几年后端、需要处理线上取舍的人 | [分布式执行](./engineering-advanced/distributed-execution.md) · [可靠性与容量](./engineering-advanced/reliability-capacity.md) · [数据演进与异步工作流](./engineering-advanced/data-evolution-workflows.md) · [多租户与安全架构](./engineering-advanced/multi-tenant-security.md) · [评测与观测](./engineering-advanced/evaluation-observability.md) · [架构决策](./engineering-advanced/architecture-decisions.md) |

**这一页讲到够用为止，不替代完整教程。** 先把概念和边界说清，再给官方资料和学习顺序；需要动手时，沿着入口去参考实现，不在这里复制一套后端课程。

真要动手做一个能跑的服务，参考实现在 [ai-app-engineering-ref](https://github.com/lance2016/ai-app-engineering-ref)。

## 二、算法基础

| 页 | 管什么 |
|---|---|
| [算法与数学](./algorithm-foundations.md) | 复杂度、哈希表、向量与余弦、top-k、ANN。够做判断就行，不考推导 |
| [LLM 原理 F00–F07](./llm-foundations/README.md) | 模型为什么这样、为什么慢、为什么贵 |

### LLM 原理（F00–F07）

主线课程不解释 token、上下文窗口、采样、attention 是什么。这八篇把这些讲清楚，**只到应用工程师能做决策的深度**——不推公式，不讲怎么训练。

这八篇按同一个目录收在“LLM 原理”下面。它们是主线的可选背景，不要求先读完；主线课点到哪个概念，再回来看对应一篇。每篇末尾都有继续学习的资料。

### 自检

下面每一条都能答上来，就不用读这一组：

- [ ] 能用一句话说清 LLM 在做什么，并推出「没有记忆」「不是数据库」「输出是抽样」三个后果
- [ ] 能解释 token 和字的关系、为什么中文更贵、上下文窗口为什么是**每轮都在花**的预算
- [ ] 能说清 attention 为什么是 O(n²)、KV cache 是什么、GQA 和量化各省了什么
- [ ] 能说出预训练、SFT、偏好对齐各给了模型什么
- [ ] 拿到一个质量问题，能判断该改提示、加检索还是微调

### 八篇

| # | 模块 | 一句话 | 主线落点 |
|---|---|---|---|
| F00 | [LLM 是什么](./llm-foundations/00-what-an-llm-is/README.md) | Next Token Prediction 及其三个直接后果；能力从哪来 | 01, 07, 08, 14 |
| F01 | [Tokenization](./llm-foundations/01-tokenization/README.md) | BPE、token 效率、embedding 层、特殊 token | 02, 05, 08, 20 |
| F02 | [Embedding 与向量空间](./llm-foundations/02-embeddings/README.md) | 文本 embedding 模型是什么、余弦与归一化、维度与模型绑定 | 04, 14, 15 |
| F03 | [Attention 与 Transformer](./llm-foundations/03-attention-and-transformer/README.md) | 一次 attention 在算什么、O(n²)、GQA；block 结构与参数量 | 08, 22 |
| F04 | [Context Window 与 Sampling](./llm-foundations/04-context-window-and-sampling/README.md) | 窗口是每轮都在花的预算；temperature 与 top-p 改了什么 | 01, 02, 08 |
| F05 | [训练与对齐](./llm-foundations/05-training-and-alignment/README.md) | 预训练、SFT、RLHF / DPO 各给了什么；对话模板；LoRA | 03, 05, 09, 21, 22 |
| F06 | [KV Cache 与推理](./llm-foundations/06-kv-cache-and-inference/README.md) | prefill 与 decode、KV cache 显存、量化、批处理、prompt caching | 08, 20, 22 |
| F07 | [模型地图](./llm-foundations/07-model-landscape/README.md) | 五类模型、开放权重与托管、怎么读模型卡 | 01, 22 |

按顺序读，或者按主线的引用跳着读，都可以。F00–F02 是理解一切的基础，F03–F06 是「为什么慢、为什么贵」的答案，F07 是选型时查的。

## 这门课用不到的东西

省下时间，下面这些不用补：

- **训练和微调模型的能力。** 第 23 课讲什么时候该微调、怎么算显存、成本临界点在哪，但不教你训一个模型。
- **深度学习框架。** 全课不出现 PyTorch。LLM 原理那八篇里的小实验是纯标准库的。
- **线性代数和概率论的推导。** 需要的部分（向量、余弦、采样）在那八篇里用具体数字讲完了。
- **前端框架。** 第 24 课讲交互设计和状态机，不写 React。
- **Kubernetes。** 第 21 课到容器和灰度为止。

## 从哪开始

| 你的情况 | 建议 |
|---|---|
| 必备项基本都有，没做过 AI 应用 | [第 00 课](../lessons/setup/README.md)顺着读 |
| 做过 AI 应用，想查漏补缺 | 看[课程总览](../lessons/README.md)，每个 Part 开头有几道题，答不上就读那个 Part |
| 模型原理不熟（token、attention、KV cache） | 上面那八篇 |
| 必备项缺得比较多 | 先读工程能力目录的“零基础与开工”，再补 Python 运行时、Web 与 HTTP、数据与存储三页 |
| 有几年后端经验，想看高阶取舍 | 直接读[工程能力进阶](./engineering-advanced/README.md)，按它指向的 M2–M6 和第 07、17–22、26 课回到主线 |

---

[主线第 00 课 →](../lessons/setup/README.md)
