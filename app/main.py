from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import analyze, embeddings
from .routers import storage, ingest, search

app = FastAPI(title="Gemini PDF Analysis API", version="0.1.0")

app.include_router(analyze.router, prefix="/v1")
app.include_router(embeddings.router, prefix="/v1")
app.include_router(storage.router, prefix="/v1")
app.include_router(ingest.router, prefix="/v1")
app.include_router(search.router, prefix="/v1")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
