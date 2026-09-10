---
status: complete
part: 背景知识
---

# 观测、容器与部署：给失败留下证据

> 日志、指标、trace、容器和健康检查把“服务好像挂了”变成可以定位和回滚的事实。

## 日志、指标和 trace：给失败留下证据

日志回答“发生了什么”，指标回答“发生了多少”，trace 回答“一次请求经过了哪些步骤、每步花了多久”。一次模型请求至少要能关联 request id、thread id、model、工具名、耗时、token 用量和停止原因；这些字段要避免放入密钥、完整用户隐私和未经处理的 prompt。

参考实现的结构化日志、成本和 trace 在 [`ops/logging.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/logging.py)、[`ops/cost.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/cost.py)、[`ops/telemetry.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/telemetry.py)。第 20 课会把一条请求串成模型、工具、检索和存储的 span。

官方资料访问日期为 2026-09-10：[OpenTelemetry Observability primer](https://opentelemetry.io/docs/concepts/observability-primer/)。先分清 logs、metrics、traces，再看 trace context 怎样跨异步任务和 HTTP 边界传播。


## 容器、配置和部署

容器镜像是应用和依赖的只读打包，容器是这个镜像的一次运行。镜像本身不保存运行时数据；数据库卷、环境变量和密钥要单独管理。Compose 适合在本地把应用、PostgreSQL、Redis 和观测服务接成一组，生产环境还要考虑备份、滚动更新和资源限制。

健康检查至少分两类：`/healthz` 只说明进程还活着，`/readyz` 才说明依赖已经连好、可以接流量。收到 `SIGTERM` 后，进程应停止接新请求，等待正在写入的事件完成，再退出；否则重启可能留下半条流或未保存的 checkpoint。

参考实现的镜像、Compose、健康检查和退出处理在 [`Dockerfile`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/Dockerfile)、[`docker-compose.yml`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/docker-compose.yml)、[`ops/health.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/health.py)、[`runtime/runner.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/runtime/runner.py)。官方资料访问日期均为 2026-09-10：[Docker Compose](https://docs.docker.com/compose/)、[Dockerfile reference](https://docs.docker.com/reference/dockerfile/)。

---

[工程能力概览](./README.md) · [背景知识总览](../README.md)
