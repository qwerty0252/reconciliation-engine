import pytest
import pytest_asyncio
from decimal import Decimal
from datetime import datetime, timezone

from comparators.record_comparator import RecordComparator
from comparators.settlement_comparator import SettlementComparator
from comparators.reversal_comparator import ReversalComparator
from detectors.missing_transaction import MissingTransactionDetector
from detectors.duplicate_detector import DuplicateDetector
from models.mismatch import MismatchType


def make_txn(**kwargs):
    """Factory for minimal Transaction-like objects."""
    from types import SimpleNamespace
    defaults = dict(
        id="test-id",
        transaction_id="TXN_001",
        reference="REF123",
        amount=Decimal("5000.00"),
        currency="NGN",
        status="SUCCESS",
        source_system="gateway",
        timestamp=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
        reversal_reference=None,
        settlement_id=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestRecordComparator:
    def test_no_mismatch_identical(self):
        comparator = RecordComparator()
        a = make_txn()
        b = make_txn(source_system="ledger")
        assert comparator.compare(a, b) == []

    def test_amount_mismatch(self):
        comparator = RecordComparator()
        a = make_txn(amount=Decimal("5000.00"))
        b = make_txn(source_system="ledger", amount=Decimal("4000.00"))
        results = comparator.compare(a, b)
        assert len(results) == 1
        assert results[0].mismatch_type == MismatchType.AMOUNT_MISMATCH

    def test_status_mismatch(self):
        comparator = RecordComparator()
        a = make_txn(status="SUCCESS")
        b = make_txn(source_system="ledger", status="FAILED")
        results = comparator.compare(a, b)
        assert any(r.mismatch_type == MismatchType.STATUS_MISMATCH for r in results)

    def test_currency_mismatch(self):
        comparator = RecordComparator()
        a = make_txn(currency="NGN")
        b = make_txn(source_system="ledger", currency="USD")
        results = comparator.compare(a, b)
        assert any(r.mismatch_type == MismatchType.LEDGER_INCONSISTENCY for r in results)


class TestMissingTransactionDetector:
    def test_detects_missing(self):
        detector = MissingTransactionDetector()
        a = [make_txn(transaction_id="T1", reference="REF1")]
        b = [make_txn(transaction_id="T2", reference="REF2", source_system="ledger")]
        results = detector.detect(a, b, "gateway", "ledger")
        assert len(results) == 1
        assert results[0].mismatch_type == MismatchType.MISSING_TRANSACTION

    def test_no_missing_when_all_present(self):
        detector = MissingTransactionDetector()
        txn = make_txn(reference="REF1")
        results = detector.detect([txn], [make_txn(reference="REF1", source_system="ledger")], "gateway", "ledger")
        assert results == []


class TestDuplicateDetector:
    def test_detects_duplicate(self):
        detector = DuplicateDetector()
        txns = [
            make_txn(transaction_id="T1", reference="REF1"),
            make_txn(transaction_id="T2", reference="REF1"),
        ]
        results = detector.detect(txns)
        assert len(results) == 1
        assert results[0].mismatch_type == MismatchType.DUPLICATE_TRANSACTION

    def test_no_duplicate_for_unique_refs(self):
        detector = DuplicateDetector()
        txns = [
            make_txn(transaction_id="T1", reference="REF1"),
            make_txn(transaction_id="T2", reference="REF2"),
        ]
        assert detector.detect(txns) == []


class TestReversalComparator:
    def test_orphan_reversal(self):
        comparator = ReversalComparator()
        reversal = make_txn(
            transaction_id="REV_001",
            status="REVERSAL",
            reversal_reference="TXN_ORIG",
        )
        result = comparator.check_delayed_reversal(reversal, original=None)
        assert result.has_mismatch
        assert result.mismatch_type == MismatchType.ORPHAN_REVERSAL
