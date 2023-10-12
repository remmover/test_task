from typing import List, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, Credit, Payment


async def get_customer_by_id(id: int, db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Retrieves information about a customer's credits by their user ID.

    :param id: The ID of the customer for whom to retrieve credit information.
    :type id: int
    :param db: The database session.
    :type db: AsyncSession
    :return: A list of dictionaries containing credit information.
    :rtype: List[dict[str]]
    """
    sq = (
        select(
            Credit.issuance_date,
            Credit.actual_return_date,
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
            Credit.actual_return_date,
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
            "issuance_date": credit["issuance_date"].strftime("%Y-%m-%d"),
            "credit_closed": True if credit["actual_return_date"] else False,
        }

        if credit_info["credit_closed"]:
            credit_info.update(
                {
                    "return_date": credit["return_date"].strftime("%Y-%m-%d"),
                    "credit_amount": credit["body"],
                    "interest_amount": credit["percent"],
                    "total_payments": credit["total_body_payments"]
                    + credit["total_percent_payments"],
                }
            )
        else:
            credit_info.update(
                {
                    "return_date": credit["return_date"].strftime("%Y-%m-%d"),
                    "days_overdue": credit["days_overdue"],
                    "credit_amount": credit["body"],
                    "interest_amount": credit["percent"],
                    "total_body_payments": credit["total_body_payments"],
                    "total_percent_payments": credit["total_percent_payments"],
                }
            )

        credit_info_list.append(credit_info)

    return credit_info_list
