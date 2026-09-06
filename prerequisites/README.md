# 补充基础：编程底子与 LLM 原理

> 这里有两组东西，**都不是必修**，用途也不一样：**编程与后端底子**回答「读这门课的代码需要会什么，不会去哪补」；**LLM 原理**回答「模型为什么这样、为什么慢、为什么贵」。
>
> 底子够的人直接去 [第 00 课](../lessons/00-setup/README.md)；读主线时遇到「前置 F0x」的引用，再回来看对应那篇。

## 一、编程与后端底子

[编程与后端底子](./engineering-foundations.md)把 Python、后端、算法三块按「必备 / 用到再学 / 可选」分了档，每项标着这门课哪里用到、缺了去哪学、该读哪几节。

**它是一张索引，不是教程。** 这门课不教 Python，也不教后端——把该学的指出来，你自己去学，比在这里塞一份二手教程有用。

真要动手做一个能跑的服务，参考实现在 [ai-app-engineering-ref](https://github.com/lance2016/ai-app-engineering-ref)。

## 二、LLM 原理（F00–F07）

主线课程默认你知道 token、上下文窗口、采样、attention 大致是怎么回事。这八篇把这些讲清楚，**只到应用工程师能做决策的深度**——不推公式，不讲怎么训练。

**这一组大部分还是草稿。** F02 和 F07 已经补齐，其余六篇的学习目标、核心要点和可跑的小实验都在，但比主线课薄——定位是「够你做决策」，不是完整的原理教程。想深入，看每篇末尾的「延伸阅读」。主线 26 课不受影响，是完整的。

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

---

[主线第 00 课 →](../lessons/00-setup/README.md)
