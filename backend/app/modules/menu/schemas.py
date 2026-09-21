from typing import Any

from pydantic import BaseModel, Field


class LocationOut(BaseModel):
    id: int
    code: str
    name: str
    address: str = ""
    timezone: str
    is_open_now: bool


class OptionOut(BaseModel):
    id: int
    name: str
    price_delta: int
    visual: dict[str, Any] | None = None
    available: bool = True


class GroupOut(BaseModel):
    id: int
    key: str
    name: str
    min_select: int
    max_select: int
    required: bool
    default_option_ids: list[int] = []
    options: list[OptionOut] = []


class ProductOut(BaseModel):
    id: int
    slug: str
    name: str
    description: str = ""
    base_price: int
    image_url: str = ""
    video_url: str = ""
    poster_url: str = ""
    video_duration_sec: int | None = None
    video_steps: list[dict[str, Any]] | None = None
    tags: list[str] = []
    prep_units: int = 1
    available: bool = True
    groups: list[GroupOut] = []


class CategoryOut(BaseModel):
    id: int
    slug: str
    name: str
    products: list[ProductOut] = []


class MenuOut(BaseModel):
    location_id: int
    categories: list[CategoryOut] = []


class QuoteItemIn(BaseModel):
    product_id: int
    option_ids: list[int] = Field(default_factory=list)
    quantity: int = Field(default=1, ge=1, le=10)


class QuoteIn(BaseModel):
    items: list[QuoteItemIn] = Field(min_length=1, max_length=50)


class QuoteLineOut(BaseModel):
    product_id: int
    quantity: int
    unit_price: int
    line_total: int


class QuoteOut(BaseModel):
    lines: list[QuoteLineOut]
    total: int
    currency: str
