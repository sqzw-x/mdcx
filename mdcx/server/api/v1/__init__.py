from fastapi import APIRouter, Security

from ...dependencies import check_api_key
from .files import router as files_router
from .ws import router as ws_router

api = APIRouter(prefix="/api/v1", dependencies=[Security(check_api_key)])
api.include_router(ws_router)
api.include_router(files_router)
