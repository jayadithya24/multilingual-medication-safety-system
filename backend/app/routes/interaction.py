from fastapi import APIRouter, Query

from app.services.interaction_service import get_interaction


router = APIRouter()


@router.get("/interaction")
async def check_interaction(
    drug1: str = Query(..., min_length=1),
    drug2: str = Query(..., min_length=1),
):

    interaction = get_interaction(drug1, drug2)

    if interaction:
        return {
            "status": "success",
            "interaction": interaction,
        }

    return {
        "status": "not_found",
        "message": "No known interaction found",
    }