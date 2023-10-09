from pydantic import BaseModel, ConfigDict
from datetime import date


class BaseUserResponseSchema(BaseModel):
    issuance_date: int
    credit_closed: bool
    return_date: date
    interest_amount: int


class NotDebtorResponseSchema(BaseUserResponseSchema):
    credit_amount: int
    total_payments: int
    model_config = ConfigDict(from_attributes=True)


class DebtorResponseSchema(BaseUserResponseSchema):
    days_overdue: int
    credit_amount: int
    total_body_payments: float
    total_percent_payments: float
    model_config = ConfigDict(from_attributes=True)


class FileResponseSchema(BaseModel):
    text: str
