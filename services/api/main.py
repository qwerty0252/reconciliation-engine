from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from shared.database import create_tables
from shared.logging import configure_logging, get_logger
from services.api.routers import transactions, mismatches, reconciliation, alerts, dashboard

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await create_tables()
    logger.info("api_service_started")
    yield
    logger.info("api_service_stopped")


app = FastAPI(
    title="BankOps Reconciliation Engine API",
    description="Operational API for transaction reconciliation and monitoring",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

app.include_router(transactions.router)
app.include_router(mismatches.router)
app.include_router(reconciliation.router)
app.include_router(alerts.router)
app.include_router(dashboard.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "api"}
