"""SQLAlchemy table definitions. The event log is the truth; conversation.status is a cache of it."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversation"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # Thread.thread_id, e.g. thr_1a2b3c4d
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="new")  # cache; derive from message when in doubt


class Message(Base):
    """One row per thread event. ``seq`` is the event's index; the unique constraint is the optimistic lock."""

    __tablename__ = "message"
    __table_args__ = (UniqueConstraint("conversation_id", "seq", name="uq_message_conversation_seq"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False, index=True)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Task(Base):
    """One row per run: opened by run_started, closed by run_finished / run_failed."""

    __tablename__ = "task"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stop_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens_in: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# Storage-level guard for the one transition M2 forbids. Python checks it too; this is the backstop
# for any writer that bypasses the store. Raised with the check_violation SQLSTATE (23514).
# Kept as separate statements: asyncpg executes one statement per call.
TRANSITION_TRIGGER_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION message_check_transition() RETURNS trigger AS $$
DECLARE prev_type text;
BEGIN
  SELECT type INTO prev_type FROM message
   WHERE conversation_id = NEW.conversation_id AND seq = NEW.seq - 1;
  IF NEW.type = 'assistant_message' AND prev_type = 'human_input_requested' THEN
    RAISE EXCEPTION 'invalid_transition: assistant_message cannot follow human_input_requested'
      USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql
"""

TRANSITION_TRIGGER_SQL = """
CREATE TRIGGER message_check_transition BEFORE INSERT ON message
FOR EACH ROW EXECUTE FUNCTION message_check_transition()
"""

TRANSITION_TRIGGER_DROP_SQL = [
    "DROP TRIGGER IF EXISTS message_check_transition ON message",
    "DROP FUNCTION IF EXISTS message_check_transition()",
]
