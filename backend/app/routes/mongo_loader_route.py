import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from backend.app.auth import get_current_admin
from backend.mongo_loader import load_csvs, build_documents, insert_to_mongo

router = APIRouter(prefix="/admin", tags=["admin"])


class LoadRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')


@router.post("/load-mongo")
async def load_mongo(req: LoadRequest, current_user=Depends(get_current_admin)):
    """Administrator-only import into the configured application database."""
    dfs = load_csvs()
    docs = build_documents(dfs)

    uri = os.environ.get("MONGO_URI") or os.environ.get("MONGODB_URI")
    if not uri:
        raise HTTPException(status_code=503, detail="Application database is not configured.")

    try:
        insert_to_mongo(uri, os.environ.get("MONGO_DB", "meds"), docs)
    except Exception as e:
        raise HTTPException(status_code=503, detail="Reference import failed; check the configured database.") from e

    return {"status": "ok", "inserted_counts": {k: len(v) for k, v in docs.items()}}
