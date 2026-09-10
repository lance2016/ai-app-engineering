---
status: complete
part: 背景知识
---

# 工具链与安全：让问题可重现，也让权限可控

> 依赖锁定、CI、认证和授权都在回答同一个问题：这次运行用了什么，谁可以让系统做什么。

## 依赖、Git 与 CI

终端、Git 和依赖锁文件解决的是同一个问题：别人能不能重建你看到的结果。环境变量把配置从代码中分开；`pyproject.toml` 描述项目和依赖；`uv.lock` 固定解析后的版本；Git 记录每次改变了什么。遇到失败时，先保存完整 traceback，再缩小输入、固定 seed、记录依赖版本和运行命令。

参考实现把项目元数据和锁文件放在 [`pyproject.toml`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/pyproject.toml)、[`uv.lock`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/uv.lock)，启动配置示例在 [`.env.example`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/.env.example)。官方资料访问日期均为 2026-09-10：[Pro Git](https://git-scm.com/book/en/v2)、[uv 项目结构](https://docs.astral.sh/uv/concepts/projects/layout/)、[uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)、[Missing Semester Shell Tools](https://missing.csail.mit.edu/2020/course-shell/)。

CI 是每次提交自动运行测试、评测、迁移和构建；CD 是把通过检查的构建产物发布或部署。它们的价值是让“这次改动能不能发布”由同一套命令判断，而不是只在某个人电脑上手动点过。参考实现把这些门禁写在 [`.github/workflows/ci.yml`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/.github/workflows/ci.yml)；官方资料访问日期为 2026-09-10：[GitHub Actions](https://docs.github.com/en/actions)。


## 安全边界：谁能让系统做什么

认证回答“你是谁”，授权回答“你能做什么”。最小权限意味着工具注册表、数据库查询、文件访问和管理操作都要按用户、租户和资源范围限制。把 `tenant_id` 从请求一路传到 repository、事件、成本和 trace，才能在每一层检查边界；只在前端隐藏按钮不算授权。

密钥只进运行时配置，不进仓库、镜像、日志和 trace。用户输入、检索文档和 MCP/Skill 内容都可能包含指令，模型可以提出工具调用，但不能凭这段文字获得新的权限。工具白名单、参数校验、人工确认、幂等和审计要由确定性代码执行。

参考实现的出站限制在 [`security/outbound.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/security/outbound.py)，工具权限和租户过滤分布在 [`runtime/registry.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/registry.py)、[`api/deps.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/api/deps.py) 和存储层。官方资料访问日期为 2026-09-10：[OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/)。先看风险名称，再回到主线第 05、12、22 课看代码怎样挡住它们。

---

[工程能力概览](./README.md) · [背景知识总览](../README.md)
