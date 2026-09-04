"""SQLAlchemy 2.0: describe tables as Python classes, work with objects instead of rows.

Run:  uv run python prerequisites/backend/01-sql-and-sqlalchemy/code/03_sqlalchemy_models.py
Expect: the CREATE TABLE statements SQLAlchemy generates, then a conversation
        loaded back with its two messages.
"""

# %% imports
import sys

try:
    from sqlalchemy import ForeignKey, String, create_engine, select
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
    title: Mapped[str] = mapped_column(String(80))
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "message"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversation.id"))
    role: Mapped[str]
    content: Mapped[str]
    conversation: Mapped[Conversation] = relationship(back_populates="messages")


# %% create_schema
engine = create_engine("sqlite:///:memory:", echo=True)  # echo shows the SQL it runs
Base.metadata.create_all(engine)
engine.echo = False

# %% write_and_read
with Session(engine) as session:
    conv = Conversation(title="weather chat")
    conv.messages.append(Message(role="user", content="weather in Shenzhen?"))
    conv.messages.append(Message(role="assistant", content="31°C and sunny"))
    session.add(conv)
    session.commit()  # one transaction: conversation + both messages

with Session(engine) as session:
    loaded = session.scalars(select(Conversation).where(Conversation.title == "weather chat")).one()
    print(f"\n{loaded.title}: {[(m.role, m.content) for m in loaded.messages]}")
