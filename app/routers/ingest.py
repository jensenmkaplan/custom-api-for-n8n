from __future__ import annotations

import io
import math
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pypdf import PdfReader

from ..gemini_client import GeminiClient
from ..supabase_client import SupabaseClient

router = APIRouter(tags=["ingest"])


def chunk_text(text: str, tokens_per_chunk: int = 800) -> List[str]:
    # Simple char-based chunker as proxy; replace with token-aware if needed
    max_len = tokens_per_chunk * 4
    return [text[i : i + max_len] for i in range(0, len(text), max_len)]


@router.post("/ingest/pdf")
async def ingest_pdf(file: UploadFile = File(...)) -> dict:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    sb = SupabaseClient()
    bucket = sb.bucket()

    raw = await file.read()
    path = f"ingest/{file.filename}"

    # Upload raw PDF to storage
    try:
        sb.client.storage.from_(bucket).upload(path=path, file=raw, file_options={"contentType": "application/pdf", "upsert": True})
        public_url = sb.client.storage.from_(bucket).get_public_url(path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {exc}") from exc

    # Insert document record
    doc_res = sb.client.table("documents").insert({
        "file_name": file.filename,
        "storage_path": path,
        "public_url": public_url,
        "size_bytes": len(raw),
    }).execute()
    doc = (doc_res.data or [None])[0]
    if not doc:
        raise HTTPException(status_code=500, detail="Failed to create document record")

    # Extract text
    reader = PdfReader(io.BytesIO(raw))
    full_text: List[str] = []
    for i, page in enumerate(reader.pages):
        try:
            full_text.append(page.extract_text() or "")
        except Exception:
            full_text.append("")
    text_joined = "\n".join(full_text)

    # Chunk and embed
    chunks = chunk_text(text_joined)
    gem = GeminiClient()
    vectors = gem.embed_texts(chunks)

    rows = []
    for idx, (content, emb) in enumerate(zip(chunks, vectors)):
        rows.append({
            "doc_id": doc["id"],
            "page_num": None,
            "chunk_index": idx,
            "content": content,
            "embedding": emb,
        })

    if rows:
        sb.client.table("document_chunks").insert(rows).execute()

    # Update doc metadata
    sb.client.table("documents").update({"num_pages": len(reader.pages)}).eq("id", doc["id"]).execute()

    return {"doc_id": doc["id"], "chunks": len(rows), "public_url": public_url}
