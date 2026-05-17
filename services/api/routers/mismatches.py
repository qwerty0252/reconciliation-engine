import uuid

from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from repositories.mismatch_repository import MismatchRepository
from models.mismatch import MismatchType, MismatchStatus

router = APIRouter(prefix="/mismatches", tags=["Mismatches"])


class ResolveRequest(BaseModel):
    resolution_notes: str


@router.get("")
async def list_mismatches(
    mismatch_type: MismatchType | None = Query(default=None),
    status: MismatchStatus | None = Query(default=None),
    run_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    repo = MismatchRepository(session)
    mismatches = await repo.list(
        mismatch_type=mismatch_type,
        status=status,
        run_id=run_id,
        limit=limit,
        offset=offset,
    )
    return {
        "data": [_serialize(m) for m in mismatches],
        "limit": limit,
        "offset": offset,
    }


@router.get("/summary")
async def mismatch_summary(session: AsyncSession = Depends(get_db)):
    repo = MismatchRepository(session)
    open_count = await repo.count_open()
    by_type = await repo.count_by_type()
    return {"open_count": open_count, "by_type": by_type}


@router.get("/{mismatch_id}")
async def get_mismatch(mismatch_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    repo = MismatchRepository(session)
    m = await repo.get_by_id(mismatch_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mismatch not found")
    return _serialize(m)


@router.post("/{mismatch_id}/resolve")
async def resolve_mismatch(
    mismatch_id: uuid.UUID,
    body: ResolveRequest,
    session: AsyncSession = Depends(get_db),
):
    repo = MismatchRepository(session)
    m = await repo.resolve(mismatch_id, body.resolution_notes)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mismatch not found")
    return _serialize(m)


def _serialize(m) -> dict:
    return {
        "id": str(m.id),
        "mismatch_type": m.mismatch_type,
        "status": m.status,
        "reference": m.reference,
        "source_system_a": m.source_system_a,
        "source_system_b": m.source_system_b,
        "transaction_id_a": m.transaction_id_a,
        "transaction_id_b": m.transaction_id_b,
        "description": m.description,
        "details": m.details,
        "resolution_notes": m.resolution_notes,
        "alert_sent": m.alert_sent,
        "created_at": m.created_at.isoformat(),
        "updated_at": m.updated_at.isoformat(),
    }
