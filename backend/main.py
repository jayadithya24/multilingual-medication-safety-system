from fastapi import FastAPI
from app.routes.upload import router as upload_router
from app.routes.mongo_loader_route import router as mongo_loader_router

app = FastAPI(
    title="Medication Safety System",
    version="1.0.0"
)

app.include_router(upload_router)
app.include_router(mongo_loader_router)

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