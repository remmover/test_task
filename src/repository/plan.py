import pandas as pd
from sqlalchemy import select
from io import BytesIO
from fastapi import HTTPException, status, UploadFile

from src.conf import messages
from src.database.connect import sessionmanager
from src.database.models import Dictionary, Plan


async def download_plan(excel_file: UploadFile) -> str | HTTPException:
    """
    Loads a plan from an Excel file into the database and returns a message about the status of the operation.

    :param excel_file: The Excel file containing the plan to load.
    :type excel_file: UploadFile
    :return: A message about the status of the operation or an HTTPException object in case of an error.
    :rtype: str | HTTPException
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
