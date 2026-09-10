---
status: complete
part: 背景知识
---

# 多租户与安全架构：边界要穿过每一层

> 租户和权限不能只停在入口函数；同一个身份要沿着工具、数据库、事件、成本和 trace 一路传递。

## 多租户与安全

只在 API 入口检查租户还不够。租户身份要随请求进入工具注册表、上下文、数据库查询、事件、成本和 trace；否则某一层忘记过滤，就会出现跨租户读取。控制面（租户、配额、配置、权限）和数据面（消息、文档、工具结果）也应分开考虑。

高阶安全工作还包括：密钥轮换和审计、第三方 Skill/MCP 的来源验证、出站网络限制、敏感字段脱敏、供应商数据保留政策、删除请求的可证明完成，以及把模型输出当作不可信输入。可以用 [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)检查通用 Web 控制，再对照 [OWASP LLM Top 10](https://genai.owasp.org/llm-top-10/)检查模型特有风险，资料访问日期均为 2026-09-10。

参考实现把工具白名单、租户依赖、出站限制和删除路径拆在 [`runtime/registry.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/registry.py)、[`api/deps.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/deps.py)、[`security/outbound.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/security/outbound.py) 和知识库存储层。读代码时要追踪同一个 `tenant_id` 走过哪些边界，而不是只看登录函数。

---

[工程能力进阶概览](./README.md) · [工程能力基础](../engineering-foundations/README.md) · [背景知识总览](../README.md)
