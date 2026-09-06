# 贡献指南

## 贡献什么

- 补全某一课：按 [AGENTS.md](./AGENTS.md) 第 3 节的流程，把一课从 `outline` 推到 `draft` 或 `complete`。
- 修正错误：概念错、代码跑不通、链接断。
- 加反例和一线经验：这两样最缺。
- 改进学习入口、路径图、Demo 录制规范或项目展示，但不要用不存在的截图声称功能已经完成。
- 完善 Framework Lab 的规格、评分证据和 Capstone 验收；优先补可运行证据，不扩张主线课程数量。

## 不接受什么

- 新增一级目录，或在 `lessons/` 末尾追加编号。
- 绑定特定云厂商或 Agent 框架的课程正文。框架只在每课的「框架映射」表里对照，附官网链接。
- 可运行的项目代码。课文里的代码是示意性的；能跑的实现在 [ai-app-engineering-ref](https://github.com/lance2016/ai-app-engineering-ref)。
- 翻译搬运参考仓库的段落。
- Dashboard、学习计划类文件。

## 流程

1. 一个 PR 尽量只动一课、一条原则或一个明确的产品化单元（例如 README onboarding、Framework Lab、Capstone 1）。
2. 写完把 frontmatter 和 `README.md` 总表的状态改成一致。
3. `code/` 下的文件在没有 API Key 时也要能跑通。提交前跑 `uv run pytest -q`、`scripts/check_links.py`、`scripts/check_lesson_template.py` 和 `scripts/sync_status.py --check`，CI 会跑同样的检查。
4. 中文正文说人话，代码全英文。具体规范见 AGENTS.md 第 4 节。

## 提交信息

`<type>: <描述>`，type 用 `content`（正文）、`code`（示例代码）、`fix`、`docs`（仓库级文档）、`chore`。例如 `content: 完成第 05 课 Tool Calling 正文`。
