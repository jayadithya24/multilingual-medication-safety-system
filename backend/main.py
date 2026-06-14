from fastapi import FastAPI

app = FastAPI(
    title="Medication Safety System",
    version="1.0.0"
)

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