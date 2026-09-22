"""Заказы, слоты, статусы, staff. Revision 0003."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0003_orders"
down_revision = "0002_menu"
branch_labels = None
depends_on = None

JSONType = sa.JSON().with_variant(JSONB(), "postgresql")
TS = sa.DateTime(timezone=True)


def _ts_cols() -> list:
    return [
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", TS, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", TS, server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "orders",
        *_ts_cols(),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="confirmed"),
        sa.Column("mode", sa.String(16), nullable=False, server_default="on_site"),
        sa.Column("customer_name", sa.String(128), nullable=False),
        sa.Column("customer_phone", sa.String(32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False, server_default=""),
        sa.Column("pickup_at", TS, nullable=False),
        sa.Column("is_asap", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("units", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("total", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="RUB"),
        sa.Column("payment_method", sa.String(32), nullable=False, server_default="cash_on_pickup"),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("idempotency_hash", sa.String(64), nullable=False),
        sa.Column("access_token", sa.String(128), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
        sa.UniqueConstraint("access_token"),
    )
    op.create_table(
        "order_items",
        *_ts_cols(),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(128), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.BigInteger(), nullable=False),
        sa.Column("options", JSONType, nullable=False, server_default="[]"),
        sa.Column("line_total", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "slot_loads",
        *_ts_cols(),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("slot_start", TS, nullable=False),
        sa.Column("units_reserved", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_id", "slot_start"),
    )
    op.create_table(
        "order_status_events",
        *_ts_cols(),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.String(32), nullable=True),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("actor", sa.String(16), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "location_day_counters",
        *_ts_cols(),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("last_n", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_id", "day"),
    )


def downgrade() -> None:
    op.drop_table("location_day_counters")
    op.drop_table("order_status_events")
    op.drop_table("slot_loads")
    op.drop_table("order_items")
    op.drop_table("orders")
