---
status: draft
part: 前置 · LLM 原理
estimated_time: 约 40 分钟
---

# F04 Context Window 与 Sampling

> 两个直接决定应用行为的旋钮：窗口决定模型一次能看多少，采样决定它从概率分布里怎么挑。两者都不改变模型「知道什么」，但都改变你花多少钱、得到多稳定的输出。

## 学习目标

- 能说清 temperature 和 top-p 分别改变了什么，以及为什么 temperature 为 0 也不等于「一定正确」
- 能列出一个上下文窗口里同时挤着哪几类内容，并解释多轮对话的输入 token 为什么近似平方增长
- 能说出窗口上限、训练长度、有效长度三个数字的区别

## 前置

- [F00 LLM 是什么](../00-what-an-llm-is/README.md)
- [F03 Attention 与 Transformer](../03-attention-and-transformer/README.md)：O(n²) 和 lost in the middle

## 核心概念

```mermaid
flowchart LR
    L[每个词表项一个分数 logits] -->|÷ temperature| T[缩放后的分数]
    T -->|softmax| P[概率分布]
    P -->|top-p 砍尾| P2[截断后的分布]
    P2 -->|抽样| N[下一个 token]
```

1. **输出是抽样，不是查找。** 分数经过 temperature 缩放和 softmax 变成概率，再按概率抽一个。temperature 低，分布尖，几乎总选最高分；temperature 高，分布平，第二、第三选项经常出现。top-p 把尾部低概率项直接砍掉。
2. **temperature 为 0 是贪心，每次一样，但「一样」不等于「对」。** 它只是最可能的那个。实现上 T=0 通常特殊处理为 argmax，批处理和浮点误差仍可能让结果不完全一致。
3. **temperature 不是「创造力开关」。** 它只改变次优选项胜出的频率，不改变模型知道什么。抽取结构化数据用 0，需要多样性再调高，并且配 top-p 砍尾。
4. **上下文窗口是一笔每轮都在花的预算。** 系统提示、工具定义、检索内容、整段历史、给回答预留的空间，全部挤在一个窗口里。
5. **每一轮把历史重新发一遍，所以第 n 轮的输入 token 约等于前 n 轮的总和。** 一段 20 轮的对话总输入是单轮的几十倍。输入 token 才是账单大头，回答是小头。
6. **窗口上限、训练长度、有效长度是三个数。** 供应商标的 128k 是上限；模型训练时见过的最大长度可能更短；在你的任务上质量不下降的长度更短。越长越贵、越慢，中间部分更容易被忽略，128k 不代表应该填满。
7. **溢出时的选择只有四种：裁历史、做摘要、少检索、缩工具定义。** 每一种都丢信息，哪些可丢是主线第 08 课的核心判断。
8. **中文更贵。** 同样内容中文多花一半到一倍 token。提示词的固定部分用英文写、用户内容保持中文，是很多中文产品的实际做法。

## 动手

| 文件 | 演示什么 | 运行 |
|---|---|---|
| [`code/01_sampling_temperature.py`](./code/01_sampling_temperature.py) | 一组假 logits 抽样一千次，看 temperature 和 top-p 怎么改变分布 | `uv run python prerequisites/llm-foundations/04-context-window-and-sampling/code/01_sampling_temperature.py`，试 `TEMPERATURE=0`、`0.2`、`2.0`，`TOP_P=0.9` |

窗口预算的逐轮计算在主线 [第 01 课](../../../lessons/01-how-llms-work/README.md) 的成本模型那一节，那里把它和价格连在一起。

## 常见错误

**期待 temperature 0 消除幻觉。** [F00](../00-what-an-llm-is/README.md) 的 bigram 模型没有随机性也会生成拼接出来的句子。幻觉是机制的一部分，采样参数管不了它。

**只算输出 token。** 输入随历史增长，很快成为主要开销。看账单时先看输入列。

## 它在 AI 应用里用在哪

- 采样参数按任务分别设置 → [第 02 课 模型调用](../../../lessons/02-model-api-structured-output-streaming/README.md)
- 窗口预算与成本模型 → [第 01 课](../../../lessons/01-how-llms-work/README.md)
- 溢出时的取舍 → [第 08 课 Context Engineering](../../../lessons/08-context-engineering-for-agents/README.md)

## 延伸阅读

- [Anthropic · Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)（访问日期 2026-09-04）：一家供应商对窗口、输入输出 token 的官方解释，配图好。
- [Lost in the Middle](https://arxiv.org/abs/2307.03172)（访问日期 2026-09-04）：长上下文中间位置被忽略的实测，读图 1 就够。

---

[← F03](../03-attention-and-transformer/README.md) · [F05 →](../05-training-and-alignment/README.md)
