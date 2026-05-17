import enum
import uuid

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from shared.database import Base
from models.base import TimestampMixin, UUIDMixin


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertType(str, enum.Enum):
    HIGH_MISMATCH_VOLUME = "high_mismatch_volume"
    SETTLEMENT_DELAY = "settlement_delay"
    REVERSAL_FAILURE = "reversal_failure"
    RECONCILIATION_JOB_FAILURE = "reconciliation_job_failure"
    DUPLICATE_SPIKE = "duplicate_spike"
    MISSING_TRANSACTION_SPIKE = "missing_transaction_spike"


class Alert(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "alerts"

    alert_type: Mapped[str] = mapped_column(
        Enum(AlertType, name="alert_type_enum", values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    severity: Mapped[str] = mapped_column(
        Enum(AlertSeverity, name="alert_severity_enum", values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(AlertStatus, name="alert_status_enum", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=AlertStatus.OPEN.value,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    mismatch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mismatches.id", ondelete="SET NULL"),
        nullable=True,
    )
    reconciliation_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reconciliation_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    slack_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_alerts_severity", "severity"),
        Index("ix_alerts_status", "status"),
        Index("ix_alerts_type", "alert_type"),
    )

    def __repr__(self) -> str:
        return f"<Alert {self.alert_type} {self.severity} {self.status}>"
