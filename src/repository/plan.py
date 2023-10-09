import pandas as pd
from fastapi import File, HTTPException, status
from sqlalchemy import select

from src.conf import messages
from src.database.connect import sessionmanager
from src.database.models import Plan


async def download_plan(excel_file: File) -> str | HTTPException:
    """
    Downloads and processes a plan from an Excel file.

    :param excel_file: The Excel file containing plan data.
    :type excel_file: File
    :return: A success message or an HTTPException if there's an error.
    :rtype: str | HTTPException
    """
    try:
        df = pd.read_excel(excel_file)

        df["category"].replace({"збір": "4", "видача": "3"}, inplace=True)
        df["plane_date"] = pd.to_datetime(df["plane_date"], format="%Y-%m-%d").dt.date

        if df["sum"].isnull().any():
            return messages.AMOUNT_NONE

        if not df["plane_date"].astype(str).str.match(r"\d{4}-\d{2}-01").all():
            return messages.DATE_FORMAT_INVALID

        async with sessionmanager.session() as session:
            try:
                session.begin()

                for index, row in df.iterrows():
                    plan_exists = await session.execute(
                        select(Plan).filter(
                            Plan.period == row["plane_date"],
                            Plan.category_id == row["category"],
                        )
                    )

                    if plan_exists.scalar():
                        return messages.PLAN_ALREADY_EXISTS

                    new_plan = Plan(
                        period=row["plane_date"],
                        category_id=row["category"],
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
    except Exception as e:
        return "Error"
