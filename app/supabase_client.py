from __future__ import annotations

import os
from typing import Optional

from supabase import Client, create_client

from .config import get_settings


class SupabaseClient:
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None) -> None:
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        if not self.url or not self.key:
            raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in env")
        self.client: Client = create_client(self.url, self.key)

    def bucket(self) -> str:
        name = os.getenv("SUPABASE_BUCKET", "pdf-uploads")
        return name
