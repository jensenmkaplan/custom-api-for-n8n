from __future__ import annotations

import os
from typing import List, Optional

import dropbox

from dotenv import load_dotenv

load_dotenv()


class DropboxClient:
    def __init__(self, token: Optional[str] = None) -> None:
        # Support either a short-lived access token or a refresh token setup
        access_token = token or os.getenv("DROPBOX_ACCESS_TOKEN")
        refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")
        app_key = os.getenv("DROPBOX_APP_KEY")
        app_secret = os.getenv("DROPBOX_APP_SECRET")

        if refresh_token:
            # Use refresh-token based auth (recommended for production)
            if not app_key or not app_secret:
                raise RuntimeError("When using DROPBOX_REFRESH_TOKEN, also set DROPBOX_APP_KEY and DROPBOX_APP_SECRET")
            self.client = dropbox.Dropbox(
                oauth2_refresh_token=refresh_token,
                app_key=app_key,
                app_secret=app_secret,
            )
        elif access_token:
            # Fallback to static access token (suitable for development)
            self.client = dropbox.Dropbox(access_token)
        else:
            raise RuntimeError(
                "Missing Dropbox credentials. Set DROPBOX_REFRESH_TOKEN (+ APP_KEY/APP_SECRET) or DROPBOX_ACCESS_TOKEN in environment/.env"
            )

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


