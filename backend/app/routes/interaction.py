from typing import List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.services.interaction_service import (
    get_interaction,
    get_multi_drug_interactions,
    interaction_coverage,
)
from backend.app.services.neo4j_service import get_drug_interaction


router = APIRouter()


class MultiDrugRequest(BaseModel):
    drugs: List[str] = Field(..., min_length=2, max_length=50)


@router.get("/interaction")
def check_interaction(
    drug1: str = Query(..., min_length=1),
    drug2: str = Query(..., min_length=1),
    lang: str = Query("en"),
):
    # The dataset reconciles both directions; a single graph edge must not hide
    # conflicting ratings from another source row.
    try:
        coverage = interaction_coverage([drug1, drug2])
        interaction = None if coverage["unsupported_medicines"] else get_interaction(drug1, drug2, lang=lang)
    except Exception as error:
        raise HTTPException(status_code=503, detail="Interaction data is unavailable. Please try again later.") from error

    if interaction and not interaction.get("review_required"):
        try:
            live = get_drug_interaction(drug1, drug2, lang=lang)
            if live and live["severity"] == interaction["severity"]:
                # Keep curated evidence and class-match provenance from the resolver.
                interaction = dict(interaction, source="neo4j")
        except Exception:
            pass  # The reconciled dataset remains available during graph outages.

    if not interaction:
        return {
            "status": "not_found",
            "message": f"No interaction record was found for {drug1.strip()} and {drug2.strip()} in the current supported dataset.",
            "interaction": None,
            "lang": lang,
            "coverage": coverage,
        }

    return {
        "status": "success",
        "interaction": interaction,
        "coverage": coverage,
    }


@router.post("/interaction/multi")
def check_multi_interaction(
    body: MultiDrugRequest,
    lang: str = Query("en"),
):
    try:
        coverage = interaction_coverage(body.drugs)
        supported = [d for d in body.drugs if d.strip().lower() not in coverage["unsupported_medicines"]]
        result = get_multi_drug_interactions(supported, lang=lang)
        return dict(result, coverage=coverage)
    except Exception as error:
        raise HTTPException(status_code=503, detail="Interaction data is unavailable. Please try again later.") from error
