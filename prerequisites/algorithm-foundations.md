---
status: complete
part: 补充基础
---

# 算法与数学底子：默认你有什么，缺了去哪补

> **这门课不考算法。** 但下面几项如果没有直觉，某些判断做不出来——比如「十万条向量要不要建索引」，答案取决于你对复杂度有没有感觉。
>
> 和[编程与后端底子](./engineering-foundations.md)一样，这一页是索引不是教程：标清每项在哪一课用到、缺了去哪学。模型侧的原理是另一件事，在 [LLM 原理那八篇](./README.md)。

## 该有的直觉

| 项 | 档 | 这门课哪里用到 |
|---|---|---|
| 复杂度直觉（O(n) 还是 O(n log n)） | 必备 | 第 04 课「十万条以内暴力扫描就够，什么时候该建索引」 |
| 哈希表 | 必备 | 幂等键、result store、去重，到处都是 |
| 向量、点积、余弦相似度 | 必备 | 第 04 课的全部基础。[F02](./llm-foundations/02-embeddings/README.md) 讲了够用的部分 |
| top-k 与堆 | 用到再学 | 检索返回 top-k，重排是在这个 k 上再排一次 |
| 队列与并发模型 | 用到再学 | 第 07 课的 double texting 三种策略，本质是队列策略 |
| ANN 索引原理（HNSW） | 可选 | 第 04 课会用它，但调参靠实测，不靠推导 |
| 图与 BFS/DFS | 可选 | 第 09 课 workflow 是有向图，理解「图」这个说法有帮助 |

## 去哪学

| 想补的项 | 去哪学 | 读哪几节 |
|---|---|---|
| 复杂度直觉 | [Big-O cheat sheet](https://www.bigocheatsheet.com/) | 只看常见数据结构那张表 |
| 向量、点积、余弦 | [F02 Embedding 与向量空间](./llm-foundations/02-embeddings/README.md) | 全篇，配一个纯标准库的小实验 |
| top-k 与堆 | [`heapq` 文档](https://docs.python.org/3/library/heapq.html) | `nlargest` 一个函数就够 |
| HNSW 参数的含义 | [pgvector 的索引说明](https://github.com/pgvector/pgvector#indexing) | `m` 与 `ef_construction` 两个参数 |
| HNSW 原理（可选） | [HNSW 论文](https://arxiv.org/abs/1603.09320) | 摘要与图 1 |

访问日期均为 2026-09-06。

**线性代数和概率论的推导不用补。** 这门课需要的那部分——向量、余弦、采样——在 [LLM 原理那八篇](./README.md)里用具体数字讲完了，没有公式推导。

---

[补充基础总览](./README.md) · [编程与后端底子](./engineering-foundations.md)
