from typing import Optional
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.auth import get_current_active_user
from backend.mongo_loader import load_csvs, build_documents, insert_to_mongo

router = APIRouter(prefix="/admin", tags=["admin"])


class LoadRequest(BaseModel):
    mongo_uri: Optional[str] = None
    mongo_db: Optional[str] = "meds"


@router.post("/load-mongo")
async def load_mongo(req: LoadRequest, current_user=Depends(get_current_active_user)):
    """JWT-protected endpoint to build documents from CSVs and insert into MongoDB.

    The caller must be authenticated (Bearer token). If `mongo_uri` is not supplied
    it will use the `MONGO_URI` environment variable.
    """
    dfs = load_csvs()
    docs = build_documents(dfs)

    uri = req.mongo_uri or os.environ.get("MONGO_URI")
    if not uri:
        raise HTTPException(status_code=400, detail="No MongoDB URI provided (env MONGO_URI or request body)")

    try:
        insert_to_mongo(uri, req.mongo_db or "meds", docs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to insert to MongoDB: {e}")

    return {"status": "ok", "inserted_counts": {k: len(v) for k, v in docs.items()}}
