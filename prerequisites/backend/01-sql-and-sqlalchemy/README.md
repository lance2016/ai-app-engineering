---
status: complete
part: 前置 · 后端工程
estimated_time: 约 2.5 小时
---

# B01 SQL、PostgreSQL 与 SQLAlchemy

> 程序一关，内存里的东西就没了。数据库是把数据放到程序外面、断电也在、多个程序都能读写的地方。这一模块用 SQLite 学 SQL 本身，再用 SQLAlchemy 学怎么在 Python 里以对象的方式操作它。表的例子一直是 conversation 和 message，主项目 M2 会原样用上。

## 学习目标

- 能写建表、插入、查询、JOIN 四种基本 SQL，并解释主键和外键是什么
- 能说明事务解决什么问题、索引为什么让查询变快，并用 `EXPLAIN` 验证
- 能用 SQLAlchemy 2.0 的声明式模型定义一对多关系，在 `Session` 里增删改查

## 前置

- [P04 类、dataclass 与 Protocol](../../python/04-oop-and-dataclasses/README.md)
- [P05 类型注解](../../python/05-typing/README.md)：SQLAlchemy 2.0 的模型全靠 `Mapped[int]` 这种注解

## 核心概念

### 表、行、列、主键、外键

```sql
CREATE TABLE conversation (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL
);
CREATE TABLE message (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversation(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL
);
```

一张表像一张 Excel：列是字段，行是记录。**主键**（PRIMARY KEY）是每行的唯一编号。**外键**（REFERENCES）是"这一列的值必须是另一张表里存在的主键"，它把两张表连起来：一条 message 属于一个 conversation。

### 增、查、连

```sql
INSERT INTO conversation (title) VALUES ('weather chat');
SELECT id, title FROM conversation;
SELECT c.title, m.role, m.content
FROM message m
JOIN conversation c ON c.id = m.conversation_id;
```

`JOIN ... ON` 把两张表按外键拼成一张宽表。`01_sql_basics.py` 用 Python 自带的 `sqlite3` 跑这几句，SQLite 是一个装在文件里（或内存里）的数据库，学 SQL 用它最省事，语法和 PostgreSQL 大部分一样。

参数一律用 `?` 占位再传值，绝不用字符串拼接：`cur.execute("... WHERE id = ?", (user_input,))`。拼接会让用户输入变成 SQL 的一部分，这就是 SQL 注入。

### 事务：几条改动要么全成要么全不成

```python
try:
    cur.execute("UPDATE account SET balance = balance - 500 WHERE name = 'alice'")
    cur.execute("UPDATE account SET balance = balance + 500 WHERE name = 'bob'")
    conn.commit()
except sqlite3.IntegrityError:
    conn.rollback()      # 第一条也撤销
```

转账是两条 UPDATE。第一条成了第二条失败，钱就凭空消失了。事务的意思是：从开始到 `commit()` 之间的改动是一个整体，中途出错 `rollback()` 全部撤销。`02_transactions_and_indexes.py` 里 alice 余额不够时（表上有 `CHECK (balance >= 0)`），两个人的余额都不变。

保存一条 Agent 的消息和更新会话的"最后活跃时间"，也应该在一个事务里。

### 索引：让"按某列找"不用翻全表

```python
cur.execute("EXPLAIN QUERY PLAN SELECT count(*) FROM message WHERE conversation_id = 7")
# 加索引前：SCAN message
# 加索引后：SEARCH message USING COVERING INDEX ix_message_conversation
```

没索引时数据库要把 5000 行逐个看一遍（SCAN）。`CREATE INDEX ix_message_conversation ON message(conversation_id)` 建了一本"按 conversation_id 排好序的目录"，查询直接定位（SEARCH）。外键列几乎总是要加索引，因为你总要"找这个会话的所有消息"。代价是每次写入要多维护一份目录，所以不是所有列都加。

### SQLAlchemy 2.0：用类描述表，用对象代替行

```python
class Base(DeclarativeBase): pass

class Conversation(Base):
    __tablename__ = "conversation"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(80))
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation")

class Message(Base):
    __tablename__ = "message"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversation.id"))
    role: Mapped[str]
    content: Mapped[str]
    conversation: Mapped[Conversation] = relationship(back_populates="messages")
```

`Mapped[int]` 告诉 SQLAlchemy 这是一个整数列；`relationship` 不是列，是"通过外键能拿到的对象"：`conv.messages` 是这个会话的消息列表，`msg.conversation` 是消息所属的会话。`Base.metadata.create_all(engine)` 会替你生成 CREATE TABLE。`03_sqlalchemy_models.py` 开了 `echo=True`，能看到它生成的 SQL。

### Session：一个事务的作用域

```python
with Session(engine) as session:
    conv = Conversation(title="weather chat")
    conv.messages.append(Message(role="user", content="hot?"))
    session.add(conv)
    session.commit()          # conversation 和 message 一起写入

with Session(engine) as session:
    loaded = session.scalars(select(Conversation).where(Conversation.title == "weather chat")).one()
```

