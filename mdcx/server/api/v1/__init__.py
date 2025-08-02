from fastapi import APIRouter, Security

from ...dependencies import api_key_header
from .config import router as config_router
from .files import router as files_router
from .legacy import router as legacy_router
from .ws import router as ws_router

api = APIRouter(prefix="/api/v1", dependencies=[Security(api_key_header)])
api.include_router(config_router)
api.include_router(ws_router)
api.include_router(files_router)
api.include_router(legacy_router)
