import base64

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

from ..config import API_KEY_HEADER

SMUGGLE_PREFIX = "base64.ws.key."


class WebSocketProtocolBearerMiddleware:
    """
    此中间件实现了对浏览器 WebSocket 认证的支持, 使其可与 HTTP/其它 WebSocket Client 共用认证逻辑.

    具体来说, 浏览器不允许向 WebSocket 添加自定义 Headers, 唯一允许的是 `sec-websocket-protocol`, 可以利用(滥用)此 Header 传递 API Key.
    此中间件将 `sec-websocket-protocol` 中 Base64 编码的 API Key 提取出来, 并设置原本用于认证的 Header.

    参考:
    - https://peterbraden.co.uk/article/websocket-auth-fastapi/
    - https://github.com/kubernetes/kubernetes/pull/47740
    """

    def __init__(self, app: ASGIApp, protocol_prefix: str = SMUGGLE_PREFIX, actual_header: str = API_KEY_HEADER):
        self.app = app
        self.protocol_prefix = protocol_prefix
        self.actual_header = actual_header

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "websocket":
            headers = MutableHeaders(scope=scope)
            protocol_str = headers.get("sec-websocket-protocol", None)
            if protocol_str is not None:
                protocols = [p.strip() for p in protocol_str.split(",")]
                for proto in protocols:
                    if proto.startswith(self.protocol_prefix):
                        # Extract and decode base64 token
                        b64token = proto[len(self.protocol_prefix) :]
                        try:
                            token_bytes = base64.urlsafe_b64decode(b64token + "=" * (-len(b64token) % 4))
                            token = token_bytes.decode("utf-8")
                            headers[self.actual_header] = token
                        except Exception:
                            # Invalid base64, ignore
                            pass
                        break
        await self.app(scope, receive, send)
