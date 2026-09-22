from datetime import datetime

from pydantic import BaseModel


class LevelOut(BaseModel):
    name: str
    next_name: str | None = None
    to_next_kopeks: int = 0


class AccountOut(BaseModel):
    phone: str
    balance: int
    lifetime_spent: int
    level: LevelOut


class TransactionOut(BaseModel):
    id: int
    type: str
    amount: int
    order_id: int | None = None
    created_at: datetime
