---
status: draft
updated: 2026-09-04
---

# 07 指令微调与对齐：从"会续写"到"会听话"

> 对应 LLMs-from-scratch 第 7 章。你调用的每一个 chat 模型都经过了这一步。知道它做了什么，就知道为什么 system prompt 有效、为什么模型有时"过度拒绝"、为什么同一基座的不同版本工具调用能力差很多。

## 学习目标

- 能说出 SFT、RLHF、DPO 三个阶段各自的输入数据和优化目标
- 能解释"对话模板"是什么，以及为什么用错模板模型会胡说
- 能判断一个应用问题该靠 prompt、靠 SFT 还是靠偏好对齐解决

## 心智模型

```mermaid
flowchart LR
    B[基座模型<br/>只会续写] --> S[SFT<br/>指令-回答对<br/>学格式和任务]
    S --> P[偏好对齐<br/>RLHF / DPO<br/>成对比较：哪个回答更好]
    P --> C[Chat 模型<br/>你调用的那个]
```

## 要点

1. **SFT（监督微调）用"指令 → 期望回答"的数据对训练。** 目标函数和预训练一样是下一个 token 预测，只是只对回答部分算 loss。数据量几万到几百万条。它教会模型"看到指令就回答，而不是续写指令"。
2. **对话模板把 system / user / assistant 拼成一串带特殊 token 的文本。** 每家模型的模板不同。用错模板，模型会把角色标记当普通文本，输出质量断崖下跌。托管 API 帮你做了这一步，自部署时是最常见的坑。
3. **system prompt 有效，是因为 SFT 数据里就有 system 角色，模型学会了优先遵从它。** 它不是魔法，是训练出来的习惯，所以不同模型对 system prompt 的"服从度"不同。
4. **RLHF 用人类对成对回答的偏好训一个奖励模型，再用强化学习让模型往高奖励方向走。** 流程复杂、不稳定，但它让模型学到了"有用、诚实、无害"这类难以用数据对表达的目标。
5. **DPO 跳过奖励模型，直接用偏好对优化。** 实现简单得多，效果接近，现在开源模型普遍用它或它的变体。
6. **工具调用能力主要来自 SFT 数据里的工具调用样本。** 一个模型"会不会调工具"、"参数填得准不准"、"会不会编造工具名"，取决于这部分数据的质量和数量。这是第 05 课那些守卫存在的原因：训练不可能覆盖你的工具。
7. **过度拒绝是对齐的副作用。** 安全对齐让模型学会拒绝有害请求，代价是边界模糊的正常请求也被拒。应用里遇到时，先换措辞和加上下文，再考虑换模型。
8. **指令微调数据的多样性决定泛化。** 只在客服对话上 SFT 的模型，写代码会变差。这是"领域模型"的代价。
9. **合成数据（用大模型生成训练数据）是现在 SFT 数据的主要来源之一。** 质量靠过滤和人工抽检保证。对应用的启发：你的评测集（第 17 课）也可以这样起步。
10. **判断该用哪一层解决问题：格式和风格问题先试 prompt；prompt 不稳定且有几百条例子，试 SFT；涉及"更好 vs 更差"的主观判断，才是偏好对齐的领域。** 绝大多数应用停在第一层。

## 实验：看一眼对话模板在做什么

不训练，只拼字符串。理解模板长什么样，就理解了"角色"在模型眼里是什么。

```python
# 一种常见的对话模板形态（各家具体 token 不同，结构相似）
BOS, EOS = "<|begin|>", "<|end|>"

def render(messages):
    out = [BOS]
    for m in messages:
        out.append(f"<|{m['role']}|>\n{m['content']}{EOS}\n")
    out.append("<|assistant|>\n")     # 提示模型：轮到你了
    return "".join(out)

messages = [
    {"role": "system", "content": "You are a terse assistant."},
    {"role": "user", "content": "What is 2+2?"},
]
prompt = render(messages)
print(prompt)
print("---")
print(f"模型实际看到的是一段 {len(prompt)} 字符的纯文本；角色只是特殊 token 围起来的段落。")
```

SFT 时，loss 只在 `<|assistant|>` 之后的部分计算，所以模型学的是"在这个位置该说什么"。如果你自部署时忘了加最后那个 `<|assistant|>\n`，模型会接着"扮演用户"，因为从它的角度看用户的话还没说完。

## 和主线的关系

- system prompt 为什么有效、边界在哪 → [第 03 课 Prompt Engineering](../../lessons/03-prompt-engineering/README.md)。
- 工具调用能力的来源 → [第 05 课](../../lessons/05-tool-calling/README.md) 守卫存在的理由。
- 该 prompt 还是该微调 → [第 21 课](../../lessons/21-model-adaptation-finetuning-inference/README.md)。

## 延伸阅读

- [LLMs-from-scratch · ch07](https://github.com/rasbt/LLMs-from-scratch/tree/main/ch07)（访问日期 2026-09-04）：完整走一遍指令微调，bonus 有用 GPT-4 给回答打分的评估脚本，和第 17 课的 LLM Judge 是同一思路。
- [Happy-LLM 第 6 章](https://github.com/datawhalechina/happy-llm)（访问日期 2026-09-04）：预训练、SFT、PEFT 的训练流程实践。
- [llm-course · Supervised Fine-Tuning、Preference Alignment](https://github.com/mlabonne/llm-course)（访问日期 2026-09-04）：SFT 和 DPO 的资料与 notebook。

---

[← 06](./06-finetuning-classification.md) · [08 →](./08-inference-optimization.md)
