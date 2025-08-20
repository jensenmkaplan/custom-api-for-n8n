from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Body, Query

from ..gemini_client import GeminiClient
from ..schemas import AnalyzeResponse
from ..dropbox_client import DropboxClient

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_documents(
    instructions_form: Optional[str] = Form(None, description="Instructions to guide the analysis (form)"),
    instructions_query: Optional[str] = Query(None, description="Instructions to guide the analysis (query string, used when sending JSON body)"),
    dropbox_object: Optional[list] = Body(None, description="Optional JSON payload (array/object) containing Dropbox file metadata from which IDs will be extracted"),
    files: Optional[List[UploadFile]] = File(None, description="One or more PDF files (optional when using Dropbox)"),
    model: Optional[str] = Form(None, description="Override model (e.g., gemini-2.5-flash)"),
    use_files_api: bool = Form(False, description="Use Files API upload instead of inline bytes"),
    use_dropbox: bool = Form(False, description="If true, fetch PDFs from Dropbox using dropbox_paths or dropbox_ids"),
    dropbox_paths: Optional[str] = Form(None, description="Comma-separated Dropbox file paths to fetch (required if use_dropbox=true and dropbox_ids not provided)"),
    dropbox_ids: Optional[str] = Form(None, description="Comma-separated Dropbox file IDs to fetch (optional alternative to dropbox_paths)") ,
) -> AnalyzeResponse:
    try:
        # prefer form instructions, then query instructions
        instructions = instructions_form or instructions_query
        if not instructions:
            raise HTTPException(status_code=400, detail="instructions is required (form or query string when sending JSON body)")
        pdf_bytes_list: List[bytes] = []

        if use_dropbox:
            # Prefer explicit IDs if provided
            try:
                db = DropboxClient()
                if dropbox_ids:
                    ids = [d.strip() for d in dropbox_ids.split(",") if d.strip()]
                    pdf_bytes_list = db.download_ids(ids)
                elif dropbox_object:
                    # extract ids from provided JSON object which may be a list/containers
                    ids: List[str] = []
                    # expecting structure like: [ { "data": [ {"id": "id:..."}, ... ] } ]
                    try:
                        for container in dropbox_object:
                            data = container.get("data") if isinstance(container, dict) else None
                            if isinstance(data, list):
                                for item in data:
                                    if isinstance(item, dict) and item.get("id"):
                                        ids.append(item["id"])
                            # support top-level objects with an id
                            elif isinstance(container, dict) and container.get("id"):
                                ids.append(container.get("id"))
                    except Exception:
                        raise HTTPException(status_code=400, detail="Invalid dropbox_object structure")
                    if not ids:
                        raise HTTPException(status_code=400, detail="No ids found in dropbox_object")
                    pdf_bytes_list = db.download_ids(ids)
                else:
                    if not dropbox_paths:
                        raise HTTPException(status_code=400, detail="dropbox_paths or dropbox_ids is required when use_dropbox is true")
                    paths = [p.strip() for p in dropbox_paths.split(",") if p.strip()]
                    pdf_bytes_list = db.download_paths(paths)
            except HTTPException:
                raise
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
