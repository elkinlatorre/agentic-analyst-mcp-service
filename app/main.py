import uvicorn
from fastapi import FastAPI
from app.api.endpoints import router as api_router

app = FastAPI(title="AgenticAnalyst Service", version="1.0.0")

# Registering the routes from our api folder
app.include_router(api_router, prefix="/api/v1", tags=["Agent"])

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)