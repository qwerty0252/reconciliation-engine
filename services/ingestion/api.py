import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status
from pydantic import ValidationError

from shared.database import get_db, create_tables
from shared.logging import configure_logging, get_logger
from services.ingestion.validator import TransactionEventSchema
from services.ingestion.normalizer import normalize
from services.ingestion.consumer import start_consumer
from repositories.transaction_repository import TransactionRepository
from prometheus_fastapi_instrumentator import Instrumentator

logger = get_logger(__name__)

_consumer_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await create_tables()
    global _consumer_task
    _consumer_task = asyncio.create_task(start_consumer())
    logger.info("ingestion_service_started")
    yield
    if _consumer_task:
        _consumer_task.cancel()
    logger.info("ingestion_service_stopped")


app = FastAPI(
    title="BankOps Ingestion Service",
    version="1.0.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)


@app.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_transaction(
    payload: TransactionEventSchema,
    background_tasks: BackgroundTasks,
    session=Depends(get_db),
):
    """REST ingestion endpoint for single transaction events."""
    repo = TransactionRepository(session)
    existing = await repo.get_by_transaction_id_and_source(
        payload.transaction_id, payload.source_system
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transaction already ingested",
        )

    data = normalize(payload)
    txn = await repo.create(data)
    logger.info(
        "transaction_ingested_rest",
        id=str(txn.id),
        transaction_id=txn.transaction_id,
    )
    return {"id": str(txn.id), "status": "accepted"}


@app.post("/ingest/batch", status_code=status.HTTP_202_ACCEPTED)
async def ingest_batch(
    payloads: list[TransactionEventSchema],
    session=Depends(get_db),
):
    """Batch ingestion endpoint (CSV/JSON upload equivalent)."""
    if len(payloads) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size exceeds limit of 1000",
        )

    repo = TransactionRepository(session)
    ingested, skipped = 0, 0

    for payload in payloads:
        existing = await repo.get_by_transaction_id_and_source(
            payload.transaction_id, payload.source_system
        )
        if existing:
            skipped += 1
            continue
        await repo.create(normalize(payload))
        ingested += 1

    return {"ingested": ingested, "skipped": skipped}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ingestion"}
