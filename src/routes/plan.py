from datetime import date

from fastapi import APIRouter, UploadFile, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from src.conf import messages
from src.database.connect import get_db
from src.repository.plan import (
    download_plan,
    get_plan_performance,
    summary_information_year,
)
from src.schemas import (
    FileResponseSchema,
    PlanPerformanceResponse,
)

router = APIRouter(tags=["plans"])


@router.post("/upload_plan", response_model=FileResponseSchema)
async def create_upload_plan(
    file: UploadFile,
):
    """
    :var   The file content must have the following fields
    :var   plane_date category sum
    :var   01.01.2000 issue     0
    :param file: The uploaded file (an Excel spreadsheet).
    :type file: UploadFile
    :return: A response containing the result of the download process.
    :rtype: dict
    :raises HTTPException: If the uploaded file size exceeds the maximum allowed size or type file isn`t xslx.
    """

    MAX_FILE_SIZE = 1024 * 1024  # 1 MB

    if not file.content_type.startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ):
        raise HTTPException(
            status_code=400,
            detail=messages.WRONG_FILE_TYPE,
        )

    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=messages.FILE_SIZE_OVER,
        )

    result = await download_plan(file)

    response_data = {"result": result}
    return JSONResponse(content=response_data)


@router.get("/plans_performance", response_model=PlanPerformanceResponse)
async def fulfilment_plans(date: date, db: AsyncSession = Depends(get_db)):
    """Gets the percentage of plan execution for loans and payments for the specified month.

    :param date: Date for which you want to get the percentage of plan execution.
    :type date: datetime.date
    :param db: Database session.
    :type db: AsyncSession
    :return: Results of plan execution for payments and credits. :rtype: PlanPerformanceResponse
    """
    result_payments, result_credits = await get_plan_performance(date, db)
    return PlanPerformanceResponse(
        result_payments=result_payments, result_credits=result_credits
    )


@router.get("/year_performance")
async def fulfilment_years_plans(year: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves summary information for a specific year, including payment and credit data.

    :param year: The year for which summary information is requested.
    :type year: int
    :param db: The database session (AsyncSession) used for executing queries.
    :type db: AsyncSession
    :return: A list of summary information for each month within the specified year.
    :rtype: List[Dict[str, Any]]

    This endpoint returns summary information for a specific year, including payment and credit data. It makes use of
    the `summary_information_year` function to retrieve and process the data.

    Example usage:

    Request URL: /year_performance?year=2023
    Method: GET

    Response JSON structure:
    [
        {
            "YearMonth": "2023-01",
            "PaymentCount": 10,
            "PaymentSum": 5000.00,
            "PaymentPlanSum": 5500.00,
            "CreditCount": 5,
            "CreditSum": 3000.00,
            "CreditPlanSum": 4000.00,
            "CreditPlanCompletionPercentage": 75.0,
            "PaymentPlanCompletionPercentage": 90.91,
            "PercentageOfYearlyCredit": 60.0,
            "PercentageOfYearlyPayment": 55.56
        },
        ...
    ]

    Note: You should provide a valid `year` parameter to specify the year for which you want to retrieve summary data.
    The `db` parameter represents the database session used for executing the query.

    """
    result = await summary_information_year(year, db)
    return {"result": result}
