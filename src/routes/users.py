from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


from src.database.connect import get_db
from src.repository.users import get_customer_by_id


router = APIRouter(tags=["users"])


@router.get("/user_credits/{user_id}")
async def customer_loans(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve the credits information for a user by their ID.
    
    This endpoint retrieves a list of credit information for a user based on their ID.
    
    :param id: The ID of the user to retrieve credits for.
    :type id: int
    :param db: An asynchronous database session.
    :type db: AsyncSession
    :raises HTTPException: If the user is not found, raises a 404 error.
    :return: A list of credit information for the user.
    :rtype: List[dict]
    """
    customer = await get_customer_by_id(id, db)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return customer
