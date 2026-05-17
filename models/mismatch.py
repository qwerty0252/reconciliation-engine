import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base
from models.base import TimestampMixin, UUIDMixin


class MismatchType(str, enum.Enum):
    MISSING_TRANSACTION = "missing_transaction"
    DUPLICATE_TRANSACTION = "duplicate_transaction"
    AMOUNT_MISMATCH = "amount_mismatch"
    STATUS_MISMATCH = "status_mismatch"
    DELAYED_REVERSAL = "delayed_reversal"
    SETTLEMENT_DELAY = "settlement_delay"
    ORPHAN_REVERSAL = "orphan_reversal"
    LEDGER_INCONSISTENCY = "ledger_inconsistency"
    TIMEOUT_INCONSISTENCY = "timeout_inconsistency"


class MismatchStatus(str, enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class Mismatch(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "mismatches"

    reconciliation_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reconciliation_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    mismatch_type: Mapped[str] = mapped_column(
        Enum(MismatchType, name="mismatch_type_enum", values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(MismatchStatus, name="mismatch_status_enum", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=MismatchStatus.OPEN.value,
    )
    reference: Mapped[str] = mapped_column(String(200), nullable=False)
    source_system_a: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_system_b: Mapped[str | None] = mapped_column(String(100), nullable=True)
    transaction_id_a: Mapped[str | None] = mapped_column(String(100), nullable=True)
    transaction_id_b: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    details: Mapped[str | None] = mapped_column(String, nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(String, nullable=True)
    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("ix_mismatches_type", "mismatch_type"),
        Index("ix_mismatches_status", "status"),
        Index("ix_mismatches_reference", "reference"),
        Index("ix_mismatches_recon_run", "reconciliation_run_id"),
    )

    def __repr__(self) -> str:
        return f"<Mismatch {self.mismatch_type} ref={self.reference} {self.status}>"
