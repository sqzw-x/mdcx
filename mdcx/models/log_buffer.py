import asyncio
import threading
from warnings import deprecated


class LogBuffer:
    all_buffers = {}
    global_buffer = None

    @staticmethod
    def _global_buffer() -> "LogBuffer":
        if LogBuffer.global_buffer is None:
            LogBuffer.global_buffer = LogBuffer()
        return LogBuffer.global_buffer

    @staticmethod
    def _get_task_id() -> int | None:
        """获取当前协程的 Task ID，如果在协程环境下运行则返回 Task ID，否则返回线程 ID"""
        try:
            # 尝试获取当前协程
            task = asyncio.current_task()
            if task is not None:
                # 使用 Task 对象的 id 作为唯一标识符
                return id(task)
        except RuntimeError:
            # 如果不在协程环境中，会抛出 RuntimeError
            pass

        # 如果不是协程或获取失败，则回退到使用线程 ID
        return threading.current_thread().ident

    @staticmethod
    def _get_buffer(category: str) -> "LogBuffer":
        task_id = LogBuffer._get_task_id()
        if task_id is None:
            return LogBuffer._global_buffer()
        if task_id not in LogBuffer.all_buffers:
            LogBuffer.all_buffers[task_id] = {}
        if category not in LogBuffer.all_buffers[task_id]:
            LogBuffer.all_buffers[task_id][category] = LogBuffer()
        return LogBuffer.all_buffers[task_id][category]

    @staticmethod
    def clear_task():
        """清除当前任务（线程或协程）的日志缓冲区"""
        task_id = LogBuffer._get_task_id()
        if task_id is not None:
            LogBuffer.all_buffers.pop(task_id, None)

    @staticmethod
    def clear_thread():
        """兼容旧版 API，实际上调用 clear_task()"""
        LogBuffer.clear_task()

    @staticmethod
    def log() -> "LogBuffer":
        return LogBuffer._get_buffer("log")

    @staticmethod
    @deprecated("仅用于向后兼容")
    def info() -> "LogBuffer":
        return LogBuffer._get_buffer("info")

    @staticmethod
    def error() -> "LogBuffer":
        return LogBuffer._get_buffer("error")

    @staticmethod
    @deprecated("内容不会被任何位置使用")
    def req() -> "LogBuffer":
        return LogBuffer._get_buffer("req")

    def __init__(self):
        self.buffer = []

    def write(self, message, with_task_name=False):
        """
        写入日志消息

        Args:
            message: 日志消息
            with_task_name: 是否在日志消息前添加任务名称
        """
        if with_task_name:
            task_name = LogBuffer.get_task_name()
            message = f"[{task_name}] {message}"
        self.buffer.append(message)

    def get(self):
        return "".join(self.buffer)

    def last(self):
        if len(self.buffer) == 0:
            return ""
        return self.buffer[-1]

    def clear(self):
        self.buffer.clear()

    @staticmethod
    def get_task_name() -> str:
        """获取当前任务的名称（线程名或协程名）"""
        try:
            task = asyncio.current_task()
            if task:
                return task.get_name()
        except RuntimeError:
            pass

        return threading.current_thread().name or "unknown"
