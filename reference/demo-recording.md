# Demo 录制规范

这个仓库只提交真实录制的截图、GIF 或视频。没有素材时，README 只展示文字流程，不用假图填空。

素材放在 `.github/assets/demo/`，文件名用 `NN-short-name.ext`，并在这里记录录制日期、运行配置和对应里程碑。录制前先跑 `uv run pytest -q`，避免把偶发失败剪成“功能”。

## Demo 1｜Agent streaming → approval → execution

- 启动：`docker compose --profile full up -d --build --wait`
- 场景：发起需要副作用的请求，展示 `assistant_delta`、工具调用、`human_input_requested`、批准、幂等执行和最终回答。
- 画面：左侧 Playground 事件流，右侧批准动作；不要展示 token、密钥或真实用户数据。
- 证据：对应 M3、课程 05 / 07 / 22；建议文件名 `01-agent-approval.gif`。

## Demo 2｜RAG import → query → citation

- 场景：导入一份示例文档，查询其中事实，展示检索结果、引用回链和一个不存在答案的拒答。
- 画面：文档来源、回答中的 citation、空召回或引用校验失败。
- 证据：对应 M4、课程 13 / 15；建议文件名 `02-rag-citation.png`。

## Demo 3｜Phoenix trace

- 场景：完成一次包含模型、工具和检索的请求，在 Phoenix 展开 root span 和子 span。
- 画面：耗时、错误状态、模型与工具 span；敏感输入输出先脱敏。
- 证据：对应 M5、课程 18；建议文件名 `03-phoenix-trace.png`。

## Demo 4｜kill process → resume

- 场景：任务在 checkpoint 后被终止，重新启动服务并用同一个 thread resume；证明已完成的副作用没有重复。
- 画面：终止前的事件、重启后的恢复位置、幂等计数或测试输出。
- 证据：对应 M2 / M3、课程 07；建议文件名 `04-checkpoint-resume.gif`。

## 发布前清单

- [ ] 所有素材来自 fake model 或脱敏的公开样例。
- [ ] 录制命令和仓库当前 README 一致。
- [ ] 截图 alt 文本说明了它要证明的工程行为。
- [ ] 文件体积适合 GitHub；视频优先转成短 GIF 或外链并保留静态封面。
- [ ] 素材在 README 的 Demo 区域有链接，且没有把“待录制”写成“已完成”。
