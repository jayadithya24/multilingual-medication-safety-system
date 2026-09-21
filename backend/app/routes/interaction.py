from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.app.auth import User, get_current_active_user

from backend.app.services.interaction_service import (
    get_interaction,
    get_multi_drug_interactions,
)
from backend.app.services.neo4j_service import get_drug_interaction


router = APIRouter()


class MultiDrugRequest(BaseModel):
    drugs: List[str]


@router.get("/interaction")
async def check_interaction(
    drug1: str = Query(..., min_length=1),
    drug2: str = Query(..., min_length=1),
    lang: str = Query("en"),
):
    interaction = None
    try:
        interaction = get_drug_interaction(drug1, drug2, lang=lang)
    except Exception as error:
        print(f"Neo4j interaction lookup fallback to dataset: {error}")

    if not interaction:
        try:
            interaction = get_interaction(drug1, drug2, lang=lang)
        except Exception as error:
            print(f"Dataset interaction lookup failed: {error}")

    if not interaction:
        return {
            "status": "not_found",
            "message": f"No interaction record was found for {drug1.strip()} and {drug2.strip()} in the current supported dataset.",
            "interaction": None,
            "lang": lang,
        }

    return {
        "status": "success",
        "interaction": interaction,
    }


@router.post("/interaction/multi")
async def check_multi_interaction(
    body: MultiDrugRequest,
    lang: str = Query("en"),
):
    result = get_multi_drug_interactions(body.drugs, lang=lang)
    return result
