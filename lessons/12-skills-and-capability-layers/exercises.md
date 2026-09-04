# 12 Skill 与能力生态分层｜练习

## 练习 1：归位

下面五样东西各属于哪一层（Tool / MCP / Skill / Plugin / A2A）？

1. 一个 GitHub 仓库，里面有 `manifest.json`，声明了三个 MCP server 和两个 Skill，一条命令装进某个 IDE
2. 一段说明，教模型"用户要发周报时，先查日历，再查 PR 列表，按这个模板写"
3. 一个子进程，启动后响应 `tools/list`，返回 `query_db` 和 `list_tables`
4. 一个 JSON 文档，描述某个远程服务"能处理数据分析任务，接受这些输入格式，在这个 URL 接任务"
5. 一个 Python 函数 `get_weather(city: str) -> str` 和它的 JSON Schema

<details><summary>答案</summary>

1 Plugin，2 Skill，3 MCP server，4 A2A 的 Agent Card，5 Tool。

注意 2 和 3 的关系：Skill 里"查日历、查 PR"这两个动作可能就是 3 这样的 MCP server 提供的。Skill 不提供动作，它提供用法。

</details>

## 练习 2：重写 description

`code/skills/meeting-notes/SKILL.md` 的 description 已经是"判断条件"式的。把它改成一个功能介绍式的坏版本（比如 "Summarizes meetings."），然后想三个用户输入，判断模型在级别 1 只看到坏版本时会不会误加载或漏加载。

<details><summary>参考答案</summary>

坏版本漏掉了两个触发信号："用户贴了转录稿"和"用户要总结会议"。输入 "这是刚才的录音转文字，帮我整理一下" 没有出现"会议"二字，功能介绍式的描述很可能漏加载。而输入 "帮我总结一下这篇文章" 有"总结"，可能误加载。

description 是在替模型做分类，写法要像分类条件。

</details>

## 练习 3：激活期间收窄白名单

改 `01_progressive_loading.py`：模型 `load_skill` 成功后，把后续给模型的工具列表收窄到该 Skill 的 `allowed-tools`（和注册表取交集）。

验收：加载 `expense-report` 后，模型看到的工具只剩 `search_notes`（`read_file` 不在注册表里）；加载 `meeting-notes` 后也是 `search_notes`。

<details><summary>提示</summary>

`parse_frontmatter` 已经能拿到 `allowed-tools`。在 `load_skill` 分支里记下当前激活的 Skill，`model.complete(..., tools=...)` 时按它过滤。要考虑：模型能不能同时激活两个 Skill？取并集还是只允许一个？这题没有标准答案，但你要能说出选择的理由。

</details>

## 练习 4：哈希固定的盲区

`02_validate_and_pin.py` 的哈希覆盖了 Skill 目录里的所有文件。还有什么它管不到？

<details><summary>答案</summary>

至少三样：

- `scripts/` 里的脚本如果 `import` 了目录外的包，包被换掉哈希不变。这是普通的依赖供应链问题，要靠锁文件。
- SKILL.md 正文里如果让模型去访问一个 URL 取"最新政策"，URL 内容变了哈希不变。Skill 应该尽量把参考资料放进 `references/`，而不是指向外部。
- 模型本身。同一份 Skill 在不同模型、不同版本上的执行结果不同。这是第 17 课评测要管的事。

哈希固定解决的是"文件被改"这一个问题，它很重要，但不是全部。

</details>

## 练习 5：Skill 还是 Workflow

一个场景：用户上传发票，系统要提取金额、校验是否超预算、超了就发邮件给主管审批、没超就直接入账。哪些步骤应该写成 Skill 让模型按说明执行，哪些应该写成第 09 课的确定性 Workflow？

<details><summary>参考答案</summary>

提取金额需要理解图片和自然语言，交给模型，可以用 Skill 说明格式和注意事项。校验预算、判断超没超、发邮件、入账，都是确定性逻辑，而且涉及资金和外部副作用，应该是代码。

Skill 在这里的合理范围是"怎么读发票"，不是"怎么走审批流"。把审批流写进 Skill 让模型执行，等于把合规逻辑交给概率过程。

</details>
