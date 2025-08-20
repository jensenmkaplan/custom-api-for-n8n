from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..gemini_client import GeminiClient
from ..schemas import AnalyzeResponse
from ..dropbox_client import DropboxClient

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_documents(
    instructions: str = Form(..., description="Instructions to guide the analysis"),
    files: Optional[List[UploadFile]] = File(None, description="One or more PDF files (optional when using Dropbox)"),
    model: Optional[str] = Form(None, description="Override model (e.g., gemini-2.5-flash)"),
    use_files_api: bool = Form(False, description="Use Files API upload instead of inline bytes"),
    use_dropbox: bool = Form(False, description="If true, fetch PDFs from Dropbox using dropbox_paths"),
    dropbox_paths: Optional[str] = Form(None, description="Comma-separated Dropbox file paths to fetch (required if use_dropbox=true)"),
) -> AnalyzeResponse:
    try:
        pdf_bytes_list: List[bytes] = []

        if use_dropbox:
            if not dropbox_paths:
                raise HTTPException(status_code=400, detail="dropbox_paths is required when use_dropbox is true")
            paths = [p.strip() for p in dropbox_paths.split(",") if p.strip()]
            try:
                db = DropboxClient()
                pdf_bytes_list = db.download_paths(paths)
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Dropbox download failed: {exc}") from exc
        else:
            if not files:
                raise HTTPException(status_code=400, detail="No files provided and use_dropbox is false")
            pdf_bytes_list = [await f.read() for f in files]

        if not pdf_bytes_list:
            raise HTTPException(status_code=400, detail="No PDF bytes available for analysis")

        client = GeminiClient()
        text = client.generate_from_pdfs(
            instructions=instructions,
            pdf_bytes_list=pdf_bytes_list,
            model=model,
            use_files_api=use_files_api,
        )
        return AnalyzeResponse(text=text)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
