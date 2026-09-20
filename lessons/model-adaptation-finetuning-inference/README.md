---
status: complete
structure: narrative
part: Part 4 生产工程
topic: model-infrastructure
tier: deep-dive
estimated_time: 约 30 分钟
---

# 23 模型适配、微调与推理服务

> 应用工程师不需要先训练模型，而要知道什么时候改 Prompt、加检索、微调、换模型或自托管，并能说清证据和退出条件。

<details class="case" markdown="1">
<summary>例子：为了修正一类知识错误，团队微调模型，结果知识更新仍要重新训练</summary>

如果问题是文档经常变化，微调会把更新成本放大。RAG 更适合提供外部事实；微调更适合稳定的行为、格式或风格。

!!! note "构造的例子"
    方案对比用于说明问题类型和手段要匹配；真实选择需要用评测和成本数据确认。

</details>

## 四种手段解决不同问题

| 手段 | 适合改变 | 主要代价 |
|---|---|---|
| Prompt | 指令和输出格式 | 每次请求携带，稳定性有限 |
| RAG | 会变化的外部知识 | 数据管线和检索质量 |
| 微调 | 稳定行为、风格或格式 | 数据、训练和版本管理 |
| 自托管推理 | 隐私、吞吐或成本结构 | GPU、部署和运维 |

先用最便宜、最快能验证的手段。只有评测证明前一步不够，才向后升级。

## 推理服务要算三笔账

- **质量**：目标任务和风险切片的成功率。
- **容量**：并发、上下文长度、batch、显存和 p95 延迟。
- **运营**：模型版本、灰度、回滚、监控和安全更新。

自托管不是把 API 换成一台机器。模型加载、KV cache、量化、排队和故障恢复都会改变系统边界。

## 怎么测

同一份 golden set 比较 Prompt、RAG、微调和不同推理服务。记录质量、首 token / 完整延迟、吞吐、显存、单请求成本和失败恢复时间，并写明什么时候停止当前方案。

## 参考实现与延伸

参考实现把模型接缝、fallback 和自托管容量决策写在 [M6 Platform Design](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m6-platform-design)（核对日期 2026-09-10）。推理服务细节可查 [vLLM 文档](https://docs.vllm.ai/)（访问日期 2026-09-10）。

---

[← 上一课 22](../security-governance/README.md) · [下一课 24 →](../product-design-ux/README.md)
