"""cost_ledger: one row per charged model call, summarised per tenant per day

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-04
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cost_ledger",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Text, nullable=False),
        sa.Column("day", sa.Date, nullable=False),
        sa.Column("model", sa.Text, nullable=False),
        sa.Column("input_tokens", sa.Integer, nullable=False),
        sa.Column("output_tokens", sa.Integer, nullable=False),
        sa.Column("cost_usd", sa.Numeric(12, 6), nullable=False),
        sa.Column("calls", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cost_ledger_tenant_day", "cost_ledger", ["tenant_id", "day"])


def downgrade() -> None:
    op.drop_index("ix_cost_ledger_tenant_day", table_name="cost_ledger")
    op.drop_table("cost_ledger")
