import uuid
from datetime import datetime

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.reconciliation_run import ReconciliationRun, ReconciliationStatus, ReconciliationMode


class ReconciliationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_run(self, mode: ReconciliationMode) -> ReconciliationRun:
        run = ReconciliationRun(mode=mode)
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def start_run(self, run_id: uuid.UUID) -> None:
        await self.session.execute(
            update(ReconciliationRun)
            .where(ReconciliationRun.id == run_id)
            .values(
                status=ReconciliationStatus.RUNNING.value,
                started_at=func.now(),
            )
        )
        await self.session.commit()

    async def complete_run(
        self,
        run_id: uuid.UUID,
        total_processed: int,
        total_mismatches: int,
    ) -> None:
        await self.session.execute(
            update(ReconciliationRun)
            .where(ReconciliationRun.id == run_id)
            .values(
                status=ReconciliationStatus.COMPLETED.value,
                completed_at=func.now(),
                total_processed=total_processed,
                total_mismatches=total_mismatches,
            )
        )
        await self.session.commit()

    async def fail_run(self, run_id: uuid.UUID, error_message: str) -> None:
        await self.session.execute(
            update(ReconciliationRun)
            .where(ReconciliationRun.id == run_id)
            .values(
                status=ReconciliationStatus.FAILED.value,
                completed_at=func.now(),
                error_message=error_message,
            )
        )
        await self.session.commit()

    async def get_by_id(self, run_id: uuid.UUID) -> ReconciliationRun | None:
        result = await self.session.execute(
            select(ReconciliationRun).where(ReconciliationRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def list_runs(
        self,
        mode: ReconciliationMode | None = None,
        status: ReconciliationStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReconciliationRun]:
        q = select(ReconciliationRun)
        if mode:
            q = q.where(ReconciliationRun.mode == mode.value)
        if status:
            q = q.where(ReconciliationRun.status == status.value)
        q = q.order_by(ReconciliationRun.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(q)
        return list(result.scalars().all())
