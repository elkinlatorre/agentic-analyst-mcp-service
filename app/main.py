import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.endpoints import router as api_router
from app.core.graph import initialize_graph, saver_context

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    # We initialize the graph and the active connection here
    await initialize_graph()
    yield
    # --- SHUTDOWN ---
    # We close the connection properly
    await saver_context.__aexit__(None, None, None)

app = FastAPI(
    title="AgenticAnalyst PRO API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router, prefix="/api/v1", tags=["Agent"])

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)