import json
import uuid
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

type JsonSerializable = Mapping[str, JsonSerializable] | list[JsonSerializable] | str | int | float | bool | None
type Handler[T: JsonSerializable] = (
    Callable[[str, WebSocketMessage[T]], None] | Callable[[str, WebSocketMessage[T]], Awaitable[None]]
)
type Middleware[T: JsonSerializable] = (
    Callable[[WebSocketMessage[T]], WebSocketMessage[T] | None]
    | Callable[[WebSocketMessage[T]], Awaitable[WebSocketMessage[T] | None]]
)


class MessageType(Enum):
    """消息类型枚举"""

    PING = "ping"
    PONG = "pong"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    NOTIFICATION = "notification"
    ERROR = "error"
    PROGRESS = "progress"
    STATUS = "status"
    CUSTOM = "custom"


class ConnectionStatus(Enum):
    """连接状态枚举"""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class WebSocketMessage[T: JsonSerializable]:
    """WebSocket 消息数据类"""

    type: MessageType
    data: T | None = None
    timestamp: datetime | None = None
    message_id: str | None = None
    client_id: str | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        result = asdict(self)
        result["type"] = self.type.value
        result["timestamp"] = self.timestamp.isoformat() if self.timestamp else None
        return result

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebSocketMessage":
        """从字典创建消息对象"""
        if isinstance(data.get("type"), str):
            data["type"] = MessageType(data["type"])
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "WebSocketMessage":
        """从 JSON 字符串创建消息对象"""
        return cls.from_dict(json.loads(json_str))
