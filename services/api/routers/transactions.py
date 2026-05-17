from datetime import datetime
from decimal import Decimal
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from repositories.transaction_repository import TransactionRepository

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("")
async def list_transactions(
    source_system: str | None = Query(default=None),
    status: str | None = Query(default=None),
    from_dt: datetime | None = Query(default=None),
    to_dt: datetime | None = Query(default=None),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    repo = TransactionRepository(session)
    transactions = await repo.list(
        source_system=source_system,
        status=status,
        from_dt=from_dt,
        to_dt=to_dt,
        limit=limit,
        offset=offset,
    )
    return {
        "data": [_serialize(t) for t in transactions],
        "limit": limit,
        "offset": offset,
    }


@router.get("/summary")
async def transaction_summary(session: AsyncSession = Depends(get_db)):
    repo = TransactionRepository(session)
    total = await repo.total_count()
    return {"total_transactions": total}


@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: uuid.UUID, session: AsyncSession = Depends(get_db)
):
    repo = TransactionRepository(session)
    txn = await repo.get_by_id(transaction_id)
    if not txn:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return _serialize(txn)


def _serialize(t) -> dict:
    return {
        "id": str(t.id),
        "transaction_id": t.transaction_id,
        "reference": t.reference,
        "amount": str(t.amount),
        "currency": t.currency,
        "status": t.status,
        "source_system": t.source_system,
        "timestamp": t.timestamp.isoformat(),
        "created_at": t.created_at.isoformat(),
    }
