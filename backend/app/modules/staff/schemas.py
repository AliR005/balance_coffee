from pydantic import BaseModel


class LoginIn(BaseModel):
    location_id: int
    pin: str


class LoginOut(BaseModel):
    token: str
    location_id: int
    expires_at: int


class AvailabilityUpdateIn(BaseModel):
    is_available: bool


class ProductAvailabilityOut(BaseModel):
    id: int
    name: str
    available: bool


class OptionAvailabilityOut(BaseModel):
    id: int
    name: str
    group: str
    available: bool


class AvailabilityOut(BaseModel):
    location_id: int
    products: list[ProductAvailabilityOut]
    options: list[OptionAvailabilityOut]
