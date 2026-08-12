from fastapi import APIRouter, HTTPException, Query
from backend.app.services.medicine_service import list_medicine_names, search_medicine

router = APIRouter()


@router.get("/medicines")
async def get_medicines(lang: str = Query("en")):
    return {
        "status": "success",
        "medicines": list_medicine_names(lang=lang)
    }


@router.get("/medicine/{medicine_name}")
async def get_medicine(medicine_name: str, lang: str = Query("en")):
    medicine = search_medicine(medicine_name, lang=lang)

    if medicine:
        return {
            "status": "success",
            "medicine": medicine
        }

    raise HTTPException(
        status_code=404,
        detail=f"Medicine '{medicine_name}' not found in database."
    )