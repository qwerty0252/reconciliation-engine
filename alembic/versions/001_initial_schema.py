"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enums
    recon_mode = postgresql.ENUM(
        "record_to_record", "settlement", "reversal",
        name="recon_mode_enum", create_type=False
    )
    recon_status = postgresql.ENUM(
        "pending", "running", "completed", "failed",
        name="recon_status_enum", create_type=False
    )
    mismatch_type = postgresql.ENUM(
        "missing_transaction", "duplicate_transaction", "amount_mismatch",
        "status_mismatch", "delayed_reversal", "settlement_delay",
        "orphan_reversal", "ledger_inconsistency", "timeout_inconsistency",
        name="mismatch_type_enum", create_type=False
    )
    mismatch_status = postgresql.ENUM(
        "open", "acknowledged", "resolved", "ignored",
        name="mismatch_status_enum", create_type=False
    )
    alert_type = postgresql.ENUM(
        "high_mismatch_volume", "settlement_delay", "reversal_failure",
        "reconciliation_job_failure", "duplicate_spike", "missing_transaction_spike",
        name="alert_type_enum", create_type=False
    )
    alert_severity = postgresql.ENUM(
        "info", "warning", "critical",
        name="alert_severity_enum", create_type=False
    )
    alert_status = postgresql.ENUM(
        "open", "acknowledged", "resolved",
        name="alert_status_enum", create_type=False
    )

    for e in [recon_mode, recon_status, mismatch_type, mismatch_status,
              alert_type, alert_severity, alert_status]:
        e.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("transaction_id", sa.String(100), nullable=False),
        sa.Column("reference", sa.String(200), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("source_system", sa.String(100), nullable=False),
        sa.Column("transaction_type", sa.String(50)),
        sa.Column("reversal_reference", sa.String(200)),
        sa.Column("settlement_id", sa.String(200)),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("transaction_id", "source_system", name="uq_txn_source"),
    )

    op.create_table(
        "reconciliation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mode", recon_mode, nullable=False),
        sa.Column("status", recon_status, nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("total_processed", sa.Integer, default=0),
        sa.Column("total_mismatches", sa.Integer, default=0),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "reconciliation_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("rule_type", sa.String(100), nullable=False),
        sa.Column("source_system_a", sa.String(100), nullable=False),
        sa.Column("source_system_b", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("config", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "mismatches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reconciliation_run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("reconciliation_runs.id", ondelete="SET NULL")),
        sa.Column("mismatch_type", mismatch_type, nullable=False),
        sa.Column("status", mismatch_status, nullable=False, server_default="open"),
        sa.Column("reference", sa.String(200), nullable=False),
        sa.Column("source_system_a", sa.String(100)),
        sa.Column("source_system_b", sa.String(100)),
        sa.Column("transaction_id_a", sa.String(100)),
        sa.Column("transaction_id_b", sa.String(100)),
        sa.Column("description", sa.Text),
        sa.Column("details", sa.Text),
        sa.Column("resolution_notes", sa.Text),
        sa.Column("alert_sent", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("alert_type", alert_type, nullable=False),
        sa.Column("severity", alert_severity, nullable=False),
        sa.Column("status", alert_status, nullable=False, server_default="open"),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("mismatch_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("mismatches.id", ondelete="SET NULL")),
        sa.Column("reconciliation_run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("reconciliation_runs.id", ondelete="SET NULL")),
        sa.Column("email_sent", sa.Boolean, default=False),
        sa.Column("slack_sent", sa.Boolean, default=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("mismatches")
    op.drop_table("reconciliation_rules")
    op.drop_table("reconciliation_runs")
    op.drop_table("transactions")
