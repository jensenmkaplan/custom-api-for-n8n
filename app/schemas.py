from typing import List, Optional

from pydantic import BaseModel, Field


class EmbedRequest(BaseModel):
    texts: List[str] = Field(..., description="Texts to embed")
    model: Optional[str] = Field(None, description="Embedding model override")
    task_type: Optional[str] = Field(None, description="Embedding task type per docs (e.g., RETRIEVAL_DOCUMENT)")


class EmbedResponse(BaseModel):
    embeddings: List[List[float]]


class AnalyzeResponse(BaseModel):
    text: str
