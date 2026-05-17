from dataclasses import dataclass
from collections import defaultdict
from datetime import timedelta

from models.transaction import Transaction
from models.mismatch import MismatchType
from config.settings import get_settings

settings = get_settings()


@dataclass
class DuplicateResult:
    has_mismatch: bool
    mismatch_type: MismatchType
    reference: str
    source_system: str
    transaction_ids: list[str]
    description: str
    details: dict


class DuplicateDetector:
    """Detect the same reference processed multiple times in the same source."""

    def detect(self, transactions: list[Transaction]) -> list[DuplicateResult]:
        by_ref: dict[str, list[Transaction]] = defaultdict(list)

        for txn in transactions:
            by_ref[txn.reference].append(txn)

        results: list[DuplicateResult] = []
        for ref, txns in by_ref.items():
            # Group within duplicate window
            duplicates = self._find_duplicates_in_window(txns)
            if duplicates:
                ids = [t.transaction_id for t in duplicates]
                results.append(
                    DuplicateResult(
                        has_mismatch=True,
                        mismatch_type=MismatchType.DUPLICATE_TRANSACTION,
                        reference=ref,
                        source_system=duplicates[0].source_system,
                        transaction_ids=ids,
                        description=(
                            f"Duplicate processing detected for reference {ref}: "
                            f"{len(duplicates)} occurrences in {duplicates[0].source_system}"
                        ),
                        details={
                            "reference": ref,
                            "count": len(duplicates),
                            "transaction_ids": ids,
                            "source_system": duplicates[0].source_system,
                        },
                    )
                )

        return results

    def _find_duplicates_in_window(
        self, transactions: list[Transaction]
    ) -> list[Transaction]:
        if len(transactions) < 2:
            return []

        window = timedelta(seconds=settings.recon_duplicate_window_seconds)
        sorted_txns = sorted(transactions, key=lambda t: t.timestamp)
        first = sorted_txns[0]
        in_window = [
            t
            for t in sorted_txns
            if abs((t.timestamp - first.timestamp).total_seconds())
            <= window.total_seconds()
        ]
        return in_window if len(in_window) > 1 else []
