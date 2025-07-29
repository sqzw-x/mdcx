import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from inspect import isawaitable
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from ..config import WS_PROTOCOL
from .types import ConnectionStatus, Handler, MessageType, Middleware, WebSocketMessage

logger = logging.getLogger(__name__)


@dataclass
class WebSocketConnection:
    """WebSocket 连接信息"""

    client_id: str
    websocket: WebSocket
    status: ConnectionStatus
    connected_at: datetime
    last_ping: datetime | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def is_active(self) -> bool:
        """检查连接是否活跃"""
        return self.status == ConnectionStatus.CONNECTED and self.websocket.client_state == WebSocketState.CONNECTED


class WebSocketManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self._connections: dict[str, WebSocketConnection] = {}
        self._message_handlers: dict[MessageType, list[Handler]] = {}
        self._middleware: list[Middleware] = []
        self._ping_interval: int = 30  # 心跳间隔(秒)
        self._ping_task: asyncio.Task | None = None

    @property
    def active_connections(self) -> list[WebSocketConnection]:
        """获取所有活跃连接"""
        return [conn for conn in self._connections.values() if conn.is_active]

    @property
    def connection_count(self) -> int:
        """获取活跃连接数"""
        return len(self.active_connections)

    def add_middleware(self, middleware: Middleware):
        """添加中间件"""
        self._middleware.append(middleware)

    def add_message_handler(self, message_type: MessageType, handler: Handler):
        """添加消息处理器"""
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []
        self._message_handlers[message_type].append(handler)

    def remove_message_handler(self, message_type: MessageType, handler: Handler):
        """移除消息处理器"""
        if message_type in self._message_handlers:
            try:
                self._message_handlers[message_type].remove(handler)
            except ValueError:
                pass

    async def connect(self, websocket: WebSocket, client_id: str | None = None) -> str:
        """接受新的 WebSocket 连接"""
        await websocket.accept(subprotocol=WS_PROTOCOL)

        if client_id is None:
            client_id = str(uuid.uuid4())

        connection = WebSocketConnection(
            client_id=client_id, websocket=websocket, status=ConnectionStatus.CONNECTED, connected_at=datetime.now()
        )

        self._connections[client_id] = connection

        # 发送连接成功消息
        await self.send_to_client(
            client_id,
            WebSocketMessage(
                type=MessageType.CONNECT, data={"client_id": client_id, "status": "connected"}, client_id=client_id
            ),
        )

        # 启动心跳任务
        if self._ping_task is None:
            self._ping_task = asyncio.create_task(self._ping_loop())

        logger.info(f"WebSocket client {client_id} connected")
        return client_id

    async def disconnect(self, client_id: str):
        """断开指定客户端连接"""
        if client_id in self._connections:
            connection = self._connections[client_id]
            connection.status = ConnectionStatus.DISCONNECTED

            if connection.websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await connection.websocket.close()
                except Exception as e:
                    logger.error(f"Error closing websocket for client {client_id}: {e}")

            del self._connections[client_id]
            logger.info(f"WebSocket client {client_id} disconnected")

            # 如果没有活跃连接，停止心跳任务
            if not self.active_connections and self._ping_task:
                self._ping_task.cancel()
                self._ping_task = None

    async def send_to_client(self, client_id: str, message: WebSocketMessage) -> bool:
        """向指定客户端发送消息"""
        if client_id not in self._connections:
            logger.warning(f"Client {client_id} not found")
            return False

        connection = self._connections[client_id]
        if not connection.is_active:
            logger.warning(f"Client {client_id} is not active")
            return False

        try:
            await connection.websocket.send_text(message.to_json())
            return True
        except Exception as e:
            logger.error(f"Error sending message to client {client_id}: {e}")
            await self.disconnect(client_id)
            return False

    async def broadcast(self, message: WebSocketMessage, exclude_clients: list[str] | None = None):
        """向所有活跃客户端广播消息"""
        if exclude_clients is None:
            exclude_clients = []

        tasks = []
        for connection in self.active_connections:
            if connection.client_id not in exclude_clients:
                tasks.append(self.send_to_client(connection.client_id, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def send_notification(self, client_id: str, title: str, content: str, level: str = "info"):
        """发送通知消息"""
        message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={"title": title, "content": content, "level": level},
            client_id=client_id,
        )
        return await self.send_to_client(client_id, message)

    async def send_progress(self, client_id: str, progress: int, total: int, description: str = ""):
        """发送进度消息"""
        message = WebSocketMessage(
            type=MessageType.PROGRESS,
            data={
                "progress": progress,
                "total": total,
                "percentage": round((progress / total) * 100, 2) if total > 0 else 0,
                "description": description,
            },
            client_id=client_id,
        )
        return await self.send_to_client(client_id, message)

    async def send_error(self, client_id: str, error_code: str, error_message: str):
        """发送错误消息"""
        message = WebSocketMessage(
            type=MessageType.ERROR, data={"error_code": error_code, "error_message": error_message}, client_id=client_id
        )
        return await self.send_to_client(client_id, message)

    async def handle_message(self, client_id: str, data: str | dict):
        """处理接收到的消息"""
        try:
            # 解析消息
            if isinstance(data, str):
                message = WebSocketMessage.from_json(data)
            else:
                message = WebSocketMessage.from_dict(data)

            message.client_id = client_id

            # 应用中间件
            for middleware in self._middleware:
                r = middleware(message)
                if isawaitable(r):
                    r = await r
                message = r
                if message is None:
                    return

            # 处理心跳消息
            if message.type == MessageType.PING:
                await self._handle_ping(client_id)
                return

            # 调用消息处理器
            if message.type in self._message_handlers:
                for handler in self._message_handlers[message.type]:
                    try:
                        r = handler(client_id, message)
                        if isawaitable(r):
                            await r
                    except Exception as e:
                        logger.error(f"Error in message handler: {e}")
                        await self.send_error(client_id, "HANDLER_ERROR", str(e))

        except Exception as e:
            logger.error(f"Error handling message from client {client_id}: {e}")
            await self.send_error(client_id, "MESSAGE_PARSE_ERROR", str(e))

    async def _handle_ping(self, client_id: str):
        """处理心跳消息"""
        if client_id in self._connections:
            self._connections[client_id].last_ping = datetime.now()
            await self.send_to_client(client_id, WebSocketMessage(type=MessageType.PONG, client_id=client_id))

    async def _ping_loop(self):
        """心跳循环"""
        while True:
            try:
                await asyncio.sleep(self._ping_interval)

                # 检查需要清理的连接
                to_disconnect = []
                for client_id, connection in self._connections.items():
                    if not connection.is_active:
                        to_disconnect.append(client_id)
                    elif (
                        connection.last_ping
                        and (datetime.now() - connection.last_ping).seconds > self._ping_interval * 2
                    ):
                        # 超时未响应心跳
                        to_disconnect.append(client_id)

                # 断开超时连接
                for client_id in to_disconnect:
                    await self.disconnect(client_id)

                # 如果没有活跃连接，退出循环
                if not self.active_connections:
                    break

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ping loop: {e}")

    def get_connection_info(self, client_id: str) -> dict[str, Any] | None:
        """获取连接信息"""
        if client_id not in self._connections:
            return None

        connection = self._connections[client_id]
        return {
            "client_id": connection.client_id,
            "status": connection.status.value,
            "connected_at": connection.connected_at.isoformat(),
            "last_ping": connection.last_ping.isoformat() if connection.last_ping else None,
            "metadata": connection.metadata,
            "is_active": connection.is_active,
        }

    def get_all_connections_info(self) -> list[dict[str, Any]]:
        """获取所有连接信息"""
        result = []
        for client_id in self._connections.keys():
            info = self.get_connection_info(client_id)
            if info is not None:
                result.append(info)
        return result


class WebSocketHandler:
    """WebSocket 处理器类"""

    def __init__(self, manager: WebSocketManager):
        self.manager = manager
        self._setup_default_handlers()

    def _setup_default_handlers(self):
        """设置默认消息处理器"""
        self.manager.add_message_handler(MessageType.STATUS, self._handle_status_request)

    async def _handle_status_request(self, client_id: str, message: WebSocketMessage):
        """处理状态请求"""
        status_data = {
            "server_time": datetime.now().isoformat(),
            "connection_count": self.manager.connection_count,
            "client_info": self.manager.get_connection_info(client_id),
        }

        response = WebSocketMessage(type=MessageType.STATUS, data=status_data, client_id=client_id)
        await self.manager.send_to_client(client_id, response)

    async def handle_client(self, websocket: WebSocket, client_id: str | None = None):
        """处理单个客户端连接"""
        actual_client_id = await self.manager.connect(websocket, client_id)

        async def test_log_to_all():
            while actual_client_id in self.manager._connections:
                await asyncio.sleep(1)
                await self.manager.send_to_client(
                    actual_client_id,
                    WebSocketMessage(
                        type=MessageType.CUSTOM,
                        data={
                            "message": f"Test log from client {actual_client_id}",
                            "timestamp": datetime.now().isoformat(),
                        },
                        client_id=actual_client_id,
                    ),
                )

        asyncio.create_task(test_log_to_all())
        try:
            while True:
                # 接收消息
                data = await websocket.receive_text()
                await self.manager.handle_message(actual_client_id, data)

        except WebSocketDisconnect:
            logger.info(f"Client {actual_client_id} disconnected normally")
        except Exception as e:
            logger.error(f"Error handling client {actual_client_id}: {e}")
        finally:
            await self.manager.disconnect(actual_client_id)


# 全局 WebSocket 管理器实例
websocket_manager = WebSocketManager()
websocket_handler = WebSocketHandler(websocket_manager)


# 便利函数
async def send_notification_to_all(title: str, content: str, level: str = "info"):
    """向所有客户端发送通知"""
    message = WebSocketMessage(type=MessageType.NOTIFICATION, data={"title": title, "content": content, "level": level})
    await websocket_manager.broadcast(message)


async def send_progress_to_all(event: str, current: int, total: int, description: str = ""):
    """向所有客户端发送进度更新"""
    message = WebSocketMessage(
        type=MessageType.PROGRESS,
        data={
            "progress": current,
            "total": total,
            "percentage": round((current / total) * 100, 2) if total > 0 else 0,
            "description": description,
        },
    )
    await websocket_manager.broadcast(message)


# 自定义消息处理器示例
async def handle_custom_message(client_id: str, message: WebSocketMessage):
    """处理自定义消息"""
    logger.info(f"Received custom message from {client_id}: {message.data}")

    # 回显消息
    response = WebSocketMessage(
        type=MessageType.CUSTOM,
        data={"echo": message.data, "processed_by": "server", "original_client": client_id},
        client_id=client_id,
    )
    await websocket_manager.send_to_client(client_id, response)


# 注册自定义消息处理器
websocket_manager.add_message_handler(MessageType.CUSTOM, handle_custom_message)


# 中间件示例：记录所有消息
def message_logging_middleware(message: WebSocketMessage) -> WebSocketMessage:
    """消息日志中间件"""
    logger.info(f"Processing message: type={message.type.value}, client={message.client_id}")
    return message


websocket_manager.add_middleware(message_logging_middleware)
