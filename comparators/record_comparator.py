from dataclasses import dataclass
from decimal import Decimal

from models.transaction import Transaction
from models.mismatch import MismatchType


@dataclass
class ComparisonResult:
    has_mismatch: bool
    mismatch_type: MismatchType | None
    description: str
    details: dict


class RecordComparator:
    """Compare two transaction records field-by-field."""

    def compare(
        self, txn_a: Transaction, txn_b: Transaction
    ) -> list[ComparisonResult]:
        results: list[ComparisonResult] = []

        results.append(self._compare_amount(txn_a, txn_b))
        results.append(self._compare_status(txn_a, txn_b))
        results.append(self._compare_currency(txn_a, txn_b))

        return [r for r in results if r.has_mismatch]

    def _compare_amount(
        self, txn_a: Transaction, txn_b: Transaction
    ) -> ComparisonResult:
        if txn_a.amount != txn_b.amount:
            return ComparisonResult(
                has_mismatch=True,
                mismatch_type=MismatchType.AMOUNT_MISMATCH,
                description=(
                    f"Amount mismatch for reference {txn_a.reference}: "
                    f"{txn_a.source_system}={txn_a.amount} vs "
                    f"{txn_b.source_system}={txn_b.amount}"
                ),
                details={
                    "system_a": txn_a.source_system,
                    "system_b": txn_b.source_system,
                    "amount_a": str(txn_a.amount),
                    "amount_b": str(txn_b.amount),
                    "difference": str(abs(txn_a.amount - txn_b.amount)),
                },
            )
        return ComparisonResult(has_mismatch=False, mismatch_type=None, description="", details={})

    def _compare_status(
        self, txn_a: Transaction, txn_b: Transaction
    ) -> ComparisonResult:
        if txn_a.status.upper() != txn_b.status.upper():
            return ComparisonResult(
                has_mismatch=True,
                mismatch_type=MismatchType.STATUS_MISMATCH,
                description=(
                    f"Status mismatch for reference {txn_a.reference}: "
                    f"{txn_a.source_system}={txn_a.status} vs "
                    f"{txn_b.source_system}={txn_b.status}"
                ),
                details={
                    "system_a": txn_a.source_system,
                    "system_b": txn_b.source_system,
                    "status_a": txn_a.status,
                    "status_b": txn_b.status,
                },
            )
        return ComparisonResult(has_mismatch=False, mismatch_type=None, description="", details={})

    def _compare_currency(
        self, txn_a: Transaction, txn_b: Transaction
    ) -> ComparisonResult:
        if txn_a.currency.upper() != txn_b.currency.upper():
            return ComparisonResult(
                has_mismatch=True,
                mismatch_type=MismatchType.LEDGER_INCONSISTENCY,
                description=(
                    f"Currency mismatch for reference {txn_a.reference}: "
                    f"{txn_a.source_system}={txn_a.currency} vs "
                    f"{txn_b.source_system}={txn_b.currency}"
                ),
                details={
                    "system_a": txn_a.source_system,
                    "system_b": txn_b.source_system,
                    "currency_a": txn_a.currency,
                    "currency_b": txn_b.currency,
                },
            )
        return ComparisonResult(has_mismatch=False, mismatch_type=None, description="", details={})
