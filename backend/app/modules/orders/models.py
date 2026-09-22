from datetime import date as date_cls
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.base import Base, TimestampMixin

JSONType = JSON().with_variant(JSONB(), "postgresql")

# Статусы (SPEC 5.5). pending_payment зарезервирован, в MVP не используется.
CONFIRMED = "confirmed"
PREPARING = "preparing"
READY = "ready"
PICKED_UP = "picked_up"
CANCELLED = "cancelled"

ACTIVE_STATUSES = (CONFIRMED, PREPARING, READY)

# mode (SPEC 10.1)
ON_SITE = "on_site"
SCHEDULED = "scheduled"


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    code: Mapped[str] = mapped_column(String(16))
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(32), default=CONFIRMED)
    mode: Mapped[str] = mapped_column(String(16), default=ON_SITE)
    customer_name: Mapped[str] = mapped_column(String(128))
    customer_phone: Mapped[str] = mapped_column(String(32))
    comment: Mapped[str] = mapped_column(Text, default="")
    pickup_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_asap: Mapped[bool] = mapped_column(default=False)
    units: Mapped[int] = mapped_column(Integer, default=1)  # снапшот нагрузки на слот
    bonus_redeemed: Mapped[int] = mapped_column(Integer, default=0)  # баллы, списанные на заказ
    total: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(8), default="RUB")
    payment_method: Mapped[str] = mapped_column(String(32), default="cash_on_pickup")
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    idempotency_hash: Mapped[str] = mapped_column(String(64))
    access_token: Mapped[str] = mapped_column(String(128), unique=True)


class OrderItem(TimestampMixin, Base):
    __tablename__ = "order_items"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    product_name: Mapped[str] = mapped_column(String(128))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[int] = mapped_column(BigInteger)
    options: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, default=list)
    line_total: Mapped[int] = mapped_column(BigInteger)


class SlotLoad(TimestampMixin, Base):
    __tablename__ = "slot_loads"

    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"))
    slot_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    units_reserved: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (UniqueConstraint("location_id", "slot_start"),)


class OrderStatusEvent(TimestampMixin, Base):
    __tablename__ = "order_status_events"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32))
    actor: Mapped[str] = mapped_column(String(16))


class LocationDayCounter(TimestampMixin, Base):
    __tablename__ = "location_day_counters"

    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"))
    day: Mapped[date_cls] = mapped_column(Date)
    last_n: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (UniqueConstraint("location_id", "day"),)
