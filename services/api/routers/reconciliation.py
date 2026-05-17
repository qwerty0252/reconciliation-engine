import uuid

from fastapi import APIRouter, Depends, Query, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from repositories.reconciliation_repository import ReconciliationRepository
from models.reconciliation_run import ReconciliationMode, ReconciliationStatus
from services.reconciliation.runner import run_reconciliation

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


class TriggerRequest(BaseModel):
    mode: ReconciliationMode = ReconciliationMode.RECORD_TO_RECORD


@router.post("/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_reconciliation(
    body: TriggerRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    recon_repo = ReconciliationRepository(session)
    run = await recon_repo.create_run(body.mode)
    background_tasks.add_task(_run_in_background, run.id, body.mode)
    return {"run_id": str(run.id), "mode": body.mode, "status": "accepted"}


@router.get("/runs")
async def list_runs(
    mode: ReconciliationMode | None = Query(default=None),
    run_status: ReconciliationStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    repo = ReconciliationRepository(session)
    runs = await repo.list_runs(mode=mode, status=run_status, limit=limit, offset=offset)
    return {
        "data": [_serialize(r) for r in runs],
        "limit": limit,
        "offset": offset,
    }


@router.get("/runs/{run_id}")
async def get_run(run_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    repo = ReconciliationRepository(session)
    run = await repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return _serialize(run)


async def _run_in_background(run_id: uuid.UUID, mode: ReconciliationMode) -> None:
    from shared.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        await run_reconciliation(session, mode, run_id)


def _serialize(r) -> dict:
    return {
        "id": str(r.id),
        "mode": r.mode,
        "status": r.status,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        "total_processed": r.total_processed,
        "total_mismatches": r.total_mismatches,
        "error_message": r.error_message,
        "created_at": r.created_at.isoformat(),
    }
