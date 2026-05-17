import pytest
from decimal import Decimal
from datetime import datetime, timezone

from services.ingestion.validator import TransactionEventSchema
from services.ingestion.normalizer import normalize
from pydantic import ValidationError


class TestTransactionEventSchema:
    def test_valid_payload(self):
        event = TransactionEventSchema(
            transaction_id="TXN_001",
            reference="REF123",
            amount=5000.0,
            currency="ngn",
            status="success",
            source_system="Gateway",
            timestamp=datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc),
        )
        assert event.currency == "NGN"
        assert event.status == "SUCCESS"
        assert event.source_system == "gateway"

    def test_rejects_zero_amount(self):
        with pytest.raises(ValidationError):
            TransactionEventSchema(
                transaction_id="TXN_001",
                reference="REF123",
                amount=0,
                currency="NGN",
                status="SUCCESS",
                source_system="gateway",
                timestamp=datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc),
            )

    def test_rejects_negative_amount(self):
        with pytest.raises(ValidationError):
            TransactionEventSchema(
                transaction_id="TXN_001",
                reference="REF123",
                amount=-100,
                currency="NGN",
                status="SUCCESS",
                source_system="gateway",
                timestamp=datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc),
            )

    def test_rejects_invalid_currency_length(self):
        with pytest.raises(ValidationError):
            TransactionEventSchema(
                transaction_id="TXN_001",
                reference="REF123",
                amount=100,
                currency="NGNN",
                status="SUCCESS",
                source_system="gateway",
                timestamp=datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc),
            )


class TestNormalizer:
    def test_normalize_produces_decimal(self):
        event = TransactionEventSchema(
            transaction_id="TXN_001",
            reference="REF123",
            amount=5000.50,
            currency="NGN",
            status="SUCCESS",
            source_system="gateway",
            timestamp=datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc),
        )
        result = normalize(event)
        assert isinstance(result["amount"], Decimal)
        assert result["source_system"] == "gateway"
        assert result["raw_payload"] is not None
