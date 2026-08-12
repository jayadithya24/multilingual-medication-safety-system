from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from backend.app.services.neo4j_service import search_drug_by_text, get_drug_by_id

router = APIRouter(prefix="/neo4j", tags=["neo4j"])


@router.get("/search")
async def drug_search(term: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50)):
    results = search_drug_by_text(term, limit=limit)
    return {"results": results}


@router.get("/drugs/{drug_id}")
async def drug_details(drug_id: str):
    result = get_drug_by_id(drug_id)
    if not result:
        raise HTTPException(status_code=404, detail="Drug not found")
    return result
