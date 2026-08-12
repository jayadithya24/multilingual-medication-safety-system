from fastapi import APIRouter, HTTPException

from backend.app.services.medicine_service import list_medicine_names, search_medicine

router = APIRouter()


@router.get("/medicines")
async def get_medicines():

    return {
        "status": "success",
        "medicines": list_medicine_names()
    }


@router.get("/medicine/{medicine_name}")
async def get_medicine(medicine_name: str):

    medicine = search_medicine(medicine_name)

    if medicine:

        return {
            "status": "success",
            "medicine": medicine
        }

    raise HTTPException(
        status_code=404,
        detail="Medicine not found in database."
    )