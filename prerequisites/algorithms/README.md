---
status: outline
updated: 2026-09-04
---

# 前置 · 算法（A00～A06）

> 这不是一门刷题课。这里只讲 AI 应用工程真正会碰到的七个主题，每个主题都从一个真实的工程问题进去：幂等键为什么要规范化、检索结果怎么合并、Workflow 哪些步骤能并行、两个协程为什么会把同一条记录写坏。每篇一小时以内，纯 Python，标准库够用。
> 想系统学算法，去 [Hello 算法](https://www.hello-algo.com/)。这里是它的"应用工程子集"。

## 模块

| # | 模块 | 一句话 | 主线落点 | 状态 |
|---|---|---|---|---|
| A00 | [复杂度](./00-complexity/README.md) | 用 token、延迟和钱来度量增长；对话为什么平方增长 | 01, 08, 23 | outline |
| A01 | [Hash](./01-hashing/README.md) | 字典与集合的原理、内容哈希、幂等键的规范化、LRU | 05, 08, 15 | outline |
| A02 | [栈、队列与 Deque](./02-stacks-queues/README.md) | 事件队列、有界缓冲、backpressure 的三种策略 | 02, 07, 16 | outline |
| A03 | [堆与 Top-K](./03-heaps-topk/README.md) | top-k、多路合并、RRF、优先级调度 | 04, 13, 19 | outline |
| A04 | [树](./04-trees/README.md) | Markdown 标题树切块、JSON Schema 遍历、Trie、决策树路由 | 09, 13, 15, 20 | outline |
| A05 | [图、BFS/DFS 与拓扑排序](./05-graphs/README.md) | Workflow DAG、并行度、环检测、框架里的 State Graph | 06, 09, 10, Framework Lab | outline |
| A06 | [并发模型](./06-concurrency-models/README.md) | 线程、进程、协程；GIL；竞态、锁与死锁；单写者 | P07, 07, M0, M2 | outline |

## 怎么学

1. 建议在 P06 之后、P07 之前学 A00～A05，A06 和 P07 一起学。
2. 每篇先看「它在 AI 应用里用在哪」，知道为什么学，再看核心概念，再做 `code/`。
3. 不要求手写红黑树或平衡查找树。需要有序结构时用 `bisect` 和 `sortedcontainers`，需要图算法时先看 `graphlib`。

## 不在这里讲的

- 排序算法的实现、动态规划、字符串匹配算法：面试题范围，AI 应用里几乎不手写。
- 数值线性代数：embedding 的点积和归一化在 [F02](../llm-foundations/02-embeddings/README.md) 里够用。

---

[← 前置总览](../README.md)
