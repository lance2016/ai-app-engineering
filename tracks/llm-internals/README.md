---
status: draft
updated: 2026-09-04
---

# Track｜LLM 原理补课

> 应用工程师需要知道多少模型原理？答案是：到能做技术决策为止。这条 track 按 [LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) 的章节顺序走，每篇只写结论和一个纯 Python 小实验，不训练模型，不依赖 torch。
> 目标是面试被追问"为什么需要 KV cache"、"LoRA 为什么有效"、"上下文为什么贵"时能答出机制，而不是背名词。

## 目录

| # | 篇 | 对应章节 | 状态 |
|---|---|---|---|
| 01 | [理解 LLM：应用工程师需要知道的那一层](./01-what-an-llm-is.md) | LLMs-from-scratch ch01；Happy-LLM 1～4 | draft |
| 02 | [文本与 token](./02-text-and-tokens.md) | ch02 | draft |
| 03 | [Attention：为什么上下文越长越贵](./03-attention.md) | ch03 | draft |
| 04 | [GPT 架构：一层一层叠起来](./04-gpt-architecture.md) | ch04 | draft |
| 05 | [预训练：能力从哪来](./05-pretraining.md) | ch05 | draft |
| 06 | [分类微调：用 LLM 当分类器](./06-finetuning-classification.md) | ch06 | draft |
| 07 | [指令微调与对齐](./07-instruction-finetuning.md) | ch07 | draft |
| 08 | [推理优化：延迟、显存和吞吐的账](./08-inference-optimization.md) | 无对应章；llm-course Engineer 路线 | draft |

## 怎么学

1. 按顺序读，每篇 20～30 分钟。实验代码直接复制到 Python 里跑，都不依赖第三方库。
2. 想真正动手实现，去跟 LLMs-from-scratch 原书的 notebook；中文读者可以配合 [Happy-LLM](https://github.com/datawhalechina/happy-llm)。本 track 是它们的"结论摘要加应用映射"，不是替代。
3. 每篇末尾的「和主线的关系」告诉你这个原理在主线哪一课变成了工程决策。

## 状态说明

八篇都是 draft：结论和实验已写，缺读者反馈和更细的图。原 Vault 曾提到一份「LLMs-from-scratch × Happy-LLM 10 周计划」，文件不在库内，这里没有沿用。

## 参考

- [rasbt/LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch)（访问日期 2026-09-04）
- [datawhalechina/happy-llm](https://github.com/datawhalechina/happy-llm)（访问日期 2026-09-04）
- [mlabonne/llm-course](https://github.com/mlabonne/llm-course)（访问日期 2026-09-04）

---

[← 课程总表](../../README.md)
