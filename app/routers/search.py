from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Query

from ..gemini_client import GeminiClient
from ..supabase_client import SupabaseClient

router = APIRouter(tags=["search"])


@router.get("/search")
async def semantic_search(q: str = Query(..., description="Query text"), top_k: int = 5) -> dict:
    sb = SupabaseClient()
    gem = GeminiClient()

    query_vec = gem.embed_texts([q])[0]

    # Naive cosine in Python over JSONB vectors (for demo-scale). For prod, use pgvector.
    # Fetch a limited set of rows to score client-side to avoid huge transfers.
    rows = (
        sb.client
        .table("document_chunks")
        .select("id,doc_id,content,embedding")
        .limit(2000)
        .execute()
    ).data or []

    def cosine(a: List[float], b: List[float]) -> float:
        import math
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(y*y for y in b))
        return dot / (na * nb + 1e-8)

    scored = []
    for r in rows:
        emb = r.get("embedding")
        if isinstance(emb, dict) and "values" in emb:
            vec = emb["values"]
        else:
            vec = emb  # if stored directly as list
        if not isinstance(vec, list):
            continue
        s = cosine(query_vec, vec)
        scored.append({"score": s, **r})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return {"results": scored[:max(1, min(top_k, 50))]}
