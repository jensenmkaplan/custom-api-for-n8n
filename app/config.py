import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    api_key: str
    default_model: str = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-2.5-flash")
    default_embedding_model: str = os.getenv("DEFAULT_EMBEDDING_MODEL", "text-embedding-004")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing API key. Set GEMINI_API_KEY or GOOGLE_API_KEY in environment/.env"
        )
    return Settings(api_key=api_key)
