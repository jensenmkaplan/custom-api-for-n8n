from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..supabase_client import SupabaseClient

router = APIRouter(tags=["storage"])


@router.post("/storage/upload")
async def upload_pdf_to_supabase(file: UploadFile = File(...)) -> dict:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    client = SupabaseClient()
    bucket = client.bucket()

    data = await file.read()
    path = f"uploads/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"

    try:
        client.client.storage.from_(bucket).upload(path=path, file=data, file_options={"contentType": "application/pdf", "upsert": True})
        public_url = client.client.storage.from_(bucket).get_public_url(path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}") from exc

    return {"bucket": bucket, "path": path, "public_url": public_url}
