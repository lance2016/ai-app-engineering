---
status: draft
updated: 2026-09-04
---

# 06 分类微调：用 LLM 当分类器

> 对应 LLMs-from-scratch 第 6 章。把一个生成模型改成分类器，是理解"微调改了什么"的最清楚的例子，也是很多生产系统里意图识别、路由、安全过滤的真实做法。

## 学习目标

- 能说出把 LLM 改成分类器要换掉哪个部件、冻结哪些部件
- 能比较"用 prompt 让大模型分类"和"微调小模型分类"的成本与质量取舍
- 能解释 LoRA 为什么能用极少参数达到接近全量微调的效果

## 心智模型

```mermaid
flowchart LR
    B[预训练好的 Transformer<br/>大部分参数冻结] --> L[最后一个 token 的表示]
    L --> H2[新的输出头<br/>投影到 K 个类别]
    H2 --> C[类别概率]
    style H2 fill:#fde
```

## 要点

1. **分类微调 = 换输出头。** 原来投影到词表（几万维），现在投影到类别数（比如 2）。取序列最后一个 token 的表示喂给新头，因为 causal attention 下它看到了全部输入。
2. **只训最后几层加新头，前面冻结，效果通常就够。** 预训练已经学会了通用表示，分类任务只需要学"怎么读这些表示"。
3. **LoRA 不改原权重，在旁边加一对低秩矩阵 A（d×r）和 B（r×d），r 很小（8～64）。** 训练只更新 A、B，参数量是原来的千分之一级。推理时可以合并回原权重，零额外延迟。
4. **LoRA 有效的直觉：微调带来的权重变化本身就是低秩的。** 任务特定的调整不需要动全部维度。
5. **一个基座配多个 LoRA 适配器，是多任务部署的常见做法。** 意图分类一个、安全过滤一个、风格改写一个，切换成本是几十 MB 的加载。
6. **微调小模型做分类 vs prompt 大模型做分类**：前者延迟低（几十毫秒）、成本低、行为稳定，但要标数据、要维护；后者零样本就能用，但每次调用贵、慢、输出格式要约束。生产里高频路径常用前者。
7. **评估用准确率、精确率、召回率、F1，看混淆矩阵。** 不要只看准确率，类别不平衡时它会骗人。
8. **数据量：几百到几千条标注就能微调出可用的分类器。** 比预训练的万亿 token 差 8 个数量级，这是微调的意义。
9. **过拟合的信号是训练集准确率高、验证集不动或下降。** 微调数据少，几个 epoch 就可能过拟合。
10. **应用里的位置：路由、意图识别、安全分类、质量打分。** 这些都是"输入一段文本、输出一个标签"的任务，都是分类微调的候选。

## 实验：LoRA 的参数量到底省了多少

```python
def lora_params(d_in, d_out, rank):
    return rank * (d_in + d_out)

def full_params(d_in, d_out):
    return d_in * d_out

d = 4096
for r in [4, 8, 16, 64]:
    lora = lora_params(d, d, r)
    full = full_params(d, d)
    print(f"rank {r:>2}: LoRA {lora/1e6:.2f}M vs full {full/1e6:.1f}M  ({lora/full*100:.2f}%)")

# 一个 32 层模型，每层给 Q 和 V 两个投影加 LoRA
layers, targets = 32, 2
print(f"\nwhole model, rank 16: {layers * targets * lora_params(d, d, 16) / 1e6:.1f}M trainable params")
print(f"vs 7B full finetune:   ~6600M")
```

rank 16 的 LoRA 只训练约 8.4M 参数，全量微调是 6600M。这是为什么一张消费级显卡能微调 7B 模型。

## 和主线的关系

- 微调 vs prompt 的取舍 → [第 21 课](../../lessons/21-model-adaptation-finetuning-inference/README.md) 的决策框架。
- 分类器在 Agent 里的位置 → [第 09 课 Routing 模式](../../lessons/09-workflow-vs-agent/README.md)、[第 20 课 安全过滤](../../lessons/20-security-governance/README.md)。
- 评估指标 → [第 17 课 评测](../../lessons/17-evaluation/README.md)。

## 延伸阅读

- [LLMs-from-scratch · ch06](https://github.com/rasbt/LLMs-from-scratch/tree/main/ch06)（访问日期 2026-09-04）：把 GPT-2 微调成垃圾短信分类器，bonus 里比较了训哪几层的效果。
- [Happy-LLM 第 6 章](https://github.com/datawhalechina/happy-llm)（访问日期 2026-09-04）：LoRA / QLoRA 高效微调的实践。

---

[← 05](./05-pretraining.md) · [07 →](./07-instruction-finetuning.md)
