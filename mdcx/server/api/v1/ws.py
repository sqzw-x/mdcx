from fastapi import APIRouter, WebSocket

from ...ws.manager import websocket_handler, websocket_manager

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/", name="websocket_connection")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_handler.handle_client(websocket)


@router.get("/connections", operation_id="getWebSocketConnections", summary="获取所有 WebSocket 连接信息")
async def get_connections():
    return {
        "active_connections": websocket_manager.connection_count,
        "connections": websocket_manager.get_all_connections_info(),
    }
