from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app.services.risk_contract import UnsupportedModelInput

def predict_risk(**kwargs):
    # Optional ML dependencies must not prevent login or the rest of the API starting.
    from backend.app.services.risk_prediction_service import predict_risk as predict
    return predict(**kwargs)


router = APIRouter(
    prefix="/ml",
    tags=["ML Risk Prediction"],
)


class PairPredictionRequest(BaseModel):
    drug1: str = Field(..., min_length=1, max_length=200)
    drug2: str = Field(..., min_length=1, max_length=200)


@router.get('/ddinter/model-info')
def ddinter_model_info():
    try:
        from backend.app.services.ddinter_prediction_service import model_info
        return model_info()
    except (ImportError, OSError) as error:
        raise HTTPException(503, 'DDInter model unavailable. Download and train it using the documented scripts.') from error


@router.post('/ddinter/predict')
def ddinter_predict(request: PairPredictionRequest):
    try:
        from backend.app.services.ddinter_prediction_service import predict
        return predict(request.drug1, request.drug2)
    except (ImportError, OSError) as error:
        raise HTTPException(503, 'DDInter model unavailable. Reference checking remains available.') from error


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


@router.get("/model-info")
def model_info():
    try:
        from backend.app.services.risk_prediction_service import get_model_info
        return get_model_info()
    except Exception as error:
        raise HTTPException(503, "Experimental model unavailable. Install backend requirements and check ml/models.") from error


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

    except UnsupportedModelInput as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except (ImportError, OSError) as e:
        raise HTTPException(status_code=503, detail="Experimental model unavailable. The reference-based interaction checker remains available.") from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Experimental severity classification is unavailable.",
        )
