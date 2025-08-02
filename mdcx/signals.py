import threading
import time
from typing import TYPE_CHECKING, Literal

from PyQt5.QtCore import QObject, pyqtSignal

from mdcx.models.types import ShowData
from mdcx.utils import singleton

if TYPE_CHECKING:
    from mdcx.server.signals import ServerSignals


@singleton
class Signals(QObject):
    # region signal
    log_text = pyqtSignal(str)
    scrape_info = pyqtSignal(str)
    net_info = pyqtSignal(str)
    exec_set_main_info = pyqtSignal(ShowData)  # 主界面更新番号信息
    change_buttons_status = pyqtSignal()
    reset_buttons_status = pyqtSignal()
    set_label_file_path = pyqtSignal(str)
    label_result = pyqtSignal(str)
    logs_failed_settext = pyqtSignal(str)  # 失败面板添加信息日志信号
    view_success_file_settext = pyqtSignal(str)
    exec_set_processbar = pyqtSignal(int)  # 进度条信号量
    exec_exit_app = pyqtSignal()  # 退出信号量
    view_failed_list_settext = pyqtSignal(str)
    exec_show_list_name = pyqtSignal(str, ShowData, str)
    logs_failed_show = pyqtSignal(str)  # 失败面板添加信息日志信号

    # endregion
    def __init__(self):
        super().__init__()
        self.log_lock = threading.Lock()
        self.detail_log_list = []
        self.stop = False

    def add_log(self, *text):
        """打印日志到日志页下方详情框"""
        if self.stop:
            return
        try:
            with self.log_lock:
                self.detail_log_list.append(f" ⏰ {time.strftime('%H:%M:%S', time.localtime())} {' '.join(text)}")
        except Exception:
            pass

    def get_log(self):
        with self.log_lock:
            text = "\n".join(self.detail_log_list)
            self.detail_log_list = []
        return text

    def show_traceback_log(self, text):
        print(text)
        self.add_log(text)

    def show_log_text(self, text):
        self.log_text.emit(text)

    def show_scrape_info(self, before_info=""):
        self.scrape_info.emit(before_info)

    def show_net_info(self, text):
        self.net_info.emit(text)

    def set_main_info(self, show_data=None):
        if show_data is None:
            show_data = ShowData.empty()
        self.exec_set_main_info.emit(show_data)

    def show_list_name(self, status: Literal["succ", "fail"], show_data: ShowData, real_number=""):
        self.exec_show_list_name.emit(status, show_data, real_number)


signal_qt = Signals()
signal: "Signals | ServerSignals" = signal_qt


def set_signal(signal_instance: "Signals | ServerSignals"):
    global signal
    signal = signal_instance
