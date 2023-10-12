from datetime import date
from typing import Tuple, Dict, Union, List, Any

import pandas as pd
from sqlalchemy import select, func, and_, extract
from io import BytesIO
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf import messages
from src.database.connect import sessionmanager
from src.database.models import Dictionary, Plan, Payment, Credit


async def download_plan(excel_file: UploadFile) -> Union[str, HTTPException]:
    """
    Loads a plan from an Excel file into the database and returns a message about the status of the operation.

    :param excel_file: The Excel file containing the plan to load.
    :type excel_file: UploadFile
    :param session: The database session.
    :type session: AsyncSession
    :return: A message about the status of the operation or an HTTPException object in case of an error.
    :rtype: Union[str, HTTPException]
    """
    df = pd.read_excel(BytesIO(await excel_file.read()))

    ALLOWED_ID_CATEGORIES = [3, 4]

    if df["sum"].isnull().any():
        return messages.AMOUNT_NONE

    if not df["plane_date"].astype(str).str.match(r"\d{4}-\d{2}-01").all():
        return messages.DATE_FORMAT_INVALID

    async with sessionmanager.session() as session:
        try:
            session.begin()

            category_ids = {}
            categories = await session.execute(
                select(Dictionary.id, Dictionary.name).filter(
                    Dictionary.name.in_(df["category"])
                )
            )

            for category_id, category_name in categories:
                category_ids[category_name] = category_id

            for index, row in df.iterrows():
                category_id = category_ids.get(row["category"])

                if category_id not in ALLOWED_ID_CATEGORIES:
                    return messages.CATEGORY_NOT_FOUND

                plan_exists = await session.execute(
                    select(Plan).filter(
                        Plan.period == row["plane_date"],
                        Plan.category_id == category_id,
                    )
                )

                if plan_exists.scalar():
                    return messages.PLAN_ALREADY_EXISTS

                new_plan = Plan(
                    period=row["plane_date"],
                    category_id=category_id,
                    sum=row["sum"],
                )

                session.add(new_plan)

            await session.commit()
            return messages.PLAN_CREATE_SUCCESSFULLY

        except:
            await session.rollback()
            return HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=messages.ERROR_UPLOADING_PLAN,
            )


async def get_plan_performance(
    date: date, db: AsyncSession
) -> Tuple[Dict[str, Union[str, float]], Dict[str, Union[str, float]]]:
    """Gets the percentage of plan execution for loans and payments for the specified month.

    :param date: Date for which you want to get the percentage of plan execution.
    :type date: datetime.date
    :param db: Database session.
    :type db: Session
    :return: Results of the plan execution for payments and credits.
    :rtype: Tuple[Dict[str, Union[str, float]], Dict[str, Union[str, float]]]
    """
    total_body_credit = await db.execute(
        select(func.sum(Credit.body)).where(
            and_(
                Credit.issuance_date >= date.replace(day=1),
                Credit.issuance_date <= date,
            )
        )
    )

    total_body_payment = await db.execute(
        select(func.sum(Payment.sum)).where(
            and_(
                Payment.payment_date >= date.replace(day=1),
                Payment.payment_date <= date,
            )
        )
    )

    credit_plan_sum = await db.execute(
        select(func.sum(Plan.sum)).where(
            and_(
                Plan.category_id == 3,
                Plan.period >= date.replace(day=1),
                Plan.period <= date,
            )
        )
    )

    payment_plan_sum = await db.execute(
        select(func.sum(Plan.sum)).where(
            and_(
                Plan.category_id == 4,
                Plan.period >= date.replace(day=1),
                Plan.period <= date,
            )
        )
    )

    total_body_payment = float(total_body_payment.scalar() or 0.0)
    total_body_credit = float(total_body_credit.scalar() or 0.0)
    credit_plan_sum = float(credit_plan_sum.scalar() or 0.0)
    payment_plan_sum = float(payment_plan_sum.scalar() or 0.0)

    percent_completion_credit, percent_completion_payment = (
        ((total_body_credit / credit_plan_sum) * 100 if credit_plan_sum > 0 else 0),
        ((total_body_payment / payment_plan_sum) * 100 if payment_plan_sum > 0 else 0),
    )

    result_credits, result_payments = {
        "month": date.strftime("%B %Y"),
        "category": "видача",
        "sum_plan": credit_plan_sum,
        "total_sum": total_body_credit,
        "percent_completion": percent_completion_credit,
    }, {
        "month": date.strftime("%B %Y"),
        "category": "збір",
        "sum_plan": payment_plan_sum,
        "total_sum": total_body_payment,
        "percent_completion": percent_completion_payment,
    }
    return result_payments, result_credits


