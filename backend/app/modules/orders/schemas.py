from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class OrderItemIn(BaseModel):
    product_id: int
    option_ids: list[int] = Field(default_factory=list)
    quantity: int = Field(default=1, ge=1, le=10)


class OrderCreateIn(BaseModel):
    location_id: int
    mode: str = Field(default="on_site", pattern="^(on_site|scheduled)$")
    pickup_at: datetime | None = None
    items: list[OrderItemIn] = Field(min_length=1, max_length=50)
    customer_name: str = Field(min_length=1, max_length=128)
    customer_phone: str = Field(min_length=5, max_length=32)
    comment: str = Field(default="", max_length=500)
    # Точка расширения фазы 06b: принимается, списание делает фаза 06b.
    use_bonus_points: int = Field(default=0, ge=0)


class OrderItemOut(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: int
    options: list[dict[str, Any]]
    line_total: int


class OrderOut(BaseModel):
    id: int
    code: str
    location_id: int
    status: str
    mode: str
    customer_name: str
    customer_phone: str
    comment: str = ""
    pickup_at: datetime
    is_asap: bool
    total: int
    currency: str
    payment_method: str
    bonus_applied: int = 0
    items: list[OrderItemOut] = []
    created_at: datetime


class OrderCreateOut(BaseModel):
    order: OrderOut
    access_token: str


class SlotOut(BaseModel):
    start: datetime
    available: bool
    remaining: int


class SlotsOut(BaseModel):
    location_id: int
    open: bool
    units: int
    asap: SlotOut | None = None
    slots: list[SlotOut] = []


class StatusChangeIn(BaseModel):
    to_status: str
