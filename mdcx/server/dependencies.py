from fastapi import HTTPException, status
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.requests import HTTPConnection
from fastapi.security.api_key import APIKeyBase

from .config import API_KEY, API_KEY_HEADER


class APIKeyHeader(APIKeyBase):
    """
    同时支持 HTTP 和 WebSocket 的 API Key 认证.
    """

    def __init__(self, *, name: str, scheme_name: str | None = None, description: str | None = None):
        self.model: APIKey = APIKey(**{"in": APIKeyIn.header}, name=name, description=description)  # type: ignore[arg-type]
        self.scheme_name = scheme_name or self.__class__.__name__

    async def __call__(self, request: HTTPConnection) -> str | None:
        api_key = request.headers.get(self.model.name)
        if api_key == API_KEY:
            return api_key
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")


api_key_header = APIKeyHeader(name=API_KEY_HEADER)
