"""Filtering, joining, counting, updating and deleting through the ORM.

Run:  uv run python prerequisites/backend/01-sql-and-sqlalchemy/code/04_sqlalchemy_queries.py
Expect: message counts per conversation, the edited content, and cascade delete
        leaving zero orphan messages.
"""

# %% imports
import sys

try:
    from sqlalchemy import ForeignKey, create_engine, func, select
    from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
except ImportError:
    print("sqlalchemy is not installed. Run: uv sync --all-groups")
    sys.exit(0)


# %% models
class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversation"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "message"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversation.id"))
    role: Mapped[str]
    content: Mapped[str]
    conversation: Mapped[Conversation] = relationship(back_populates="messages")


engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)

# %% seed
with Session(engine) as s:
    s.add_all([
        Conversation(title="weather", messages=[Message(role="user", content="hot?"), Message(role="assistant", content="yes")]),
        Conversation(title="travel", messages=[Message(role="user", content="Tokyo flights")]),
    ])
    s.commit()

# %% count_per_conversation
with Session(engine) as s:
    stmt = (
        select(Conversation.title, func.count(Message.id))
        .join(Message)
        .group_by(Conversation.id)
        .order_by(Conversation.title)
    )
    for title, n in s.execute(stmt):
        print(f"{title}: {n} messages")

# %% update
with Session(engine) as s:
    msg = s.scalars(select(Message).where(Message.content == "yes")).one()
    msg.content = "yes, 31°C"
    s.commit()
    print(s.scalars(select(Message.content).where(Message.role == "assistant")).one())

# %% delete_cascade
with Session(engine) as s:
    weather = s.scalars(select(Conversation).where(Conversation.title == "weather")).one()
    s.delete(weather)
    s.commit()
    print("messages left:", s.scalar(select(func.count(Message.id))))
