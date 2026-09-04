# P09 SQL、PostgreSQL 与 SQLAlchemy｜练习

> 每题写清：任务、验收标准、提示。答案折叠。第一题照着做就能完成。

## 练习 1：多查一列

在 `01_sql_basics.py` 的 JOIN 查询里加上 `m.id`，并改成只查 `conversation_id = 1` 的消息。

验收：输出两行，都属于 "weather chat"，第一列是消息 id。

<details><summary>答案</summary>

```sql
SELECT m.id, c.title, m.role, m.content
FROM message m
JOIN conversation c ON c.id = m.conversation_id
WHERE m.conversation_id = ?
ORDER BY m.id
```

`WHERE` 的值用 `?` 传进去：`cur.execute(query, (1,))`。

</details>

## 练习 2：让转账在 SQLAlchemy 里回滚

用 `03_sqlalchemy_models.py` 的写法定义一个 `Account` 模型（`name`、`balance`），写一个 `transfer(session, amount)` 函数，在 `Session` 里做两次余额修改，余额不足时抛 `ValueError`。

验收：调用 `transfer(s, 500)` 后两个账户余额都不变，程序继续运行。

<details><summary>答案</summary>

```python
def transfer(session: Session, amount: int) -> None:
    alice = session.scalars(select(Account).where(Account.name == "alice")).one()
    bob = session.scalars(select(Account).where(Account.name == "bob")).one()
    if alice.balance < amount:
        raise ValueError("insufficient balance")
    alice.balance -= amount
    bob.balance += amount

with Session(engine) as s:
    try:
        with s.begin():          # 块正常结束就 commit，抛异常就 rollback
            transfer(s, 500)
    except ValueError as exc:
        print(exc)
```

`with s.begin():` 把"成功提交、失败回滚"变成自动的，比手写 try/commit/except/rollback 少出错。

</details>

## 练习 3：测一下索引到底快多少

在 `02_transactions_and_indexes.py` 里把 5000 行改成 200000 行，用 `time.perf_counter()` 给加索引前后各跑 100 次同一条 `SELECT count(*) ... WHERE conversation_id = 7` 计时。

验收：加索引后明显更快；写出两个时间。

<details><summary>提示</summary>

插入 20 万行本身要几秒，用 `executemany` 而不是循环 `execute`。你会看到加索引后快一到两个数量级。反过来也试试：给 `content` 列加索引，然后查 `WHERE conversation_id = 7`，速度不会变，因为索引只对"按那一列找"有用。

</details>

## 练习 4：解释这个报错并修好

```python
with Session(engine) as s:
    conv = s.scalars(select(Conversation)).first()
print(conv.messages)
```

运行报 `DetachedInstanceError`。说出原因，给两种修法。

<details><summary>答案</summary>

`conv.messages` 是懒加载的，第一次访问时才去查数据库，但此时 Session 已经关了。

修法一：把 `print` 挪进 `with` 块。修法二：查询时预加载，`select(Conversation).options(selectinload(Conversation.messages))`，这样对象离开 Session 后关联数据已经在内存里。写 API 时常用第二种，因为对象要被序列化成 JSON 返回，那时 Session 早关了。

</details>

## 练习 5：设计一张表

不写代码。主项目 M2 要存 Agent 的事件（第 07 课的 `Event`：`type`、`data`、`ts`）。你会怎么设计 `message` 表？至少回答：哪些列、主键是什么、外键指向哪、哪一列要索引、`data` 这个字典怎么存。

<details><summary>参考答案</summary>

列：`id`（主键，自增）、`conversation_id`（外键 → conversation.id，加索引）、`type TEXT`、`data JSONB`（PostgreSQL 的 JSON 类型，能按字段查询）、`created_at TIMESTAMPTZ`。

按 `(conversation_id, id)` 建一个联合索引，因为最常见的查询是"这个会话的所有事件按顺序"。`data` 用 JSONB 而不是拆成几十列，因为不同 `type` 的事件字段不同，而且以后会加新类型。这正是 SQLAlchemy 里 `mapped_column(JSONB)` 的用处。

</details>
