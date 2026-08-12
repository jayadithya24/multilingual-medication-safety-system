from fastapi import APIRouter, Depends
from datetime import timedelta
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.auth import (
    get_current_active_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.services.mongo_service import insert_to_mongo
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
        # Convert ACCESS_TOKEN_EXPIRE_MINUTES to timedelta
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        # The user is already authenticated and active
        insert_to_mongo(
            uri="mongodb+srv://user:pass@cluster.mongodb.net/medication_db",
            db_name="meds",
            documents=payload.documents,
        )
        return {"message": "Documents inserted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to insert documents: {str(e)}",
        )