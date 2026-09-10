---
status: complete
part: 背景知识
---

# 数据与存储：事实、索引和缓存不是一回事

> 数据库、缓存和连接池都在保存或传递数据，但它们承担的承诺不同。

## 数据库、缓存与连接

### 表、索引和查询

关系数据库用表保存事实，用约束保证字段和关系，用索引减少查询需要扫描的行。索引是读路径的加速结构，不能代替权限过滤，也不能证明写入已经成功。向量列只是表中的一种数据；租户、文档版本、权限和更新时间仍然需要普通字段和索引。

参考实现的表模型和 PostgreSQL 存储在 [`storage/models.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/storage/models.py)、[`storage/postgres.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/storage/postgres.py)、[`knowledge/postgres_store.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/knowledge/postgres_store.py)。官方资料访问日期均为 2026-09-10：[PostgreSQL Tutorial](https://www.postgresql.org/docs/current/tutorial.html)、[Indexes](https://www.postgresql.org/docs/current/indexes.html)、[pgvector](https://github.com/pgvector/pgvector)。

### 事务和迁移

事务把一组写入放进一个提交边界：全部成功才提交，失败则回滚。隔离级别决定一个事务能看到哪些并发写入；它不会替你解决业务幂等。迁移是数据库结构的版本控制，升级和回滚都要在 CI 中跑过，不能只在本地手动改表。

参考实现用 Alembic 管理迁移，入口在 [`storage/migrations/`](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/src/aiapp/storage/migrations)；CI 会执行升级、降级和再次升级，见 [`.github/workflows/ci.yml`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/.github/workflows/ci.yml)。官方资料访问日期均为 2026-09-10：[PostgreSQL Transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html)、[Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)。

### Redis、缓存和锁

Redis 适合保存有过期时间的缓存、短期幂等记录、限流桶和运行锁。它不是 PostgreSQL 事实表的替代品：缓存可以重建，事件和账单不能因为缓存丢失而失去。锁也只是并发控制，不能把外部支付和本地记录变成一个原子事务。

参考实现的 Redis 键值和锁在 [`storage/redis_kv.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/storage/redis_kv.py)、[`ops/ratelimit.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/ops/ratelimit.py)。官方资料访问日期为 2026-09-10：[Redis 开发文档](https://redis.io/docs/latest/develop/)。先看数据类型、过期和事务，再看主线第 07、21 课为什么把事实数据和临时控制数据分开。

### ORM、连接和连接池

ORM 把表和行映射成 Python 类和对象，减少重复的 SQL 拼接；它不能替你决定索引、事务和权限过滤。连接池复用已经建立的数据库连接，同时限制并发连接数。池太小，请求会排队；池太大，数据库会被连接和查询压垮。

参考实现用 SQLAlchemy 的 `AsyncEngine`，在 [`storage/postgres.py`](https://github.com/lance2016/ai-app-engineering-ref/blob/main/project/src/aiapp/storage/postgres.py) 里创建连接池。官方资料访问日期均为 2026-09-10：[SQLAlchemy ORM 快速开始](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)、[Engine 与连接池](https://docs.sqlalchemy.org/en/20/core/engines.html)。

---

[工程能力概览](./README.md) · [背景知识总览](../README.md)
