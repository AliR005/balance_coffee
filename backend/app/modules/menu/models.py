from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
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

# JSONB на postgres, обычный JSON на sqlite (тесты без docker всё равно идут на pg,
# но совместимость не помешает).
JSONType = JSON().with_variant(JSONB(), "postgresql")


class Location(TimestampMixin, Base):
    __tablename__ = "locations"

    code: Mapped[str] = mapped_column(String(16), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    address: Mapped[str] = mapped_column(String(256), default="")
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")
    opening_hours: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    lead_time_min: Mapped[int] = mapped_column(Integer, default=10)
    slot_step_min: Mapped[int] = mapped_column(Integer, default=15)
    slot_capacity: Mapped[int] = mapped_column(Integer, default=6)
    staff_pin_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    slug: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    sort: Mapped[int] = mapped_column(Integer, default=0)


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")
    base_price: Mapped[int] = mapped_column(BigInteger)  # минорные единицы (копейки)
    image_url: Mapped[str] = mapped_column(String(512), default="")
    video_url: Mapped[str] = mapped_column(String(512), default="")
    poster_url: Mapped[str] = mapped_column(String(512), default="")
    video_duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_steps: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONType, nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSONType, default=list)
    prep_units: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class OptionGroup(TimestampMixin, Base):
    __tablename__ = "option_groups"

    key: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    min_select: Mapped[int] = mapped_column(Integer, default=0)
    max_select: Mapped[int] = mapped_column(Integer, default=1)


class ProductOptionGroup(TimestampMixin, Base):
    __tablename__ = "product_option_groups"

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    group_id: Mapped[int] = mapped_column(ForeignKey("option_groups.id", ondelete="CASCADE"))
    sort: Mapped[int] = mapped_column(Integer, default=0)
    default_option_ids: Mapped[list[int]] = mapped_column(JSONType, default=list)
    min_select: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_select: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (UniqueConstraint("product_id", "group_id"),)


class Option(TimestampMixin, Base):
    __tablename__ = "options"

    group_id: Mapped[int] = mapped_column(ForeignKey("option_groups.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(128))
    price_delta: Mapped[int] = mapped_column(BigInteger, default=0)
    sort: Mapped[int] = mapped_column(Integer, default=0)
    visual: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)

    __table_args__ = (UniqueConstraint("group_id", "name"),)


class LocationProductAvailability(TimestampMixin, Base):
    __tablename__ = "location_product_availability"

    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("location_id", "product_id"),)


class LocationOptionAvailability(TimestampMixin, Base):
    __tablename__ = "location_option_availability"

    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"))
    option_id: Mapped[int] = mapped_column(ForeignKey("options.id", ondelete="CASCADE"))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("location_id", "option_id"),)
