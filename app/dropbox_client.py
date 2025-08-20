from __future__ import annotations

import os
from typing import List, Optional

import dropbox

from dotenv import load_dotenv

load_dotenv()


class DropboxClient:
    def __init__(self, token: Optional[str] = None) -> None:
        token = token or os.getenv("DROPBOX_ACCESS_TOKEN")
        if not token:
            raise RuntimeError("Missing Dropbox access token. Set DROPBOX_ACCESS_TOKEN in environment/.env")
        self.client = dropbox.Dropbox(token)

    def download_paths(self, paths: List[str]) -> List[bytes]:
        results: List[bytes] = []
        for p in paths:
            # Dropbox paths should start with '/'
            dp = p if p.startswith("/") else f"/{p}"
            metadata, res = self.client.files_download(dp)
            results.append(res.content)
        return results

    def download_ids(self, ids: List[str]) -> List[bytes]:
        """Download files by Dropbox file IDs. Uses the 'id:<file_id>' syntax supported by files_download."""
        results: List[bytes] = []
        for fid in ids:
            # Normalize id string
            arg = fid if fid.startswith("id:") else f"id:{fid}"
            metadata, res = self.client.files_download(arg)
            results.append(res.content)
        return results


