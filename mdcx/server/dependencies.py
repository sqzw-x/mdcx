from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from .config import API_KEY, API_KEY_NAME

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)


async def check_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
