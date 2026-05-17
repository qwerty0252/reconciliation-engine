import json
from decimal import Decimal

from services.ingestion.validator import TransactionEventSchema


def normalize(event: TransactionEventSchema) -> dict:
    """Produce a dict ready for Transaction model insertion."""
    return {
        "transaction_id": event.transaction_id,
        "reference": event.reference,
        "amount": Decimal(str(event.amount)),
        "currency": event.currency,
        "status": event.status,
        "source_system": event.source_system,
        "timestamp": event.timestamp,
        "transaction_type": event.transaction_type,
        "reversal_reference": event.reversal_reference,
        "settlement_id": event.settlement_id,
        "raw_payload": event.model_dump_json(),
    }
