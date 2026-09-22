from sqlalchemy import BigInteger, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base, TimestampMixin


class BonusAccount(TimestampMixin, Base):
    __tablename__ = "bonus_accounts"

    phone: Mapped[str] = mapped_column(String(32), unique=True)
    balance: Mapped[int] = mapped_column(Integer, default=0)  # баллы; 1 балл = 1 рубль
    lifetime_spent: Mapped[int] = mapped_column(BigInteger, default=0)  # копейки
    guest_token: Mapped[str] = mapped_column(String(128), default="")


class BonusTransaction(TimestampMixin, Base):
    __tablename__ = "bonus_transactions"

    account_id: Mapped[int] = mapped_column(ForeignKey("bonus_accounts.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(16))  # accrual | redeem | adjust
    amount: Mapped[int] = mapped_column(Integer)  # +начисление, −списание
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (UniqueConstraint("order_id", "type"),)
