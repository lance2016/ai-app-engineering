# 04 Embedding 与向量检索基础｜练习

## 练习 1：去掉归一化

把正文 `embed()` 里的归一化去掉，`cosine()` 里也去掉除以模长（变成纯点积）。再给候选列表加一条很长的、和密码无关但重复很多常见词的句子。

验收：那条长句子得分排到前面。恢复归一化后它掉回去。

<details><summary>答案</summary>

点积同时受方向和长度影响，长文本的向量元素多、模长大，天然占便宜。归一化把长度信息去掉，只留方向。这也是为什么 pgvector 文档建议存归一化后的向量，用内积代替余弦可以少算一次开方。

</details>

## 练习 2：加一个词表大小的实验

`DIM = 64` 意味着所有词被哈希到 64 个桶，不同的词会撞进同一个桶。把 `DIM` 改成 8 和 4096，想一想检索排序会怎么变。

验收：`DIM=8` 时出现明显的乱序；`DIM=4096` 和 64 结果接近。

<details><summary>答案</summary>

桶少碰撞多，不相关的词被算成相同特征。真实 embedding 没有 hash 碰撞的问题，但有类似的取舍：维度低了表达力不够，高了浪费存储。差别是真实模型的每一维都是学出来的有意义方向，不是随机桶。

</details>

## 练习 3：滑动窗口切块

正文的按句切块让每块只有一句，上下文太少。写一个「两句一块、重叠一句」的滑动窗口切块函数，比较三种方式下目标句子的排名和得分。

验收：滑动窗口的目标块得分介于整块和单句之间，但它带上了前后文。

<details><summary>答案</summary>

```python
def sliding(text, size=2, overlap=1):
    sents = by_sentence(text)
    step = size - overlap
    return [" ".join(sents[i:i + size]) for i in range(0, len(sents) - overlap, step)]
```

没有最优切块，只有适合当前查询类型的切块。问答类查询偏好小块精准命中，摘要类查询需要大块保留上下文。第 14 课会用 Recall@k 把这个选择变成可以测量的。

</details>

## 练习 4：写出完整的 pgvector 流程

不用运行数据库，写出这些 SQL：建表（维度 1024）、批量插入 3 条（向量用占位符）、按 doc_id 删除一份文档的所有块、查询 top-3 并返回相似度。

验收：四段 SQL 语法正确，查询里用了 `<=>`，删除用了 `doc_id`。

<details><summary>答案</summary>

```sql
CREATE TABLE chunks (id bigserial PRIMARY KEY, doc_id text NOT NULL, content text NOT NULL, embedding vector(1024));
INSERT INTO chunks (doc_id, content, embedding) VALUES ('d1', '...', $1), ('d1', '...', $2), ('d2', '...', $3);
DELETE FROM chunks WHERE doc_id = 'd1';
SELECT content, 1 - (embedding <=> $q) AS similarity FROM chunks ORDER BY embedding <=> $q LIMIT 3;
```

删除那一句是很多 RAG 系统缺的能力：用户要求删数据时，只删原文不删向量，向量里的信息还能被检索出来。所以每条向量都要能追溯到来源。

</details>

## 练习 5：换模型要付什么代价

团队用模型 A 建了 200 万条向量的索引，现在想换到更好的模型 B。列出至少四件必须做的事，以及一种能让切换期间服务不中断的做法。

<details><summary>参考答案</summary>

必须做：用 B 重新计算全部 200 万条向量（时间和调用费用）；新建维度匹配的表或列；重建 HNSW 索引；所有查询路径切到 B。可能还要重新调相似度阈值，因为不同模型的分数分布不同。

不中断的做法：双写一段时间，新表灌完并验证召回后，把查询切过去，再删旧表。给每条向量记模型版本字段，查询时按版本过滤，就是为了这种切换。

</details>
