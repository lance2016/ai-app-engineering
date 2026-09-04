# 01 LLM 工作原理与能力边界｜练习

## 练习 1：中文合并

`01_bpe_tokenizer_toy.py` 的语料全是英文，所以中文完全没有合并。往 `CORPUS` 里加几句重复出现"下一个"、"模型"的中文，把 `num_merges` 调到 80，再看中文样本的 bytes/token。

验收：中文样本的 bytes/token 从 3.0 上升到接近 6 或更高，说明高频中文词被合并成了单个 token。

<details><summary>答案与讨论</summary>

真实 tokenizer 就是这样：训练语料里中文多，中文的合并就多。所以同一个模型对不同语言的"token 效率"差别很大，取决于它的训练数据配比。这也是为什么面向中文用户选模型时，tokenizer 效率是一个应该实际测量的指标。

</details>

## 练习 2：top-p 与 temperature 的组合

用 `02_sampling_temperature.py` 试三组参数：`TEMPERATURE=1.5 TOP_P=1.0`、`TEMPERATURE=1.5 TOP_P=0.9`、`TEMPERATURE=0.7 TOP_P=0.9`。记录每组出现的 distinct token 数。

验收：能用一句话说出 top-p 和 temperature 各自的作用，以及为什么通常两个一起调。

<details><summary>答案</summary>

temperature 决定分布的平坦程度，top-p 决定砍掉多少尾部。高 temperature 让尾部有机会，top-p 再把最离谱的尾部去掉，结果是"在合理范围内多样"。只调 temperature 会把 banana 放进来，只调 top-p 在低 temperature 下几乎没效果。

</details>

## 练习 3：加一个摘要策略

给 `03_context_window_budget.py` 加一条规则：当 `history` 超过 3000 token 时，把它压缩到 800（模拟做了一次摘要）。重新跑 `INJECT_LONG_HISTORY=1`。

验收：不再溢出，但累计输入 token 仍然明显高于前六轮，说明摘要控制了单轮峰值但不是免费的。

<details><summary>答案</summary>

在循环里加 `if history > 3000: history = 800`。这就是第 08 课要讲的上下文压缩的最简形态。它引入了一个新问题：摘要丢掉的信息模型再也看不到了。哪些该保留、哪些可丢，是上下文工程的核心判断。

</details>

## 练习 4：让 bigram 模型"说真话"

不改 `04_bigram_lm.py` 的模型，只改语料或生成方式，让它生成的五句话全部出现在语料里。

验收：五句都是 `[in corpus]`。然后解释为什么这不是"消除幻觉"。

<details><summary>答案</summary>

最简单的办法是让语料里每个词后面只有一种可能的下一个词（消除所有分叉），或者在生成时只允许输出语料里出现过的完整句子。前者是过拟合，后者是查表而不是生成。

真实 LLM 的对应做法是：把事实放进上下文让它"照着说"（RAG），或者限制输出只能来自一组候选（结构化输出、工具调用）。这两种都不是让模型变得知道更多，而是缩小它自由发挥的空间。

</details>

## 练习 5：估一个真实场景

一个客服机器人：系统提示 1500 token，工具定义 600 token，每轮检索两段共 800 token，用户平均每轮 40 token，回复平均 150 token，一次会话平均 8 轮。窗口 32k。

问：第 8 轮的输入是多少 token？整个会话的输入总量是多少？如果检索改成只在第一轮做，节省多少？

<details><summary>答案</summary>

每轮固定 1500 + 600 + 800 = 2900。历史每轮增加 40 + 150 = 190。第 8 轮输入约 2900 + 7 × 190 = 4230 token，窗口够用。

八轮总输入约 8 × 2900 + 190 × (0 + 1 + ... + 7) = 23200 + 5320 = 28520 token。其中检索占 6400。只在第一轮检索能省 5600，接近两成。

但省钱的前提是后面几轮确实不需要新检索。这个判断需要看真实对话数据，不能拍脑袋。第 17 课的评测就是用来回答这类问题的。

</details>
