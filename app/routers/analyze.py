from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Body, Query, Header

from ..gemini_client import GeminiClient
from ..schemas import AnalyzeResponse
from ..dropbox_client import DropboxClient

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_documents(
    instructions_header: Optional[str] = Header(None, alias="X-Instructions", description="Instructions provided via header (preferred)") ,
    instructions_form: Optional[str] = Form(None, description="Instructions to guide the analysis (form)"),
    instructions_query: Optional[str] = Query(None, description="Instructions to guide the analysis (query string, used when sending JSON body)"),
    body_payload: Optional[object] = Body(None, description="Optional JSON payload (array/object) containing Dropbox file metadata from which IDs will be extracted; may also carry 'instructions'") ,
    files: Optional[List[UploadFile]] = File(None, description="One or more PDF files (optional when using Dropbox)"),
    model: Optional[str] = Form(None, description="Override model (e.g., gemini-2.5-flash)"),
    use_files_api: bool = Form(False, description="Use Files API upload instead of inline bytes"),
    use_dropbox: bool = Query(False, description="If true, fetch PDFs from Dropbox using dropbox_paths or dropbox_ids"),
    dropbox_paths: Optional[str] = Query(None, description="Comma-separated Dropbox file paths to fetch (required if use_dropbox=true and dropbox_ids not provided)"),
    dropbox_ids: Optional[str] = Query(None, description="Comma-separated Dropbox file IDs to fetch (optional alternative to dropbox_paths)"),
) -> AnalyzeResponse:
    try:
        # prefer header, then form instructions, then query instructions, then instructions inside JSON body
        instructions = instructions_header or instructions_form or instructions_query
        if not instructions:
            # Look for instructions in the JSON body payload in several common shapes
            def _extract_instructions(obj):
                if isinstance(obj, dict):
                    # direct field
                    if obj.get("instructions"):
                        return obj.get("instructions")
                    # nested containers commonly named 'body', 'payload', or 'data'
                    for key in ("body", "payload", "data"):
                        val = obj.get(key)
                        if isinstance(val, dict) and val.get("instructions"):
                            return val.get("instructions")
                        if isinstance(val, list):
                            for item in val:
                                if isinstance(item, dict) and item.get("instructions"):
                                    return item.get("instructions")
                    return None
                elif isinstance(obj, list):
                    for elem in obj:
                        if isinstance(elem, dict) and elem.get("instructions"):
                            return elem.get("instructions")
                        # also check nested 'body' inside list elements
                        if isinstance(elem, dict):
                            for key in ("body", "payload", "data"):
                                val = elem.get(key)
                                if isinstance(val, dict) and val.get("instructions"):
                                    return val.get("instructions")
                                if isinstance(val, list):
                                    for item in val:
                                        if isinstance(item, dict) and item.get("instructions"):
                                            return item.get("instructions")
                    return None
                return None

            instr = _extract_instructions(body_payload)
            if instr:
                instructions = instr

        if not instructions:
            raise HTTPException(status_code=400, detail="instructions is required (header, form, query string, or JSON body)")
        pdf_bytes_list: List[bytes] = []

        if use_dropbox:
            # Prefer explicit IDs if provided; otherwise extract from JSON body, then fallback to paths
            try:
                db = DropboxClient()
                if dropbox_ids:
                    ids = [d.strip() for d in dropbox_ids.split(",") if d.strip()]
                    pdf_bytes_list = db.download_ids(ids)
                else:
                    # extract ids from provided JSON body payload which may be a list/containers or a dict
                    ids: List[str] = []
                    try:
                        containers = []
                        if isinstance(body_payload, list):
                            containers = body_payload
                        elif isinstance(body_payload, dict):
                            containers = [body_payload]

                        for container in containers:
                            if not isinstance(container, dict):
                                continue
                            data = container.get("data")
                            if isinstance(data, list):
                                for item in data:
                                    if isinstance(item, dict) and item.get("id"):
                                        ids.append(item["id"])
                            # support top-level objects with an id
                            if container.get("id"):
                                ids.append(container.get("id"))
                    except Exception:
                        raise HTTPException(status_code=400, detail="Invalid JSON body structure for Dropbox IDs")

                    if ids:
                        pdf_bytes_list = db.download_ids(ids)
                    else:
                        # fallback to dropbox_paths if provided
                        if not dropbox_paths:
                            raise HTTPException(status_code=400, detail="dropbox_paths or dropbox_ids or JSON body with ids is required when use_dropbox is true")
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
