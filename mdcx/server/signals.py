import asyncio
import threading
import time
from collections.abc import Callable
from dataclasses import asdict
from typing import Any, Literal

from mdcx.models.types import ShowData
from mdcx.utils import singleton

from .ws.manager import websocket_manager
from .ws.types import MessageType, WebSocketMessage


class Signal[*T = *tuple[()]]:
    def __init__(self, fn: Callable[[*T], None]):
        self.fn = fn

    def emit(self, *args: *T):
        self.fn(*args)


@singleton
class ServerSignals:
    """
    Server端信号系统，将Qt信号转换为WebSocket消息
    """

    def __init__(self):
        self.log_lock = threading.Lock()
        self.detail_log_list = []
        self.stop = False

        # 初始化所有信号
        self.log_text = Signal(self._emit_log_text)
        self.scrape_info = Signal(self._emit_scrape_info)
        self.net_info = Signal(self._emit_net_info)
        self.exec_set_main_info = Signal(self._emit_set_main_info)
        self.change_buttons_status = Signal(self._emit_change_buttons_status)
        self.reset_buttons_status = Signal(self._emit_reset_buttons_status)
        self.set_label_file_path = Signal(self._emit_set_label_file_path)
        self.label_result = Signal(self._emit_label_result)
        self.logs_failed_settext = Signal(self._emit_logs_failed_settext)
        self.view_success_file_settext = Signal(self._emit_view_success_file_settext)
        self.exec_set_processbar = Signal(self._emit_set_processbar)
        self.exec_exit_app = Signal(self._emit_exit_app)
        self.view_failed_list_settext = Signal(self._emit_view_failed_list_settext)
        self.exec_show_list_name = Signal(self._emit_show_list_name)
        self.logs_failed_show = Signal(self._emit_logs_failed_show)

    def _broadcast_message(self, signal_name: str, data: Any):
        message = WebSocketMessage(type=MessageType.QT_SINGAL, data={"name": signal_name, "data": data})

        # 在异步上下文中广播消息
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果当前线程已经有运行的事件循环，创建一个任务
                asyncio.create_task(websocket_manager.broadcast(message))
            else:
                # 如果没有运行的事件循环，运行广播
                loop.run_until_complete(websocket_manager.broadcast(message))
        except RuntimeError:
            # 如果没有事件循环，创建一个新的
            try:
                asyncio.run(websocket_manager.broadcast(message))
            except Exception as e:
                print(f"Failed to broadcast message: {e}")

    def _emit_log_text(self, text: str):
        """发送日志文本消息"""
        self._broadcast_message("log_text", text)

    def _emit_scrape_info(self, before_info: str):
        """发送刮削信息"""
        self._broadcast_message("scrape_info", before_info)

    def _emit_net_info(self, text: str):
        """发送网络信息"""
        self._broadcast_message("net_info", text)

    def _emit_set_main_info(self, show_data: ShowData):
        """发送主界面信息更新"""
        # 将ShowData转换为可序列化的字典
        try:
            data_dict = asdict(show_data)
            self._broadcast_message("set_main_info", {"show_data": data_dict})
        except Exception as e:
            print(f"Failed to serialize ShowData: {e}")
            self._broadcast_message("set_main_info", {"show_data": None})

    def _emit_change_buttons_status(self):
        """发送按钮状态变更"""
        # self._broadcast_message("change_buttons_status", None)

    def _emit_reset_buttons_status(self):
        """发送按钮状态重置"""
        # self._broadcast_message("reset_buttons_status", None)

    def _emit_set_label_file_path(self, path: str):
        """发送文件路径标签设置"""
        # self._broadcast_message("set_label_file_path", path)

    def _emit_label_result(self, result: str):
        """发送结果标签"""
        # self._broadcast_message("label_result", result)

    def _emit_logs_failed_settext(self, text: str):
        """发送失败日志"""
        self._broadcast_message("logs_failed_settext", text)

    def _emit_view_success_file_settext(self, text: str):
        """发送成功文件信息"""
        self._broadcast_message("view_success_file_settext", text)

    def _emit_set_processbar(self, value: int):
        """发送进度条更新"""
        # 使用WebSocket的进度消息类型
        message = WebSocketMessage(
            type=MessageType.PROGRESS,
            data={"progress": value, "total": 100, "percentage": value, "description": "Processing..."},
        )
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(websocket_manager.broadcast(message))
            else:
                loop.run_until_complete(websocket_manager.broadcast(message))
        except RuntimeError:
            try:
                asyncio.run(websocket_manager.broadcast(message))
            except Exception as e:
                print(f"Failed to broadcast progress: {e}")

    def _emit_exit_app(self):
        """发送应用退出信号（Web应用可能无需处理）"""
        # self._broadcast_message("exit_app", None)

    def _emit_view_failed_list_settext(self, text: str):
        """发送失败列表文本"""
        self._broadcast_message("view_failed_list_settext", text)

    def _emit_show_list_name(self, status: str, show_data: ShowData, real_number: str):
        """发送列表名称显示"""
        try:
            data_dict = asdict(show_data)
            self._broadcast_message(
                "show_list_name", {"status": status, "show_data": data_dict, "real_number": real_number}
            )
        except Exception as e:
            print(f"Failed to serialize ShowData in show_list_name: {e}")
            self._broadcast_message("show_list_name", {"status": status, "show_data": None, "real_number": real_number})

    def _emit_logs_failed_show(self, text: str):
        """发送失败日志显示"""
        self._broadcast_message("logs_failed_show", text)

    # 以下方法保持与原始Qt信号系统相同的接口
    def add_log(self, *text):
        """打印日志到日志页下方详情框"""
        if self.stop:
            return
        try:
            with self.log_lock:
                log_text = f" ⏰ {time.strftime('%H:%M:%S', time.localtime())} {' '.join(map(str, text))}"
                self.detail_log_list.append(log_text)
                # 同时通过WebSocket发送日志
                self._broadcast_message("detail_log", log_text)
        except Exception:
            pass

    def get_log(self):
        """获取并清空日志列表"""
        with self.log_lock:
            text = "\n".join(self.detail_log_list)
            self.detail_log_list = []
        return text

    def show_traceback_log(self, text):
        """显示错误追踪日志"""
        print(text)
        self.add_log(text)

    def show_log_text(self, text):
        """显示日志文本"""
        self.log_text.emit(text)

    def show_scrape_info(self, before_info=""):
        """显示刮削信息"""
        self.scrape_info.emit(before_info)

    def show_net_info(self, text):
        """显示网络信息"""
        self.net_info.emit(text)

    def set_main_info(self, show_data=None):
        """设置主界面信息"""
        if show_data is None:
            show_data = ShowData.empty()
        self.exec_set_main_info.emit(show_data)

    def show_list_name(self, status: Literal["succ", "fail"], show_data: ShowData, real_number=""):
        """显示列表名称"""
        self.exec_show_list_name.emit(status, show_data, real_number)


# 创建全局信号实例
signal = ServerSignals()
