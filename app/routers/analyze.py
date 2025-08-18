from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..gemini_client import GeminiClient
from ..schemas import AnalyzeResponse

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_documents(
    instructions: str = Form(..., description="Instructions to guide the analysis"),
    files: List[UploadFile] = File(..., description="One or more PDF files"),
    model: Optional[str] = Form(None, description="Override model (e.g., gemini-2.5-flash)"),
    use_files_api: bool = Form(False, description="Use Files API upload instead of inline bytes"),
) -> AnalyzeResponse:
    try:
        pdf_bytes_list = [await f.read() for f in files]
        if not pdf_bytes_list:
            raise HTTPException(status_code=400, detail="No files provided")

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
