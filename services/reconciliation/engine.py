import json
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from models.mismatch import MismatchType
from models.reconciliation_run import ReconciliationMode
from repositories.transaction_repository import TransactionRepository
from repositories.mismatch_repository import MismatchRepository
from repositories.reconciliation_repository import ReconciliationRepository
from comparators.record_comparator import RecordComparator
from comparators.settlement_comparator import SettlementComparator
from comparators.reversal_comparator import ReversalComparator
from detectors.missing_transaction import MissingTransactionDetector
from detectors.duplicate_detector import DuplicateDetector
from shared.logging import get_logger

logger = get_logger(__name__)

SOURCE_SYSTEMS = ["gateway", "switch", "ledger"]


class ReconciliationEngine:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.txn_repo = TransactionRepository(session)
        self.mismatch_repo = MismatchRepository(session)
        self.recon_repo = ReconciliationRepository(session)
        self.record_comparator = RecordComparator()
        self.settlement_comparator = SettlementComparator()
        self.reversal_comparator = ReversalComparator()
        self.missing_detector = MissingTransactionDetector()
        self.duplicate_detector = DuplicateDetector()

    async def run_record_to_record(self, run_id: uuid.UUID) -> tuple[int, int]:
        """Compare gateway vs ledger record by record."""
        await self.recon_repo.start_run(run_id)

        gateway_txns = await self.txn_repo.list_by_source("gateway", limit=5000)
        ledger_txns = await self.txn_repo.list_by_source("ledger", limit=5000)

        processed = 0
        mismatches: list[dict] = []

        # Missing transaction detection
        missing = self.missing_detector.detect(
            gateway_txns, ledger_txns, "gateway", "ledger"
        )
        for m in missing:
            mismatches.append(self._detection_to_dict(m, run_id))

        missing_reverse = self.missing_detector.detect(
            ledger_txns, gateway_txns, "ledger", "gateway"
        )
        for m in missing_reverse:
            mismatches.append(self._detection_to_dict(m, run_id))

        # Record-to-record comparison
        ledger_map = {t.reference: t for t in ledger_txns}
        for txn_a in gateway_txns:
            txn_b = ledger_map.get(txn_a.reference)
            if txn_b:
                results = self.record_comparator.compare(txn_a, txn_b)
                for r in results:
                    mismatches.append({
                        "reconciliation_run_id": run_id,
                        "mismatch_type": r.mismatch_type,
                        "reference": txn_a.reference,
                        "source_system_a": txn_a.source_system,
                        "source_system_b": txn_b.source_system,
                        "transaction_id_a": txn_a.transaction_id,
                        "transaction_id_b": txn_b.transaction_id,
                        "description": r.description,
                        "details": json.dumps(r.details),
                    })
            processed += 1

        # Duplicate detection per source
        for system_txns in [gateway_txns, ledger_txns]:
            dups = self.duplicate_detector.detect(system_txns)
            for d in dups:
                mismatches.append({
                    "reconciliation_run_id": run_id,
                    "mismatch_type": d.mismatch_type,
                    "reference": d.reference,
                    "source_system_a": d.source_system,
                    "transaction_id_a": d.transaction_ids[0] if d.transaction_ids else None,
                    "description": d.description,
                    "details": json.dumps(d.details),
                })

        if mismatches:
            await self.mismatch_repo.bulk_create(mismatches)

        await self.recon_repo.complete_run(run_id, processed, len(mismatches))
        logger.info(
            "reconciliation_completed",
            run_id=str(run_id),
            mode="record_to_record",
            processed=processed,
            mismatches=len(mismatches),
        )
        return processed, len(mismatches)

    async def run_settlement_reconciliation(self, run_id: uuid.UUID) -> tuple[int, int]:
        """Detect settlement delays."""
        await self.recon_repo.start_run(run_id)

        all_txns = await self.txn_repo.list(status="SUCCESS", limit=5000)
        mismatches: list[dict] = []

        for txn in all_txns:
            result = self.settlement_comparator.check_settlement_delay(txn)
            if result.has_mismatch:
                mismatches.append({
                    "reconciliation_run_id": run_id,
                    "mismatch_type": result.mismatch_type,
                    "reference": txn.reference,
                    "source_system_a": txn.source_system,
                    "transaction_id_a": txn.transaction_id,
                    "description": result.description,
                    "details": json.dumps(result.details),
                })

        if mismatches:
            await self.mismatch_repo.bulk_create(mismatches)

        await self.recon_repo.complete_run(run_id, len(all_txns), len(mismatches))
        return len(all_txns), len(mismatches)

    async def run_reversal_reconciliation(self, run_id: uuid.UUID) -> tuple[int, int]:
        """Validate reversals."""
        await self.recon_repo.start_run(run_id)

        reversals = await self.txn_repo.list(
            status="REVERSAL", limit=5000
        )
        mismatches: list[dict] = []

        for reversal in reversals:
            original = None
            if reversal.reversal_reference:
                matches = await self.txn_repo.get_by_reference(
                    reversal.reversal_reference
                )
                original = matches[0] if matches else None

            result = self.reversal_comparator.check_delayed_reversal(reversal, original)
            if result.has_mismatch:
                mismatches.append({
                    "reconciliation_run_id": run_id,
                    "mismatch_type": result.mismatch_type,
                    "reference": reversal.reference,
                    "source_system_a": reversal.source_system,
                    "transaction_id_a": reversal.transaction_id,
                    "transaction_id_b": original.transaction_id if original else None,
                    "description": result.description,
                    "details": json.dumps(result.details),
                })

        if mismatches:
            await self.mismatch_repo.bulk_create(mismatches)

        await self.recon_repo.complete_run(run_id, len(reversals), len(mismatches))
        return len(reversals), len(mismatches)

    def _detection_to_dict(self, detection, run_id: uuid.UUID) -> dict:
        return {
            "reconciliation_run_id": run_id,
            "mismatch_type": detection.mismatch_type,
            "reference": detection.reference,
            "source_system_a": detection.source_system_a,
            "source_system_b": detection.source_system_b,
            "transaction_id_a": detection.transaction_id_a,
            "transaction_id_b": detection.transaction_id_b,
            "description": detection.description,
            "details": json.dumps(detection.details),
        }
