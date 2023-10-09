from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


from src.database.models import User, Credit, Payment


async def get_customer_by_id(id: int, db: AsyncSession) -> List[dict[str]]:
    sq = (
        select(
            Credit.issuance_date,
            Credit.credit,
            Credit.return_date,
            Credit.body,
            Credit.percent,
            func.datediff(func.now(), Credit.return_date).label("days_overdue"),
            func.sum(func.if_(Payment.type_id == 1, Payment.sum, 0)).label(
                "total_body_payments"
            ),
            func.sum(func.if_(Payment.type_id == 2, Payment.sum, 0)).label(
                "total_percent_payments"
            ),
        )
        .where(
            User.id == id,
            Credit.user_id == User.id,
            Credit.id == Payment.credit_id,
        )
        .group_by(
            Credit.issuance_date,
            Credit.credit,
            Credit.return_date,
            Credit.body,
            Credit.percent,
        )
    )

    result = await db.execute(sq)
    user_credits = result.mappings().all()

    credit_info_list = []

    for credit in user_credits:
        credit_info = {
            "issuance_date": credit["issuance_date"],
            "credit_closed": credit["credit"],
        }

        if credit["credit"]:
            credit_info.update(
                {
                    "return_date": credit["return_date"],
                    "credit_amount": credit["body"],
                    "interest_amount": credit["percent"],
                    "total_payments": credit["total_body_payments"]
                    + credit["total_percent_payments"],
                }
            )
        else:
            credit_info.update(
                {
                    "return_date": credit["return_date"],
                    "days_overdue": credit["days_overdue"],
                    "credit_amount": credit["body"],
                    "interest_amount": credit["percent"],
                    "total_body_payments": credit["total_body_payments"],
                    "total_percent_payments": credit["total_percent_payments"],
                }
            )

        credit_info_list.append(credit_info)

    return credit_info_list
