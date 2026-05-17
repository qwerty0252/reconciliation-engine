import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base
from models.base import TimestampMixin, UUIDMixin


class Transaction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(String(100), nullable=False)
    reference: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    source_system: Mapped[str] = mapped_column(String(100), nullable=False)
    transaction_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reversal_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    settlement_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_payload: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        # Deduplication: same transaction_id from same source_system
        UniqueConstraint("transaction_id", "source_system", name="uq_txn_source"),
        Index("ix_transactions_reference", "reference"),
        Index("ix_transactions_status", "status"),
        Index("ix_transactions_source_system", "source_system"),
        Index("ix_transactions_timestamp", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.transaction_id} {self.source_system} {self.status}>"
