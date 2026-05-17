# BankOps Reconciliation Engine

A distributed reconciliation and operational intelligence system for detecting transaction inconsistencies across financial systems.

## Architecture

```
Transaction Simulator
      ↓
RabbitMQ
      ↓
Ingestion Service  ←→  REST API (batch)
      ↓
PostgreSQL
      ↓
Reconciliation Workers (APScheduler)
      ↓
Mismatch Engine (comparators + detectors)
      ↓
Alerting Service (Slack / Email)
      ↓
API Service (FastAPI) ← Next.js Dashboard
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| `api` | 8000 | Main operational API + dashboard backend |
| `ingestion` | 8001 | RabbitMQ consumer + REST ingestion endpoint |
| `reconciliation` | — | Scheduled reconciliation workers |
| `alerts` | — | Alert evaluation + notification dispatch |
| `rabbitmq` | 5672 / 15672 | Message queue |
| `postgres` | 5432 | Primary database |
| `redis` | 6379 | Cache + real-time state |
| `prometheus` | 9090 | Metrics |
| `grafana` | 3001 | Monitoring dashboards |
| `dashboard` | 3000 | Next.js operational dashboard |

## Quick Start

### 1. Clone and configure

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 2. Start infrastructure

```bash
docker-compose up -d postgres rabbitmq redis
```

### 3. Run database migrations

```bash
pip install -r requirements.txt
alembic upgrade head
```

### 4. Start all services

```bash
docker-compose up -d
```

### 5. Start the dashboard

```bash
cd dashboards
npm install
npm run dev
```
Dashboard: http://localhost:3000

### 6. Simulate transactions

```bash
# Publish 200 events to RabbitMQ
python -m workers.simulator --count 200

# Target a specific source system
python -m workers.simulator --count 100 --source gateway
python -m workers.simulator --count 100 --source ledger
```

### 7. Trigger a manual reconciliation run

```bash
curl -X POST http://localhost:8000/reconciliation/trigger \
  -H "Content-Type: application/json" \
  -d '{"mode": "record_to_record"}'
```

## API Reference

### Transactions
- `GET /transactions` — list with filters (`source_system`, `status`, `from_dt`, `to_dt`)
- `GET /transactions/{id}` — get single transaction
- `GET /transactions/summary` — total count

### Mismatches
- `GET /mismatches` — list with filters (`mismatch_type`, `status`, `run_id`)
- `GET /mismatches/summary` — counts by type
- `GET /mismatches/{id}` — mismatch detail
- `POST /mismatches/{id}/resolve` — resolve with notes

### Reconciliation
- `POST /reconciliation/trigger` — trigger a run (`record_to_record` | `settlement` | `reversal`)
- `GET /reconciliation/runs` — run history
- `GET /reconciliation/runs/{id}` — run detail

### Alerts
- `GET /alerts` — list with filters (`severity`, `status`, `alert_type`)
- `GET /alerts/summary` — open counts by severity
- `GET /alerts/{id}` — alert detail
- `POST /alerts/{id}/acknowledge` — acknowledge alert

### Dashboard
- `GET /dashboard/summary` — aggregated operational metrics

## Running Tests

```bash
pytest tests/ -v
```

## Mismatch Types

| Type | Description |
|------|-------------|
| `missing_transaction` | Exists in source A, absent in source B |
| `duplicate_transaction` | Same reference processed multiple times |
| `amount_mismatch` | Gateway amount ≠ ledger amount |
| `status_mismatch` | SUCCESS in gateway, FAILED in ledger |
| `delayed_reversal` | Reversal exceeds SLA threshold |
| `settlement_delay` | Settlement pending beyond threshold |
| `orphan_reversal` | Reversal references non-existent original |
| `ledger_inconsistency` | Currency or ledger field mismatch |

## Reconciliation Schedules

| Job | Default Interval |
|-----|-----------------|
| Record-to-record | Every 5 minutes |
| Settlement reconciliation | Hourly |
| Reversal reconciliation | Hourly |
| Alert evaluation | Every 30 seconds |

Intervals are configurable via `.env` (`RECON_SCHEDULE_MINUTES`).

## Project Structure

```
reconciliation-engine/
├── services/
│   ├── ingestion/      # RabbitMQ consumer + REST ingestion API
│   ├── reconciliation/ # Reconciliation engine + scheduler
│   ├── alerts/         # Alert evaluation + dispatch
│   └── api/            # FastAPI operational API
├── workers/
│   └── simulator.py    # Transaction event simulator
├── models/             # SQLAlchemy ORM models
├── repositories/       # Data access layer
├── comparators/        # Field-level comparison logic
├── detectors/          # Missing / duplicate detection
├── shared/             # Database, RabbitMQ, Redis, logging
├── config/             # Pydantic settings
├── dashboards/         # Next.js frontend
├── tests/              # Unit tests
├── alembic/            # DB migrations
├── infrastructure/
│   ├── db/             # init.sql
│   ├── prometheus/     # prometheus.yml
│   └── grafana/        # Grafana provisioning
└── docker/             # Per-service Dockerfiles
```

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy (async), APScheduler
- **Database**: PostgreSQL 16
- **Queue**: RabbitMQ 3.13
- **Cache**: Redis 7
- **Frontend**: Next.js 14, React, Recharts, Tailwind CSS
- **Observability**: Prometheus, Grafana, OpenTelemetry, structlog
- **Containerisation**: Docker Compose