`Session` 是一个工作单元：你往里 add 对象、改对象属性，`commit()` 时它算出需要的 INSERT/UPDATE 一次发出去。`select(...)` 是 2.0 风格的查询构造器，`.where()`、`.join()`、`.order_by()` 和 SQL 一一对应。`04_sqlalchemy_queries.py` 有按会话数消息（`func.count` + `group_by`）、改一条内容、删一个会话连带删消息（`cascade="all, delete-orphan"`）三种操作。

### 迁移：表结构变了怎么办

真实项目里表结构会一直改：加一列、改类型、加索引。不能每次 `DROP TABLE` 重建，数据会丢。**Alembic** 是 SQLAlchemy 配套的迁移工具，流程是：

```bash
alembic init migrations                                  # 只做一次
alembic revision --autogenerate -m "add message.tokens"  # 对比模型和数据库，生成一个迁移脚本
alembic upgrade head                                     # 执行到最新版本
alembic downgrade -1                                     # 退一步
```

生成的脚本是 Python 文件，有 `upgrade()` 和 `downgrade()` 两个函数，要看一眼再执行，autogenerate 偶尔会漏掉或多出东西。本模块不装 Alembic，主项目 M2 第一次改表时会用到。

## 动手

| 文件 | 一个知识点 |
|---|---|
| [`code/01_sql_basics.py`](./code/01_sql_basics.py) | 建表、插入、查询、JOIN，纯 `sqlite3` |
| [`code/02_transactions_and_indexes.py`](./code/02_transactions_and_indexes.py) | 转账回滚；加索引前后的 `EXPLAIN QUERY PLAN` |
| [`code/03_sqlalchemy_models.py`](./code/03_sqlalchemy_models.py) | 声明式模型、一对多关系、生成的 SQL、写入并读回 |
| [`code/04_sqlalchemy_queries.py`](./code/04_sqlalchemy_queries.py) | 分组计数、更新、级联删除 |

`03` 的输出前半段是 `echo=True` 打出来的 SQL，包括几条 `PRAGMA` 探测语句，看 `CREATE TABLE` 那两段就行。

## 常见错误

**Session 关了之后再碰对象的关联属性。**

```text
sqlalchemy.orm.exc.DetachedInstanceError: Parent instance <C at 0x...> is not bound to a Session; lazy load operation of attribute 'ms' cannot proceed
```

`relationship` 默认是"用到时再去查"（lazy load）。`with Session(...)` 块结束后对象和数据库断开了，再访问 `conv.messages` 就会报这个。修法：在 Session 里把需要的东西用完，或者在查询时用 `.options(selectinload(Conversation.messages))` 一次性加载。

**外键指向了不存在的行。**

```text
sqlite3.IntegrityError: FOREIGN KEY constraint failed
```

插入 message 时 `conversation_id` 对应的会话不存在。注意 SQLite 默认**不检查**外键，要先 `PRAGMA foreign_keys = ON`；PostgreSQL 默认检查。所以在 SQLite 上跑通的代码到 PostgreSQL 上可能才第一次报这个错。

**忘了 `commit()`。** 不报错，数据也"看起来"写进去了，但只在当前连接里可见，程序退出就没了。用 `with Session(engine) as s:` 加显式 `s.commit()`，或者 `with Session(engine) as s, s.begin():` 让退出块时自动提交。

## 练习

见 [exercises.md](./exercises.md)。

## 它在 AI 应用里用在哪

主线落点：[07 Agent State 与 Runtime](../../../lessons/07-agent-state-and-runtime/README.md)、[14 Memory](../../../lessons/14-memory/README.md)、[16 系统架构](../../../lessons/16-system-architecture/README.md)、主项目 [M2 数据与状态](../../../project/m2-state-and-storage/README.md)。

具体场景：第 07 课把 Agent 的一次运行记成一串事件，存在一个 JSON 文件里。M2 把这个文件换成 PostgreSQL：`conversation` 表一行是一个会话，`message` 表一行是一条事件，外键把它们连起来，`conversation_id` 上有索引。用户回来继续聊，就是 `select(Message).where(Message.conversation_id == ...)`。写一条新消息和更新会话的 `updated_at` 放在同一个 `Session` 里提交，保证不会出现"消息存了但会话时间没更新"。表结构以后加 `tokens` 列，用 Alembic 迁移而不是删库。

## 延伸阅读

- [SQLAlchemy 2.0 · Unified Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/index.html)（访问日期 2026-09-04）：官方教程，从 Core 讲到 ORM，读"Working with Data"和"Data Manipulation with the ORM"两章。
- [SQLAlchemy 2.0 · ORM Quick Start](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)（访问日期 2026-09-04）：一页纸版本，本模块的 `03`、`04` 就是照它的形状写的。
- [Alembic · Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)（访问日期 2026-09-04）：M2 用到迁移时再读。
- [PostgreSQL · Tutorial](https://www.postgresql.org/docs/current/tutorial.html)（访问日期 2026-09-04）：SQL 部分和 SQLite 通用，第 3 章讲事务和视图。

---

[← B00](../00-http-and-fastapi/README.md) · [B02 →](../02-testing/README.md)
