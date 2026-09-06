# 前置：LLM 原理

> 主线课程默认你知道 token、上下文窗口、采样、attention 大致是怎么回事。这一组八篇把这些讲清楚，**只到应用工程师能做决策的深度**——不推公式，不讲怎么训练。
>
> 已经懂的人直接去 [第 00 课](../lessons/00-setup/README.md)；读主线时遇到「前置 F0x」的引用，再回来看对应那篇。
>
> **这一组还是草稿。** 八篇的学习目标、核心要点和可跑的小实验都在，但比主线课薄——它的定位是「够你做决策」，不是完整的原理教程。想深入，看每篇末尾的「延伸阅读」。主线 26 课不受影响，是完整的。

## 自检

下面每一条都能答上来，就不用读这一组：

- [ ] 能用一句话说清 LLM 在做什么，并推出「没有记忆」「不是数据库」「输出是抽样」三个后果
- [ ] 能解释 token 和字的关系、为什么中文更贵、上下文窗口为什么是**每轮都在花**的预算
- [ ] 能说清 attention 为什么是 O(n²)、KV cache 是什么、GQA 和量化各省了什么
- [ ] 能说出预训练、SFT、偏好对齐各给了模型什么
- [ ] 拿到一个质量问题，能判断该改提示、加检索还是微调

## 八篇

| # | 模块 | 一句话 | 主线落点 |
|---|---|---|---|
| F00 | [LLM 是什么](./llm-foundations/00-what-an-llm-is/README.md) | Next Token Prediction 及其三个直接后果；能力从哪来 | 01, 07, 13 |
| F01 | [Tokenization](./llm-foundations/01-tokenization/README.md) | BPE、token 效率、embedding 层、特殊 token | 01, 02, 08 |
| F02 | [Embedding 与向量空间](./llm-foundations/02-embeddings/README.md) | 文本 embedding 模型是什么、余弦与归一化、维度与模型绑定 | 04, 13, 14 |
| F03 | [Attention 与 Transformer](./llm-foundations/03-attention-and-transformer/README.md) | 一次 attention 在算什么、O(n²)、GQA；block 结构与参数量 | 08, 21 |
| F04 | [Context Window 与 Sampling](./llm-foundations/04-context-window-and-sampling/README.md) | 窗口是每轮都在花的预算；temperature 与 top-p 改了什么 | 01, 02, 08 |
| F05 | [训练与对齐](./llm-foundations/05-training-and-alignment/README.md) | 预训练、SFT、RLHF / DPO 各给了什么；对话模板；LoRA | 03, 05, 21 |
| F06 | [KV Cache 与推理](./llm-foundations/06-kv-cache-and-inference/README.md) | prefill 与 decode、KV cache 显存、量化、批处理、prompt caching | 08, 19, 21 |
| F07 | [模型地图](./llm-foundations/07-model-landscape/README.md) | 五类模型、开放权重与托管、怎么读模型卡 | 01, 21 |

按顺序读，或者按主线的引用跳着读，都可以。F00–F02 是理解一切的基础，F03–F06 是「为什么慢、为什么贵」的答案，F07 是选型时查的。

## 编程与后端基础

这门课不教 Python 和后端工程。主线正文里的代码都是示意性的，读懂需要：

- **Python**：能读带类型注解的函数、dataclass 和 async 代码。不熟的话，[官方教程](https://docs.python.org/zh-cn/3/tutorial/) 和 [Real Python](https://realpython.com/) 是好起点；async 部分推荐 [asyncio 官方文档](https://docs.python.org/zh-cn/3/library/asyncio.html)。
- **HTTP 与 Web 服务**：知道状态码语义、请求头、SSE 是什么。参考 [MDN HTTP 文档](https://developer.mozilla.org/zh-CN/docs/Web/HTTP)。
- **SQL 基础**：会写 SELECT / JOIN，知道索引干什么。任意一本入门书都够。

真要动手做一个能跑的服务，参考实现在 [ai-app-engineering-ref](https://github.com/lance2016/ai-app-engineering-ref)。

---

[主线第 00 课 →](../lessons/00-setup/README.md)
