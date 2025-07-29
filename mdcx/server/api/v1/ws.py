from fastapi import APIRouter, WebSocket

from ...ws.manager import websocket_handler, websocket_manager

router = APIRouter(prefix="/ws")


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点"""
    await websocket_handler.handle_client(websocket)


@router.get("/connections")
async def get_connections():
    """获取所有连接信息"""
    return {
        "active_connections": websocket_manager.connection_count,
        "connections": websocket_manager.get_all_connections_info(),
    }
