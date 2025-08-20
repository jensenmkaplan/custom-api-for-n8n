from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import analyze, embeddings
from .routers import storage, ingest, search
from .routers import dropbox_oauth

app = FastAPI(title="Gemini PDF Analysis API", version="0.1.0")

# CORS: allow all origins/methods/headers (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(analyze.router, prefix="/v1")
app.include_router(embeddings.router, prefix="/v1")
app.include_router(storage.router, prefix="/v1")
app.include_router(ingest.router, prefix="/v1")
app.include_router(search.router, prefix="/v1")
app.include_router(dropbox_oauth.router, prefix="/v1")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}