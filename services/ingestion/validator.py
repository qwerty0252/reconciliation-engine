import json
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TransactionEventSchema(BaseModel):
    transaction_id: str = Field(..., min_length=1, max_length=100)
    reference: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    status: str = Field(..., min_length=1, max_length=50)
    source_system: str = Field(..., min_length=1, max_length=100)
    timestamp: datetime
    transaction_type: str | None = Field(default=None, max_length=50)
    reversal_reference: str | None = Field(default=None, max_length=200)
    settlement_id: str | None = Field(default=None, max_length=200)

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, v: str) -> str:
        return v.upper()

    @field_validator("status")
    @classmethod
    def status_uppercase(cls, v: str) -> str:
        return v.upper()

    @field_validator("source_system")
    @classmethod
    def source_system_lowercase(cls, v: str) -> str:
        return v.lower()
