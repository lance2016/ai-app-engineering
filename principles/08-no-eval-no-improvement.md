---
status: complete
---

# 原则 08｜没有评测集，就没有「变好了」

> 改了 prompt，试了三个问题，感觉更好了。这句话里每个词都有问题：三个问题不是样本，"感觉"不是指标，"更好"没有基线。

## 主张

AI 应用的每一次改动，无论是 prompt、模型、检索参数还是工具描述，都会同时让一些案例变好、一些变坏。没有评测集，你只能看到自己碰巧试到的那几个。所以：

1. **评测集先于优化。** 第一版 prompt 写完之前，先有 10 条带预期的案例。宁可评测集简陋，不能没有。
2. **断言优先于打分。** 大多数失败可以用确定性断言捕获：必须包含、不能包含、必须调某个工具、不能超过几步。断言零成本、毫秒级、每次改动都跑。打分留给断言测不了的。
3. **切片优先于总分。** 总分 92% 掩盖了"对抗类 0%"。评测集的每条案例都要打标签，报告按标签看。
4. **Judge 先校准再信。** 用模型给模型打分之前，让人先标一批，算一致率和 kappa。分歧案例拿去改 judge 的 prompt。
5. **改动进不进，由门禁说。** 基线分数存下来，新版本任何切片跌破阈值就拒绝合并。阈值是产品决策，但必须有。

## 违反它会怎样

- **一直在"优化"，从未变好。** 每周改一次 prompt，每次都修了上周的抱怨，也每次都引入了新的。半年后回头看，整体质量在原地打转。
- **上线后才发现退化。** 新模型便宜三成，试了几个问题都好，切换后客服工单翻倍。退化的是"多轮追问"这个切片，没人在切换前试过。
- **Judge 说好就是好。** 用 GPT 给自己的输出打分，全是 4.5 分以上。后来发现 judge 对"礼貌但没回答问题"的输出一律给高分。
- **评测集变成摆设。** 有评测集，但跑一次要半小时、要 key、要人盯，于是只在发版前跑一次。等它报警时，改动已经堆了二十个，不知道是哪个引起的。

## 最小做法

```python
@dataclass(frozen=True)
class Case:
    id: str
    question: str
    must_contain: tuple[str, ...] = ()
    must_not_contain: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

def evaluate(cases, answer) -> dict[str, float]:
    by_tag = defaultdict(lambda: [0, 0])
    for c in cases:
        out = answer(c.question).lower()
        ok = all(k.lower() in out for k in c.must_contain) and not any(k.lower() in out for k in c.must_not_contain)
        for t in c.tags:
            by_tag[t][0] += ok; by_tag[t][1] += 1
    return {t: ok / n for t, (ok, n) in by_tag.items()}

def gate(current, baseline, max_drop=0.10) -> list[str]:
    return [t for t, b in baseline.items() if b - current.get(t, 0) > max_drop]
```

三十行，没有依赖，跑一次不到一秒。它不完美，但它存在，而且每次 `pytest` 都会跑。

## 对照

- 参考：[Hamel Husain · Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/)（访问日期 2026-09-04），Level 1/2/3 的分层和"pass rate is a product decision"；[Hamel Husain · Creating a LLM-as-a-Judge](https://hamel.dev/blog/posts/llm-judge/)（访问日期 2026-09-04），二元 pass/fail 加 critique；[openai-cookbook · examples/evaluation](https://github.com/openai/openai-cookbook/tree/main/examples/evaluation)（访问日期 2026-09-04），看 `use-cases/regression.ipynb` 的组织方式
- 相关课程：[18 评测](../lessons/18-evaluation/README.md)

---

[← 原则总览](./README.md)
