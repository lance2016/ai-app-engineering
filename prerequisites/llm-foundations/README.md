---
status: draft
updated: 2026-09-04
---

# 前置 · LLM 原理（F00～F07）

> 应用工程师需要知道多少模型原理？答案是：到能做技术决策为止。这组模块只写结论和纯 Python 小实验，不训练模型，不依赖 torch。目标是被追问"为什么需要 KV cache"、"LoRA 为什么有效"、"上下文为什么贵"时能答出机制，而不是背名词。
> 主线课程默认你已经学完这里。第 01、04、08、21 课不会再解释 token、attention、KV cache 是什么。

## 模块

| # | 模块 | 一句话 | 对应章节 | 状态 |
|---|---|---|---|---|
| F00 | [LLM 是什么](./00-what-an-llm-is/README.md) | Next Token Prediction 及其三个直接后果；能力从哪来 | LLMs-from-scratch ch01；Happy-LLM 1～4 | draft |
| F01 | [Tokenization](./01-tokenization/README.md) | BPE、token 效率、embedding 层、特殊 token | ch02 | draft |
| F02 | [Embedding 与向量空间](./02-embeddings/README.md) | 文本 embedding 模型是什么、余弦与归一化、维度与模型绑定 | 无对应章 | outline |
| F03 | [Attention 与 Transformer](./03-attention-and-transformer/README.md) | 一次 attention 在算什么、O(n²)、GQA；block 结构与参数量 | ch03、ch04 | draft |
| F04 | [Context Window 与 Sampling](./04-context-window-and-sampling/README.md) | 窗口是每轮都在花的预算；temperature 与 top-p 改了什么 | 无对应章 | draft |
| F05 | [训练与对齐](./05-training-and-alignment/README.md) | 预训练、SFT、RLHF / DPO 各给了什么；对话模板；分类微调与 LoRA | ch05、ch06、ch07 | draft |
| F06 | [KV Cache 与推理](./06-kv-cache-and-inference/README.md) | prefill 与 decode、KV cache 显存、量化、批处理、prompt caching | llm-course Engineer 路线 | draft |
| F07 | [模型地图](./07-model-landscape/README.md) | 五类模型、开放权重与托管、怎么读模型卡 | generative-ai-for-beginners ch02 | outline |

## 怎么学

1. 按顺序读，每篇 30～60 分钟。`code/` 里的实验全部不依赖第三方库，先跑再读。
2. 想真正动手实现，去跟 LLMs-from-scratch 原书的 notebook；中文读者可以配合 Happy-LLM。这组模块是它们的"结论摘要加应用映射"，不是替代。
3. 每篇末尾的「它在 AI 应用里用在哪」告诉你这个原理在主线哪一课变成了工程决策。

## 不在这里讲的

- 训练代码、分布式训练、数据清洗流水线：研究和训练路线，看 LLMs-from-scratch 和 llm-course 的 Scientist 路线。
- 怎样用 embedding 建索引、怎样选推理引擎：那是工程决策，在主线第 04 课和第 21 课。

## 参考

- [rasbt/LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch)（访问日期 2026-09-04）
- [datawhalechina/happy-llm](https://github.com/datawhalechina/happy-llm)（访问日期 2026-09-04）
- [mlabonne/llm-course](https://github.com/mlabonne/llm-course)（访问日期 2026-09-04）

---

[← 前置总览](../README.md)
