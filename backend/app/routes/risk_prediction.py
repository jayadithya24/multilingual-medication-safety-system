from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.risk_prediction_service import predict_risk


router = APIRouter(
    prefix="/ml",
    tags=["ML Risk Prediction"],
)


class RiskPredictionRequest(BaseModel):
    age: int = Field(..., ge=0, le=120)
    gender: str = Field(..., min_length=1)
    conditions: str = Field(..., min_length=1)
    kidney_function: str = Field(..., min_length=1)
    liver_function: str = Field(..., min_length=1)
    bmi_category: str = Field(..., min_length=1)
    n_drugs: int = Field(..., ge=1)
    drug_1: str = Field(..., min_length=1)
    drug_2: str = Field(..., min_length=1)


@router.post("/risk-predict")
def risk_predict(request: RiskPredictionRequest):
    try:
        result = predict_risk(
            age=request.age,
            gender=request.gender,
            conditions=request.conditions,
            kidney_function=request.kidney_function,
            liver_function=request.liver_function,
            bmi_category=request.bmi_category,
            n_drugs=request.n_drugs,
            drug_1=request.drug_1,
            drug_2=request.drug_2,
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Risk prediction failed: {str(e)}",
        )
