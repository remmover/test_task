from fastapi import APIRouter, UploadFile, HTTPException
from starlette.responses import JSONResponse

from src.conf import messages
from src.repository.plan import download_plan
from src.schemas import FileResponseSchema

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

    response_data = {"text": result}
    return JSONResponse(content=response_data)
