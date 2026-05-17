from dataclasses import dataclass
from collections import defaultdict

from models.transaction import Transaction
from models.mismatch import MismatchType


@dataclass
class DetectionResult:
    has_mismatch: bool
    mismatch_type: MismatchType
    reference: str
    source_system_a: str
    source_system_b: str
    transaction_id_a: str | None
    transaction_id_b: str | None
    description: str
    details: dict


class MissingTransactionDetector:
    """Detect transactions present in one system but absent in another."""

    def detect(
        self,
        transactions_a: list[Transaction],
        transactions_b: list[Transaction],
        system_a: str,
        system_b: str,
    ) -> list[DetectionResult]:
        refs_b = {t.reference for t in transactions_b}
        id_map_a = {t.reference: t for t in transactions_a}
        results: list[DetectionResult] = []

        for ref, txn in id_map_a.items():
            if ref not in refs_b:
                results.append(
                    DetectionResult(
                        has_mismatch=True,
                        mismatch_type=MismatchType.MISSING_TRANSACTION,
                        reference=ref,
                        source_system_a=system_a,
                        source_system_b=system_b,
                        transaction_id_a=txn.transaction_id,
                        transaction_id_b=None,
                        description=(
                            f"Transaction {txn.transaction_id} exists in {system_a} "
                            f"but is missing in {system_b}"
                        ),
                        details={
                            "reference": ref,
                            "found_in": system_a,
                            "missing_in": system_b,
                        },
                    )
                )

        return results
