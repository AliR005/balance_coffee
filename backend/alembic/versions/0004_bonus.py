"""Бонусы. Revision 0004."""

import sqlalchemy as sa

from alembic import op

revision = "0004_bonus"
down_revision = "0003_orders"
branch_labels = None
depends_on = None

TS = sa.DateTime(timezone=True)


def _ts_cols() -> list:
    return [
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", TS, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", TS, server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "bonus_accounts",
        *_ts_cols(),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lifetime_spent", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("guest_token", sa.String(128), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone"),
    )
    op.create_table(
        "bonus_transactions",
        *_ts_cols(),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["bonus_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", "type"),
    )
    op.add_column(
        "orders", sa.Column("bonus_redeemed", sa.Integer(), nullable=False, server_default="0")
    )


def downgrade() -> None:
    op.drop_column("orders", "bonus_redeemed")
    op.drop_table("bonus_transactions")
    op.drop_table("bonus_accounts")