async def summary_information_year(year: int, db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Retrieves summary information for a specific year, including payment and credit data.

    :param year: The year for which summary information is requested.
    :type year: int
    :param db: The database session (AsyncSession) used for executing queries.
    :type db: AsyncSession
    :return: A list of summary information for each month within the specified year.
    :rtype: List[Dict[str, Any]]

    This function retrieves and combines payment and credit data for a specific year. It calculates various metrics,
    such as completion percentages and percentages of yearly credit and payment sums for each month.

    Example usage:

    year = 2023
    db = create_async_session()  # Replace with your database session creation logic.
    result = await summary_information_year(year, db)

    The returned list of dictionaries contains summary information for each month, including the following keys:
    - 'YearMonth': The month in the format 'YYYY-MM'.
    - 'PaymentCount': The count of payments for the month.
    - 'PaymentSum': The sum of payments for the month.
    - 'PaymentPlanSum': The sum of payment plans for the month.
    - 'CreditCount': The count of credits for the month.
    - 'CreditSum': The sum of credits for the month.
    - 'CreditPlanSum': The sum of credit plans for the month.
    - 'CreditPlanCompletionPercentage': The completion percentage of credit plans for the month.
    - 'PaymentPlanCompletionPercentage': The completion percentage of payment plans for the month.
    - 'PercentageOfYearlyCredit': The percentage of the monthly credit sum relative to the yearly credit total.
    - 'PercentageOfYearlyPayment': The percentage of the monthly payment sum relative to the yearly payment total.

    Note: You should have a valid database connection (db) to use this function.

    """

    async def execute_query(query) -> List[Dict[str, Any]]:
        result = await db.execute(query)
        return result.mappings().all()

    payment_query = (
        select(
            func.date_format(Payment.payment_date, "%Y-%m").label("YearMonth"),
            func.count(Payment.id).label("PaymentCount"),
            func.sum(Payment.sum).label("PaymentSum"),
        )
        .filter(
            Payment.payment_date.isnot(None),
            extract("year", Payment.payment_date) == year,
        )
        .group_by("YearMonth")
        .order_by("YearMonth")
    )

    payment_plan_query = (
        select(
            func.date_format(Plan.period, "%Y-%m").label("YearMonth"),
            func.sum(Plan.sum).label("PaymentPlanSum"),
        )
        .filter(Plan.category_id == 4, extract("year", Plan.period) == year)
        .group_by("YearMonth")
        .order_by("YearMonth")
    )

    credit_query = (
        select(
            func.date_format(Credit.issuance_date, "%Y-%m").label("YearMonth"),
            func.count(Credit.id).label("CreditCount"),
            func.sum(Credit.body).label("CreditSum"),
        )
        .filter(
            Credit.issuance_date.isnot(None),
            extract("year", Credit.issuance_date) == year,
        )
        .group_by("YearMonth")
        .order_by("YearMonth")
    )

    credit_plan_query = (
        select(
            func.date_format(Plan.period, "%Y-%m").label("YearMonth"),
            func.sum(Plan.sum).label("CreditPlanSum"),
        )
        .filter(Plan.category_id == 3, extract("year", Plan.period) == year)
        .group_by("YearMonth")
        .order_by("YearMonth")
    )

    (
        payment_query_result,
        payment_plan_query_result,
        credit_query_result,
        credit_plan_query_result,
    ) = (
        await execute_query(payment_query),
        await execute_query(payment_plan_query),
        await execute_query(credit_query),
        await execute_query(credit_plan_query),
    )

    all_results = (
        payment_query_result
        + payment_plan_query_result
        + credit_query_result
        + credit_plan_query_result
    )

    combined_payment = []
    for year_month in set(result["YearMonth"] for result in all_results):
        payment = next(
            (item for item in payment_query_result if item["YearMonth"] == year_month),
            {"PaymentCount": 0, "PaymentSum": 0},
        )
        payment_plan = next(
            (
                item
                for item in payment_plan_query_result
                if item["YearMonth"] == year_month
            ),
            {"PaymentPlanSum": 0},
        )
        credit = next(
            (item for item in credit_query_result if item["YearMonth"] == year_month),
            {"CreditCount": 0, "CreditSum": 0},
        )
        credit_plan = next(
            (
                item
                for item in credit_plan_query_result
                if item["YearMonth"] == year_month
            ),
            {"CreditPlanSum": 0},
        )

        combined_payment.append(
            {
                "YearMonth": year_month,
                **credit,
                **credit_plan,
                **payment,
                **payment_plan,
                "CreditPlanCompletionPercentage": (
                    float(credit.get("CreditSum", 0))
                    / float(credit_plan.get("CreditPlanSum", 0))
                )
                * 100
                if credit_plan.get("CreditPlanSum", 0)
                else 0,
                "PaymentPlanCompletionPercentage": (
                    payment.get("PaymentSum", 0)
                    / float(payment_plan.get("PaymentPlanSum", 0))
                )
                * 100
                if payment_plan.get("PaymentPlanSum", 0)
                else 0,
            }
        )
    credit_total_yearly_payment = sum(
        payment["CreditSum"] for payment in combined_payment
    )
    payment_total_yearly_payment = sum(
        payment["PaymentSum"] for payment in combined_payment
    )

    for payment in combined_payment:
        payment.update(
            {
                "PercentageOfYearlyCredit": (
                    payment["CreditSum"] / credit_total_yearly_payment
                )
                * 100,
                "PercentageOfYearlyPayment": (
                    payment["PaymentSum"] / payment_total_yearly_payment
                )
                * 100,
            }
        )
    combined_payment = sorted(combined_payment, key=lambda x: x["YearMonth"])
    return combined_payment
