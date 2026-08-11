from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers from app/routers/
from app.routers import medicine, patient

# If you also created app/routes/upload.py, you can keep this import:
# from app.routes.upload import router as upload_router 

app = FastAPI(
    title="Medication Safety System",
    version="1.0.0"
)

# 1. Enable CORS (Required for Frontend connection)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any frontend/browser
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Register Routers
app.include_router(medicine.router)
app.include_router(patient.router)

# app.include_router(upload_router)  # Uncomment if upload.py exists

@app.get("/")
def root():
    return {
        "message": "Medication Safety System Backend Running"
    }

@app.get("/health")
def health():
    return {
        "status": "running",
        "project": "Multilingual Medication Safety System"
    }