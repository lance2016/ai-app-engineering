"""conversation, message and task tables plus the transition trigger

Revision ID: 0001
Revises:
Create Date: 2026-09-04
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

from aiapp.storage.models import TRANSITION_TRIGGER_DROP_SQL, TRANSITION_TRIGGER_FUNCTION_SQL, TRANSITION_TRIGGER_SQL

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversation",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status", sa.Text, nullable=False),
    )
    op.create_index("ix_conversation_tenant_id", "conversation", ["tenant_id"])
    op.create_table(
        "message",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("conversation_id", sa.String(64), sa.ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seq", sa.Integer, nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("data", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("conversation_id", "seq", name="uq_message_conversation_seq"),
    )
    op.create_index("ix_message_conversation_id", "message", ["conversation_id"])
    op.create_table(
        "task",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("conversation_id", sa.String(64), sa.ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stop_reason", sa.Text, nullable=True),
        sa.Column("tokens_in", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_task_conversation_id", "task", ["conversation_id"])
    op.execute(TRANSITION_TRIGGER_FUNCTION_SQL)
    op.execute(TRANSITION_TRIGGER_SQL)


def downgrade() -> None:
    for statement in TRANSITION_TRIGGER_DROP_SQL:
        op.execute(statement)
    op.drop_table("task")
    op.drop_table("message")
    op.drop_table("conversation")
