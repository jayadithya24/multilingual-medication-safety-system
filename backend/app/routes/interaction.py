from typing import List
from fastapi import APIRouter, Query
from pydantic import BaseModel

from backend.app.services.interaction_service import get_interaction, get_multi_drug_interactions


router = APIRouter()


class MultiDrugRequest(BaseModel):
    drugs: List[str]


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


@router.post("/interaction/multi")
async def check_multi_interaction(body: MultiDrugRequest):
    result = get_multi_drug_interactions(body.drugs)
    return result