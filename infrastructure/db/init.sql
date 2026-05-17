-- BankOps Reconciliation Engine — Initial Schema
-- This runs on first PostgreSQL container start.
-- Alembic manages subsequent migrations.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Transactions
CREATE TABLE IF NOT EXISTS transactions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id  VARCHAR(100) NOT NULL,
    reference       VARCHAR(200) NOT NULL,
    amount          NUMERIC(18,2) NOT NULL,
    currency        VARCHAR(3) NOT NULL,
    status          VARCHAR(50) NOT NULL,
    source_system   VARCHAR(100) NOT NULL,
    transaction_type VARCHAR(50),
    reversal_reference VARCHAR(200),
    settlement_id   VARCHAR(200),
    timestamp       TIMESTAMPTZ NOT NULL,
    raw_payload     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_txn_source UNIQUE (transaction_id, source_system)
);
CREATE INDEX IF NOT EXISTS ix_transactions_reference    ON transactions (reference);
CREATE INDEX IF NOT EXISTS ix_transactions_status       ON transactions (status);
CREATE INDEX IF NOT EXISTS ix_transactions_source       ON transactions (source_system);
CREATE INDEX IF NOT EXISTS ix_transactions_timestamp    ON transactions (timestamp);

-- Reconciliation runs
CREATE TYPE IF NOT EXISTS recon_mode_enum   AS ENUM ('record_to_record','settlement','reversal');
CREATE TYPE IF NOT EXISTS recon_status_enum AS ENUM ('pending','running','completed','failed');

CREATE TABLE IF NOT EXISTS reconciliation_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mode            recon_mode_enum NOT NULL,
    status          recon_status_enum NOT NULL DEFAULT 'pending',
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    total_processed INTEGER NOT NULL DEFAULT 0,
    total_mismatches INTEGER NOT NULL DEFAULT 0,
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Reconciliation rules
CREATE TABLE IF NOT EXISTS reconciliation_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(200) NOT NULL UNIQUE,
    description     TEXT,
    rule_type       VARCHAR(100) NOT NULL,
    source_system_a VARCHAR(100) NOT NULL,
    source_system_b VARCHAR(100) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    config          TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Mismatches
CREATE TYPE IF NOT EXISTS mismatch_type_enum AS ENUM (
    'missing_transaction','duplicate_transaction','amount_mismatch',
    'status_mismatch','delayed_reversal','settlement_delay',
    'orphan_reversal','ledger_inconsistency','timeout_inconsistency'
);
CREATE TYPE IF NOT EXISTS mismatch_status_enum AS ENUM ('open','acknowledged','resolved','ignored');

CREATE TABLE IF NOT EXISTS mismatches (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reconciliation_run_id UUID REFERENCES reconciliation_runs(id) ON DELETE SET NULL,
    mismatch_type       mismatch_type_enum NOT NULL,
    status              mismatch_status_enum NOT NULL DEFAULT 'open',
    reference           VARCHAR(200) NOT NULL,
    source_system_a     VARCHAR(100),
    source_system_b     VARCHAR(100),
    transaction_id_a    VARCHAR(100),
    transaction_id_b    VARCHAR(100),
    description         TEXT,
    details             TEXT,
    resolution_notes    TEXT,
    alert_sent          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_mismatches_type    ON mismatches (mismatch_type);
CREATE INDEX IF NOT EXISTS ix_mismatches_status  ON mismatches (status);
CREATE INDEX IF NOT EXISTS ix_mismatches_ref     ON mismatches (reference);

-- Alerts
CREATE TYPE IF NOT EXISTS alert_type_enum AS ENUM (
    'high_mismatch_volume','settlement_delay','reversal_failure',
    'reconciliation_job_failure','duplicate_spike','missing_transaction_spike'
);
CREATE TYPE IF NOT EXISTS alert_severity_enum AS ENUM ('info','warning','critical');
CREATE TYPE IF NOT EXISTS alert_status_enum   AS ENUM ('open','acknowledged','resolved');

CREATE TABLE IF NOT EXISTS alerts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type          alert_type_enum NOT NULL,
    severity            alert_severity_enum NOT NULL,
    status              alert_status_enum NOT NULL DEFAULT 'open',
    title               VARCHAR(300) NOT NULL,
    message             TEXT NOT NULL,
    mismatch_id         UUID REFERENCES mismatches(id) ON DELETE SET NULL,
    reconciliation_run_id UUID REFERENCES reconciliation_runs(id) ON DELETE SET NULL,
    email_sent          BOOLEAN NOT NULL DEFAULT FALSE,
    slack_sent          BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_at     TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_alerts_severity ON alerts (severity);
CREATE INDEX IF NOT EXISTS ix_alerts_status   ON alerts (status);
CREATE INDEX IF NOT EXISTS ix_alerts_type     ON alerts (alert_type);
