from typing import Optional
import time
import secrets
from urllib.parse import urlencode

import os
import requests
from fastapi import APIRouter, HTTPException, Query

APP_KEY = os.getenv("DROPBOX_APP_KEY")
APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

# In-memory state store: state -> timestamp
_oauth_state_store: dict[str, float] = {}

router = APIRouter(tags=["dropbox"])


@router.get("/dropbox/oauth/start")
def dropbox_oauth_start(redirect_uri: Optional[str] = Query(None, description="Callback URI to use; must be registered in your Dropbox app")) -> dict:
    """Return an authorize URL and a state token. Use the URL to direct the user to Dropbox's consent page.

    The client should open the returned `authorize_url` in a browser, complete consent, and Dropbox will
    redirect to `redirect_uri` with `code` and `state` query params. Then call `/v1/dropbox/oauth/callback` with the same params.
    """
    if not APP_KEY or not APP_SECRET:
        raise HTTPException(status_code=500, detail="Missing DROPBOX_APP_KEY or DROPBOX_APP_SECRET in environment")

    # Default redirect if not provided
    if not redirect_uri:
        redirect_uri = "https://custom-api-for-n8n.onrender.com/v1/dropbox/oauth/callback"

    state = secrets.token_urlsafe(16)
    _oauth_state_store[state] = time.time()

    params = {
        "client_id": APP_KEY,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
        "token_access_type": "offline",  # request refresh token
    }
    authorize_url = f"https://www.dropbox.com/oauth2/authorize?{urlencode(params)}"
    return {"authorize_url": authorize_url, "state": state, "redirect_uri": redirect_uri}


@router.get("/dropbox/oauth/callback")
def dropbox_oauth_callback(code: str = Query(...), state: str = Query(...), redirect_uri: Optional[str] = Query(None)) -> dict:
    """Exchange the authorization code for an access token (and refresh token if available).

    Returns the JSON token response from Dropbox. The caller should store tokens securely.
    """
    if state not in _oauth_state_store:
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    # Optional expiry: allow states younger than 15 minutes
    ts = _oauth_state_store.pop(state, 0)
    if time.time() - ts > 15 * 60:
        raise HTTPException(status_code=400, detail="State expired")

    if not APP_KEY or not APP_SECRET:
        raise HTTPException(status_code=500, detail="Missing DROPBOX_APP_KEY or DROPBOX_APP_SECRET in environment")

    if not redirect_uri:
        redirect_uri = "https://custom-api-for-n8n.onrender.com/v1/dropbox/oauth/callback"

    token_url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    try:
        resp = requests.post(token_url, data=data, auth=(APP_KEY, APP_SECRET), timeout=15)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Token request failed: {exc}") from exc

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Token exchange failed: {resp.text}")

    return resp.json()


@router.post("/dropbox/oauth/refresh")
def dropbox_oauth_refresh(refresh_token: str = Query(..., description="Dropbox refresh token to exchange for a new access token")) -> dict:
    """Exchange a refresh token for a new access token.

    Note: For server-side use, prefer configuring DROPBOX_REFRESH_TOKEN, DROPBOX_APP_KEY, DROPBOX_APP_SECRET
    in environment variables. This endpoint is provided for manual testing.
    """
    if not APP_KEY or not APP_SECRET:
        raise HTTPException(status_code=500, detail="Missing DROPBOX_APP_KEY or DROPBOX_APP_SECRET in environment")

    token_url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    try:
        resp = requests.post(token_url, data=data, auth=(APP_KEY, APP_SECRET), timeout=15)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Refresh request failed: {exc}") from exc

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Refresh failed: {resp.text}")

    return resp.json()


