import os
from fastapi import APIRouter, Depends, HTTPException
from backend.app.auth import (
    get_current_active_user,
    User,
)
from backend.mongo_loader import insert_to_mongo
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(prefix="/mongo", tags=["mongo"])


class MongoDocumentPayload(BaseModel):
    collection: str
    documents: List[Dict[str, Any]]


@router.post("/insert")
async def insert_documents(
    payload: MongoDocumentPayload,
    current_user: User = Depends(get_current_active_user),
):
    try:
        mongo_uri = os.environ.get("MONGO_URI")
        if not mongo_uri:
            raise HTTPException(status_code=400, detail="Set MONGO_URI to connect to MongoDB")

        insert_to_mongo(
            uri=mongo_uri,
            db_name=os.environ.get("MONGO_DB", "meds"),
            documents=payload.documents,
        )
        return {"message": "Documents inserted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to insert documents: {str(e)}",
        )