---
status: complete
---

# 原则 07｜失败要分层定位：数据、检索、上下文、模型、工具、控制流

> 「模型答错了」不是诊断，是症状。一次 Agent 回答经过六层，每一层都会以自己的方式坏掉。不先定位到层，改什么都是猜。

## 主张

一条请求从进来到答出去，至少经过这六层。任何一层出错，最终表现都是「回答不对」：

| 层 | 典型失败 | 怎么看出来 |
|---|---|---|
| 数据 | 文档过期、切块切断了表格、权限过滤掉了正确来源 | 检索结果里根本没有正确答案 |
| 检索 | 召回了无关段落、正确段落排在第 20 位 | 正确答案在库里，但不在 top-k |
| 上下文 | 检索到了却被裁剪掉、历史太长把指令挤出去、工具结果格式模型读不懂 | 正确内容在检索结果里，不在最终 prompt 里 |
| 模型 | 上下文里有正确答案，模型还是答错或编造 | prompt 完整，输出错 |
| 工具 | 参数对但外部系统返回错、超时、返回了空 | tool span 有 error 或结果为空 |
| 控制流 | 该调工具没调、调了不该调的、循环、提前停 | 轨迹不对，即使每一步单独看都对 |

定位的顺序是从下往上查数据：先看检索结果里有没有正确答案，再看最终 prompt 里有没有，再看模型输出。每一步都是「看数据」，不是「猜原因」。这要求每一层的输入输出都被记下来，也就是原则 09 说的 trace。

## 违反它会怎样

- **改 prompt 治检索问题。** 正确段落没被召回，团队却在 system prompt 里加「请仔细阅读参考资料」。加了三轮，召回率没变。
- **换模型治数据问题。** 知识库里的价格表是去年的，换了更贵的模型答案依然过期。模型再强也只能基于它看到的东西。
- **给工具加重试治控制流问题。** 模型每次都调错工具，重试只是把错误的调用多做几遍。
- **统一归因为「模型幻觉」。** 这是最常见的一种，因为它不需要看数据。真正的幻觉（上下文正确、模型仍编造）在生产 Agent 的失败里往往是少数。

## 最小做法

评测集的每个失败案例，记录它挂在哪一层，再决定动哪里：

```python
def locate(case, trace) -> str:
    retrieved = trace.retrieved_chunks()
    prompt = trace.final_prompt()
    if not any(case.answer_in(c) for c in retrieved):
        return "data_or_retrieval"   # 再看库里有没有：有则检索，无则数据
    if not case.answer_in(prompt):
        return "context"             # 检索到了，没进 prompt
    if trace.tool_errors():
        return "tool"
    if trace.trajectory_violations():
        return "control_flow"
    return "model"                   # 只有排除了前五层，才算模型的问题
```

把 `locate()` 的结果按层聚合，你会得到一张「这周的失败主要在哪一层」的图。它比总分更能指导下一步做什么。

## 对照

- 参考：[Hamel Husain · Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/)（访问日期 2026-09-04），"critically examine your traces and failure modes"那一段；[ai-agents-for-beginners · 10 AI Agents in Production](https://github.com/microsoft/ai-agents-for-beginners/blob/main/10-ai-agents-production/README.md)（访问日期 2026-09-04）的 root-cause analysis 一节
- 相关课程：[14 RAG](../lessons/rag-end-to-end/README.md)、[16 数据工程](../lessons/data-engineering/README.md)、[18 评测](../lessons/evaluation/README.md)、[19 可观测性](../lessons/observability/README.md)

---

[← 原则总览](./README.md)
