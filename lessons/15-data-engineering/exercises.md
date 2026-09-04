# 15 数据工程与数据质量｜练习

## 练习 1：不跨章节但也不切断句子

`01_parse_and_chunk.py` 在节内按固定字符数切块，可能把一句话切成两半。改成在 `MAX_CHUNK_CHARS` 范围内寻找最近的句末（`。` `.` `!` `?`）再切。

验收：把 `MAX_CHUNK_CHARS` 改成 60 跑一遍，没有任何 chunk 以半句话结尾；每个 chunk 长度不超过 60 加一个合理的溢出量。

<details><summary>提示</summary>

从 `start + MAX_CHUNK_CHARS` 往前找最后一个句末标点，找不到就退回硬切。允许溢出是因为一句话可能本身就超长，此时宁可超一点也不切断。

</details>

## 练习 2：权限变更也是一种更新

`02_incremental_update.py` 只处理了内容变化。假设 v2 的文档从"customers, support"改成只有"support"可见，内容一字未改。现在的哈希 diff 会认为"全部不变"，权限标签不会更新。

修改索引结构，让权限变化能被识别并只更新标签，不重新 embedding。

验收：v2 只改 acl 时，报告显示 0 条重新 embedding、N 条更新了 acl；检索时按新权限过滤生效。

<details><summary>答案</summary>

哈希只算内容，acl 不进哈希。`upsert_source` 里对 `unchanged` 集合再做一步：比较 acl，不同就原地更新 acl 字段。这题的要点是分清"决定要不要重算 embedding 的东西"和"跟着 chunk 走但不影响 embedding 的东西"。

</details>

## 练习 3：给删除演练加上记忆存储

`03_delete_drill.py` 有三个派生存储。第 14 课的长期记忆也可能是从文档派生的（比如从用户上传的简历里提取的事实）。加第四个存储 `memories`，来源字段用 `source_id`，让演练覆盖它。

验收：删除源文档后 `residue()` 报告四个存储都是 0；注入时可以选择漏删任意一个。

<details><summary>答案</summary>

在 `DerivedStores` 加 `memories: dict[str, str]`，`ingest` 时写入一条，`delete_source` 的循环和 `residue` 的元组加上 `"memories"`。这题想说明的是：派生物的清单会随着系统长大而变长，删除演练的清单必须跟着长。最好把这个清单收在一处，所有派生物注册进来，而不是散在各处。

</details>

## 练习 4：陈旧数据巡检的告警阈值

`stale_chunks()` 返回落后于源版本的 chunk。如果它每天跑一次，什么情况下应该告警？只要有一条就告警，还是超过一定比例？

<details><summary>参考答案</summary>

取决于陈旧的原因。如果增量更新是同步的，出现任何一条陈旧数据都说明更新流程有 bug，一条就该告警。如果更新是异步批处理，处理窗口内的陈旧是正常的，应该按"陈旧超过 X 小时"告警，而不是按数量。

所以 `stale_chunks()` 应该带上时间：记录 chunk 的 `embedded_on` 和源版本的发布时间，告警条件是两者的差超过 SLA。第 18 课会把这个变成一个可观测指标。

</details>

## 练习 5：读一段检索结果，判断是哪一步的问题

用户问"数字商品能退款吗"，检索返回的 top-1 chunk 是：

```text
source=policy/refund.md v1 section="Digital goods" acl=(customers, support)
"Digital goods are refundable only if not downloaded."
```

但当前政策文档已经是 v2，内容是"14 天内可退，即使已下载"。问题出在数据链的哪一步？

<details><summary>答案</summary>

`02` 里的增量更新没有跑，或者跑了但没有删掉旧版本的 chunk。检索本身是对的，它忠实返回了索引里的内容；问题是索引落后于源。`stale_chunks()` 应该能查出这条 v1 的 chunk。

这也说明引用里带版本号有多重要：用户或运维一眼能看出"v1"和当前版本不一致。没有版本字段，这类问题只能靠用户投诉发现。

</details>
