from typing import Optional

from fastapi import APIRouter, HTTPException

from ..gemini_client import GeminiClient
from ..schemas import EmbedRequest, EmbedResponse

router = APIRouter(tags=["embeddings"])


@router.post("/embed", response_model=EmbedResponse)
async def embed_texts(payload: EmbedRequest) -> EmbedResponse:
    try:
        client = GeminiClient()
        vectors = client.embed_texts(
            texts=payload.texts,
            model=payload.model,
            task_type=payload.task_type,
        )
        return EmbedResponse(embeddings=vectors)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
