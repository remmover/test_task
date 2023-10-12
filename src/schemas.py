from pydantic import BaseModel
from typing import List


class CreditInfo(BaseModel):
    issuance_date: str = ""
    credit_closed: bool = False
    return_date: str = ""
    days_overdue: int = 0
    credit_amount: float = 0.0
    interest_amount: float = 0.0
    total_body_payments: float = 0.0
    total_percent_payments: float = 0.0


class CustomerLoansResponse(BaseModel):
    user_credits: List[CreditInfo]


class FileResponseSchema(BaseModel):
    text: str


class PlanPerformance(BaseModel):
    month: str
    category: str
    sum_plan: float
    total_sum: float
    percent_completion: float


class PlanPerformanceResponse(BaseModel):
    result_payments: PlanPerformance
    result_credits: PlanPerformance
