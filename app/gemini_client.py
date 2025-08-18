from __future__ import annotations

import io
from typing import Iterable, List, Optional

from google import genai
from google.genai import types

from .config import get_settings


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None) -> None:
        settings = get_settings()
        self.client = genai.Client(api_key=api_key or settings.api_key)
        self.default_model = settings.default_model
        self.default_embedding_model = settings.default_embedding_model

    def generate_from_pdfs(
        self,
        instructions: str,
        pdf_bytes_list: Iterable[bytes],
        model: Optional[str] = None,
        use_files_api: bool = False,
    ) -> str:
        model_name = model or self.default_model

        # Prefer inline bytes for small PDFs per docs; optionally use Files API
        parts: List[types.Part] = []

        if use_files_api:
            try:
                for data in pdf_bytes_list:
                    buf = io.BytesIO(data)
                    uploaded = self.client.files.upload(buf, {"mime_type": "application/pdf"})
                    parts.append(types.Part.from_uri(uploaded.uri, uploaded.mime_type))
            except Exception:
                # Fallback to inline bytes if upload path not available
                parts.extend(
                    [types.Part.from_bytes(data=d, mime_type="application/pdf") for d in pdf_bytes_list]
                )
        else:
            parts.extend(
                [types.Part.from_bytes(data=d, mime_type="application/pdf") for d in pdf_bytes_list]
            )

        # Use the contents list form (list of parts + prompt text) per docs
        contents = [*parts, instructions]

        result = self.client.models.generate_content(
            model=model_name,
            contents=contents,
        )
        return result.text

    def embed_texts(
        self,
        texts: List[str],
        model: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> List[List[float]]:
        model_name = model or self.default_embedding_model

        config = types.EmbedContentConfig(task_type=task_type) if task_type else None

        result = self.client.models.embed_content(
            model=model_name,
            contents=texts,
            config=config,
        )

        vectors: List[List[float]] = []
        for emb in getattr(result, "embeddings", []) or []:
            values = getattr(emb, "values", None)
            if values is not None:
                vectors.append(list(values))
        return vectors
