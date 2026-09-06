"""余弦、归一化和维度截断：三个能看到数字变化的实验。

纯标准库。运行：
    python3 prerequisites/llm-foundations/02-embeddings/code/01_cosine_and_normalization.py
"""

import math
import re
from collections import Counter

# 一个玩具"embedding"：词袋。没有语义，但足以说明向量怎么比较。
# 真实 embedding 模型的向量是训练出来的，这里的每一维就是一个词的出现次数。
VOCAB = ["cat", "dog", "pet", "run", "fast", "food", "vet", "sleep"]

DOCS = {
    "short_cat":  "cat pet",
    "long_cat":   "cat cat pet pet food sleep vet run fast dog",   # 同主题，但长得多
    "dog_doc":    "dog pet food",
    "unrelated":  "run fast",
}
QUERY = "cat pet"


def bag_of_words(text: str) -> list[float]:
    counts = Counter(re.findall(r"[a-z]+", text.lower()))
    return [float(counts[w]) for w in VOCAB]


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def norm(v: list[float]) -> float:
    return math.sqrt(dot(v, v))


def normalize(v: list[float]) -> list[float]:
    n = norm(v)
    return [x / n for x in v] if n else v[:]


def cosine(a: list[float], b: list[float]) -> float:
    n = norm(a) * norm(b)
    return dot(a, b) / n if n else 0.0


def rank(query: str, score) -> list[tuple[str, float]]:
    q = bag_of_words(query)
    return sorted(((d, score(q, bag_of_words(t))) for d, t in DOCS.items()),
                  key=lambda kv: -kv[1])


def main() -> None:
    print("=== 1. 不归一化直接比点积：长文档天然占便宜 ===")
    for name, s in rank(QUERY, dot):
        print(f"  {name:<10} 点积 {s:.3f}   模长 {norm(bag_of_words(DOCS[name])):.3f}")
    print("  long_cat 排在 short_cat 前面，不是因为它更相关，是因为它更长。\n")

    print("=== 2. 换成余弦：只看方向，长度不再影响排序 ===")
    for name, s in rank(QUERY, cosine):
        print(f"  {name:<10} 余弦 {s:.3f}")
    print("  short_cat 回到第一，它和查询的词分布完全一致。\n")

    print("=== 3. 先 L2 归一化，再点积 == 余弦 ===")
    q = normalize(bag_of_words(QUERY))
    for name in DOCS:
        v = normalize(bag_of_words(DOCS[name]))
        print(f"  {name:<10} 归一化后点积 {dot(q, v):.6f}   直接算余弦 {cosine(bag_of_words(QUERY), bag_of_words(DOCS[name])):.6f}")
    print("  两列完全相同。所以向量库存归一化后的向量，用内积就够，省一次开方。\n")

    print("=== 4. 维度截断：丢掉的那半维度里有信息，排序会翻 ===")
    print(f"  完整 {len(VOCAB)} 维：{VOCAB}")
    print(f"  截断到前 4 维：  {VOCAB[:4]}（food / vet / sleep 这几维被丢掉）")
    pair = {
        "noisy_cat_pet": "cat pet food food food food",   # 两个查询词都有，但后半维度噪声很大
        "just_pet":      "pet",                            # 只命中一个查询词，但很干净
    }
    q = bag_of_words(QUERY)
    for label, cut_to in (("完整 8 维", 8), ("截断到 4 维", 4)):
        scored = sorted(((d, cosine(q[:cut_to], bag_of_words(t)[:cut_to])) for d, t in pair.items()),
                        key=lambda kv: -kv[1])
        detail = "   ".join(f"{d} {s:.3f}" for d, s in scored)
        print(f"  {label:<12} {detail}   → 第一名 {scored[0][0]}")
    print("  同一组文档，砍掉一半维度之后名次翻了过来。")
    print("  真实模型的 Matryoshka 截断之所以还能用，是因为训练时就要求前 k 维单独可用，")
    print("  不是随便砍哪几维都行——所以截断只能用模型自己支持的那几个长度。")


if __name__ == "__main__":
    main()
