import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base
from models.base import TimestampMixin, UUIDMixin


class ReconciliationMode(str, enum.Enum):
    RECORD_TO_RECORD = "record_to_record"
    SETTLEMENT = "settlement"
    REVERSAL = "reversal"


class ReconciliationStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReconciliationRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "reconciliation_runs"

    mode: Mapped[str] = mapped_column(
        Enum(ReconciliationMode, name="recon_mode_enum", values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(ReconciliationStatus, name="recon_status_enum", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ReconciliationStatus.PENDING.value,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    total_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_mismatches: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        Index("ix_recon_runs_status", "status"),
        Index("ix_recon_runs_mode", "mode"),
    )

    def __repr__(self) -> str:
        return f"<ReconciliationRun {self.id} {self.mode} {self.status}>"


class ReconciliationRule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "reconciliation_rules"

    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    rule_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_system_a: Mapped[str] = mapped_column(String(100), nullable=False)
    source_system_b: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    config: Mapped[str | None] = mapped_column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<ReconciliationRule {self.name}>"
