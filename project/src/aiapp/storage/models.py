"""SQLAlchemy table definitions. The event log is the truth; conversation.status is a cache of it."""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, BigInteger, Boolean, Computed, DateTime, ForeignKey, Index, Integer, PrimaryKeyConstraint, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
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


# ---- M4: knowledge and memory ------------------------------------------------------------------


class DocumentRow(Base):
    """One row per (tenant, document): the version currently indexed."""

    __tablename__ = "document"
    __table_args__ = (PrimaryKeyConstraint("tenant_id", "doc_id"),)

    tenant_id: Mapped[str] = mapped_column(Text, nullable=False)
    doc_id: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ChunkRow(Base):
    """A contiguous slice of a document version. ``embedding`` is untyped ``vector`` so any model's dimension fits;
    searches filter on ``embedding_model`` so vectors from different spaces are never compared. Add a typed column
    plus an HNSW index once the model is fixed (M5)."""

    __tablename__ = "chunk"
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "chunk_id"),
        Index("ix_chunk_tenant_doc", "tenant_id", "doc_id"),
        Index("ix_chunk_tsv", "tsv", postgresql_using="gin"),
    )

    tenant_id: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_id: Mapped[str] = mapped_column(String(220), nullable=False)
    doc_id: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[str] = mapped_column(Text, nullable=False)
    start: Mapped[int] = mapped_column(Integer, nullable=False)
    end: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(32), nullable=False)
    embedding = mapped_column(Vector(), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(Text, nullable=True)
    tsv = mapped_column(TSVECTOR, Computed("to_tsvector('simple', text)", persisted=True))


class MemoryRow(Base):
    """A durable fact about a user with provenance. Soft-deleted so a deletion can be proven later."""

    __tablename__ = "memory"
    __table_args__ = (Index("ix_memory_tenant_user", "tenant_id", "user_id"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    source_thread_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_event_seqs: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    embedding = mapped_column(Vector(), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    superseded_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


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
