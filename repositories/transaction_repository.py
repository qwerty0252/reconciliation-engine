import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.transaction import Transaction


class TransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: dict) -> Transaction:
        txn = Transaction(**data)
        self.session.add(txn)
        await self.session.commit()
        await self.session.refresh(txn)
        return txn

    async def get_by_id(self, transaction_id: uuid.UUID) -> Transaction | None:
        result = await self.session.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def get_by_transaction_id_and_source(
        self, transaction_id: str, source_system: str
    ) -> Transaction | None:
        result = await self.session.execute(
            select(Transaction).where(
                and_(
                    Transaction.transaction_id == transaction_id,
                    Transaction.source_system == source_system,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_reference(self, reference: str) -> list[Transaction]:
        result = await self.session.execute(
            select(Transaction).where(Transaction.reference == reference)
        )
        return list(result.scalars().all())

    async def list_by_source(
        self,
        source_system: str,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        q = select(Transaction).where(Transaction.source_system == source_system)
        if status:
            q = q.where(Transaction.status == status)
        q = q.order_by(Transaction.timestamp.desc()).limit(limit).offset(offset)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def list(
        self,
        source_system: str | None = None,
        status: str | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        q = select(Transaction)
        if source_system:
            q = q.where(Transaction.source_system == source_system)
        if status:
            q = q.where(Transaction.status == status)
        if from_dt:
            q = q.where(Transaction.timestamp >= from_dt)
        if to_dt:
            q = q.where(Transaction.timestamp <= to_dt)
        q = q.order_by(Transaction.timestamp.desc()).limit(limit).offset(offset)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def count_by_source(self, source_system: str) -> int:
        result = await self.session.execute(
            select(func.count()).where(Transaction.source_system == source_system)
        )
        return result.scalar_one()

    async def total_count(self) -> int:
        result = await self.session.execute(select(func.count(Transaction.id)))
        return result.scalar_one()
