"""document, chunk (pgvector + tsvector) and memory tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-04
"""

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "document",
        sa.Column("tenant_id", sa.Text, nullable=False),
        sa.Column("doc_id", sa.String(200), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("title", sa.Text, nullable=False, server_default=""),
        sa.Column("indexed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "doc_id"),
    )
    op.create_table(
        "chunk",
        sa.Column("tenant_id", sa.Text, nullable=False),
        sa.Column("chunk_id", sa.String(220), nullable=False),
        sa.Column("doc_id", sa.String(200), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("section", sa.Text, nullable=False),
        sa.Column("start", sa.Integer, nullable=False),
        sa.Column("end", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("content_hash", sa.String(32), nullable=False),
        sa.Column("embedding", Vector(), nullable=True),
        sa.Column("embedding_model", sa.Text, nullable=True),
        sa.Column("tsv", TSVECTOR, sa.Computed("to_tsvector('simple', text)", persisted=True)),
        sa.PrimaryKeyConstraint("tenant_id", "chunk_id"),
    )
    op.create_index("ix_chunk_tenant_doc", "chunk", ["tenant_id", "doc_id"])
    op.create_index("ix_chunk_tsv", "chunk", ["tsv"], postgresql_using="gin")
    op.create_table(
        "memory",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.Text, nullable=False),
        sa.Column("user_id", sa.Text, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("kind", sa.Text, nullable=False),
        sa.Column("subject", sa.Text, nullable=False),
        sa.Column("source_thread_id", sa.String(64), nullable=False),
        sa.Column("source_event_seqs", ARRAY(sa.Integer), nullable=False),
        sa.Column("embedding", Vector(), nullable=True),
        sa.Column("embedding_model", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("superseded_by", sa.String(64), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_reason", sa.Text, nullable=True),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_memory_tenant_user", "memory", ["tenant_id", "user_id"])


def downgrade() -> None:
    op.drop_table("memory")
    op.drop_index("ix_chunk_tsv", table_name="chunk")
    op.drop_index("ix_chunk_tenant_doc", table_name="chunk")
    op.drop_table("chunk")
    op.drop_table("document")
