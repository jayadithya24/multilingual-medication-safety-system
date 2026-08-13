from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.app.auth import User, get_current_active_user

from backend.app.services.interaction_service import get_interaction, get_multi_drug_interactions


router = APIRouter()


class MultiDrugRequest(BaseModel):
    drugs: List[str]


@router.get("/interaction")
async def check_interaction(
    drug1: str = Query(..., min_length=1),
    drug2: str = Query(..., min_length=1),
    lang: str = Query("en"),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can check drug interactions")

    interaction = get_interaction(drug1, drug2, lang=lang)

    if interaction:
        return {
            "status": "success",
            "interaction": interaction,
        }

    return {
        "status": "not_found",
        "message": "No known interaction found",
    }


@router.post("/interaction/multi")
async def check_multi_interaction(
    body: MultiDrugRequest,
    lang: str = Query("en"),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can check drug interactions")

    result = get_multi_drug_interactions(body.drugs, lang=lang)
    return result
