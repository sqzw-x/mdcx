from fastapi import APIRouter, WebSocket
from fastapi.responses import HTMLResponse

from ...ws.manager import websocket_handler, websocket_manager

router = APIRouter(prefix="/ws")


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点"""
    await websocket_handler.handle_client(websocket)


@router.websocket("/{client_id}")
async def websocket_endpoint_with_id(websocket: WebSocket, client_id: str):
    """带客户端 ID 的 WebSocket 端点"""
    await websocket_handler.handle_client(websocket, client_id)


@router.get("/test")
async def get():
    """提供简单的 WebSocket 测试页面"""
    return HTMLResponse("""
<!DOCTYPE html>
<html>
    <head>
        <title>WebSocket Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .messages { border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; margin: 10px 0; }
            .controls { margin: 10px 0; }
            input, button { margin: 5px; padding: 8px; }
            .message { margin: 2px 0; padding: 5px; border-radius: 3px; }
            .sent { background-color: #e3f2fd; }
            .received { background-color: #f3e5f5; }
            .system { background-color: #e8f5e8; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>WebSocket Manager Test</h1>
            <div class="controls">
                <input type="text" id="clientId" placeholder="客户端 ID (可选)" />
                <button onclick="connect()">连接</button>
                <button onclick="disconnect()">断开连接</button>
                <span id="status">未连接</span>
            </div>
            
            <div class="controls">
                <input type="text" id="messageInput" placeholder="输入消息" style="width: 300px;" />
                <select id="messageType">
                    <option value="custom">自定义</option>
                    <option value="ping">心跳</option>
                    <option value="status">状态</option>
                </select>
                <button onclick="sendMessage()">发送消息</button>
            </div>
            
            <div class="controls">
                <button onclick="requestStatus()">请求状态</button>
                <button onclick="sendPing()">发送心跳</button>
                <button onclick="clearMessages()">清空消息</button>
            </div>
            
            <div id="messages" class="messages"></div>
        </div>

        <script>
            let ws = null;
            let clientId = null;

            function connect() {
                const inputClientId = document.getElementById('clientId').value;
                const url = inputClientId ? `ws://localhost:8000/ws/${inputClientId}` : 'ws://localhost:8000/ws';
                
                ws = new WebSocket(url);
                
                ws.onopen = function(event) {
                    document.getElementById('status').textContent = '已连接';
                    addMessage('已连接到服务器', 'system');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    addMessage(`收到: ${JSON.stringify(data, null, 2)}`, 'received');
                    
                    if (data.type === 'connect') {
                        clientId = data.data.client_id;
                        addMessage(`客户端 ID: ${clientId}`, 'system');
                    }
                };
                
                ws.onclose = function(event) {
                    document.getElementById('status').textContent = '已断开';
                    addMessage('连接已断开', 'system');
                };
                
                ws.onerror = function(error) {
                    addMessage(`错误: ${error}`, 'system');
                };
            }

            function disconnect() {
                if (ws) {
                    ws.close();
                    ws = null;
                }
            }

            function sendMessage() {
                if (!ws) {
                    alert('请先连接');
                    return;
                }
                
                const input = document.getElementById('messageInput');
                const messageType = document.getElementById('messageType').value;
                
                const message = {
                    type: messageType,
                    data: { content: input.value },
                    timestamp: new Date().toISOString()
                };
                
                ws.send(JSON.stringify(message));
                addMessage(`发送: ${JSON.stringify(message, null, 2)}`, 'sent');
                input.value = '';
            }

            function requestStatus() {
                if (!ws) {
                    alert('请先连接');
                    return;
                }
                
                const message = {
                    type: 'status',
                    data: {},
                    timestamp: new Date().toISOString()
                };
                
                ws.send(JSON.stringify(message));
                addMessage('请求状态信息', 'sent');
            }

            function sendPing() {
                if (!ws) {
                    alert('请先连接');
                    return;
                }
                
                const message = {
                    type: 'ping',
                    timestamp: new Date().toISOString()
                };
                
                ws.send(JSON.stringify(message));
                addMessage('发送心跳', 'sent');
            }

            function addMessage(message, type) {
                const messages = document.getElementById('messages');
                const div = document.createElement('div');
                div.className = `message ${type}`;
                div.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong>: ${message}`;
                messages.appendChild(div);
                messages.scrollTop = messages.scrollHeight;
            }

            function clearMessages() {
                document.getElementById('messages').innerHTML = '';
            }

            // 键盘事件
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
</html>
    """)


@router.get("/connections")
async def get_connections():
    """获取所有连接信息"""
    return {
        "active_connections": websocket_manager.connection_count,
        "connections": websocket_manager.get_all_connections_info(),
    }
