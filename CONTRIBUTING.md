# 贡献指南

## 贡献什么

- 补全某一课：按 [AGENTS.md](./AGENTS.md) 第 3 节的流程，把一课从 `outline` 推到 `draft` 或 `complete`。
- 修正错误：概念错、代码跑不通、链接断。
- 加反例和练习：这两样最缺。

## 不接受什么

- 新增一级目录，或在 `lessons/`、`prerequisites/` 末尾追加编号。
- 绑定特定云厂商或 Agent 框架的课程正文。框架代码只接受进 `project/framework-lab/`。
- 翻译搬运参考仓库的段落。
- Dashboard、学习计划类文件。

## 流程

1. 一个 PR 只动一课或一条原则。
2. 写完把 frontmatter 和 `README.md` 总表的状态改成一致。
3. `code/` 下的文件在没有 API Key 时也要能跑通。提交前跑 `uv run pytest`、`scripts/check_links.py`、`scripts/check_lesson_template.py`，CI 会跑同样的检查。
4. 中文正文说人话，代码全英文。具体规范见 AGENTS.md 第 4 节。

## 提交信息

`<type>: <描述>`，type 用 `content`（正文）、`code`（示例代码）、`fix`、`docs`（仓库级文档）、`chore`。例如 `content: 完成第 05 课 Tool Calling 正文与练习`。
