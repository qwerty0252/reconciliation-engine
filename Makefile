VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn
ALEMBIC := $(VENV)/bin/alembic
PYTEST := $(VENV)/bin/pytest

.PHONY: help install db-setup migrate api ingestion reconciliation alerts simulate test lint

help:
	@echo ""
	@echo "BankOps Reconciliation Engine — Local Dev"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Create venv and install dependencies"
	@echo "  make db-setup       Create PostgreSQL user + database"
	@echo "  make migrate        Run Alembic migrations"
	@echo ""
	@echo "Run services (each in a separate terminal):"
	@echo "  make api            Start API service         → http://localhost:8002"
	@echo "  make ingestion      Start Ingestion service   → http://localhost:8003"
	@echo "  make reconciliation Start Reconciliation scheduler"
	@echo "  make alerts         Start Alert engine"
	@echo ""
	@echo "Dev tools:"
	@echo "  make simulate       Publish 200 test events to RabbitMQ"
	@echo "  make test           Run unit tests"
	@echo "  make docs           Open API docs in browser"

# ── Setup ──────────────────────────────────────────────────────────────────────

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip -q
	$(PIP) install -r requirements.txt

db-setup:
	@echo "Creating PostgreSQL user and database..."
	psql -U postgres -c "CREATE USER bankops WITH PASSWORD 'bankops_secret';" 2>/dev/null || true
	createdb -U postgres -O bankops bankops_reconciliation 2>/dev/null || true
	psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE bankops_reconciliation TO bankops;" 2>/dev/null || true
	@echo "Creating RabbitMQ user..."
	rabbitmqctl add_user bankops bankops_secret 2>/dev/null || true
	rabbitmqctl set_permissions -p / bankops ".*" ".*" ".*" 2>/dev/null || true
	@echo "Done."

migrate:
	$(ALEMBIC) upgrade head

# ── Services ───────────────────────────────────────────────────────────────────

api:
	$(UVICORN) services.api.main:app --host 0.0.0.0 --port 8002 --reload

ingestion:
	$(UVICORN) services.ingestion.api:app --host 0.0.0.0 --port 8003 --reload

reconciliation:
	$(PYTHON) -m services.reconciliation.scheduler

alerts:
	$(PYTHON) -m services.alerts.runner

# ── Dev ────────────────────────────────────────────────────────────────────────

simulate:
	$(PYTHON) -m workers.simulator --count 200 --source gateway
	$(PYTHON) -m workers.simulator --count 200 --source ledger
	$(PYTHON) -m workers.simulator --count 100 --source switch

test:
	$(PYTEST) tests/ -v

docs:
	open http://localhost:8002/docs
