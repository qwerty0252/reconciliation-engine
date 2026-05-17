import uuid
from datetime import datetime

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.mismatch import Mismatch, MismatchStatus, MismatchType


class MismatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: dict) -> Mismatch:
        mismatch = Mismatch(**data)
        self.session.add(mismatch)
        await self.session.commit()
        await self.session.refresh(mismatch)
        return mismatch

    async def bulk_create(self, records: list[dict]) -> list[Mismatch]:
        if not records:
            return []

        # Deduplicate: skip any record where an open mismatch already exists
        # for the same (reference, mismatch_type, source_system_a, source_system_b)
        references = list({r["reference"] for r in records if r.get("reference")})
        existing_result = await self.session.execute(
            select(
                Mismatch.reference,
                Mismatch.mismatch_type,
                Mismatch.source_system_a,
                Mismatch.source_system_b,
            )
            .where(Mismatch.reference.in_(references))
            .where(Mismatch.status == MismatchStatus.OPEN.value)
        )
        existing = {
            (row.reference, row.mismatch_type, row.source_system_a, row.source_system_b)
            for row in existing_result.all()
        }

        new_records = [
            r for r in records
            if (r.get("reference"), r.get("mismatch_type"), r.get("source_system_a"), r.get("source_system_b"))
            not in existing
        ]

        if not new_records:
            return []

        mismatches = [Mismatch(**r) for r in new_records]
        self.session.add_all(mismatches)
        await self.session.commit()
        return mismatches

    async def get_by_id(self, mismatch_id: uuid.UUID) -> Mismatch | None:
        result = await self.session.execute(
            select(Mismatch).where(Mismatch.id == mismatch_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        mismatch_type: MismatchType | None = None,
        status: MismatchStatus | None = None,
        run_id: uuid.UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Mismatch]:
        q = select(Mismatch)
        if mismatch_type:
            q = q.where(Mismatch.mismatch_type == mismatch_type.value)
        if status:
            q = q.where(Mismatch.status == status.value)
        if run_id:
            q = q.where(Mismatch.reconciliation_run_id == run_id)
        q = q.order_by(Mismatch.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def resolve(self, mismatch_id: uuid.UUID, notes: str) -> Mismatch | None:
        await self.session.execute(
            update(Mismatch)
            .where(Mismatch.id == mismatch_id)
            .values(status=MismatchStatus.RESOLVED.value, resolution_notes=notes)
        )
        await self.session.commit()
        return await self.get_by_id(mismatch_id)

    async def count_open(self) -> int:
        result = await self.session.execute(
            select(func.count()).where(Mismatch.status == MismatchStatus.OPEN.value)
        )
        return result.scalar_one()

    async def count_by_type(self) -> dict[str, int]:
        result = await self.session.execute(
            select(Mismatch.mismatch_type, func.count()).group_by(Mismatch.mismatch_type)
        )
        return {row[0]: row[1] for row in result.all()}

    async def mark_alert_sent(self, mismatch_id: uuid.UUID) -> None:
        await self.session.execute(
            update(Mismatch)
            .where(Mismatch.id == mismatch_id)
            .values(alert_sent=True)
        )

        await self.session.commit()
