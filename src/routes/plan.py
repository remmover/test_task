import pathlib


from fastapi import APIRouter, status, UploadFile, HTTPException

from src.conf import messages
from src.repository.plan import download_plan


router = APIRouter(tags=["plans"])
MAX_FILE_SIZE = 1_000_000


@router.post("/upload_plan")
async def create_upload_plan(
    file: UploadFile,
):
    """
    :var   The file content must have the following fields
    :var   plane_date category sum
    :var   01.01.2000 issue     0
    :param file: The uploaded file to create a plan for.
    :type file: UploadFile
    :raises HTTPException: If the uploaded file size exceeds the maximum allowed size.
    """
    pathlib.Path("uploads").mkdir(exist_ok=True)
    file_path = f"uploads/{file.filename}"
    file_size = 0
    with open(file_path, "wb+") as f:
        while True:
            chunk = await file.read(1024)
            if not chunk:
                break
            file_size += len(chunk)
            if file_size > MAX_FILE_SIZE:
                f.close()
                pathlib.Path(file_path).unlink()
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=messages.FILE_SIZE_OVER,
                )
            f.write(chunk)

    result = await download_plan(file_path)

    return {"result": result}
