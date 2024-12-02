"""
信号及日志类, 包括与 controller 通信所需的所有信号量
功能:
    向控制台输出日志
    通过信号量显示可视化日志
    其他需要操作 UI 的行为
依赖:
    此模块不应依赖除 models.base.utils 外的任何项目代码
"""
import threading
import time

from PyQt5.QtCore import QObject, pyqtSignal

from models.base.utils import singleton


@singleton
class Signals(QObject):
    # region signal
    log_text = pyqtSignal(str)
    scrape_info = pyqtSignal(str)
    net_info = pyqtSignal(str)
    set_main_info = pyqtSignal(object)  # 主界面更新番号信息
    change_buttons_status = pyqtSignal()
    reset_buttons_status = pyqtSignal()
    set_label_file_path = pyqtSignal(str)
    label_result = pyqtSignal(str)
    logs_failed_settext = pyqtSignal(str)  # 失败面板添加信息日志信号
    view_success_file_settext = pyqtSignal(str)
    exec_set_processbar = pyqtSignal(int)  # 进度条信号量
    exec_exit_app = pyqtSignal()  # 退出信号量
    view_failed_list_settext = pyqtSignal(str)
    exec_show_list_name = pyqtSignal(str, str, object, str)
    logs_failed_show = pyqtSignal(str)  # 失败面板添加信息日志信号

    # endregion
    def __init__(self):
        super().__init__()
        self.log_lock = threading.Lock()
        self.detail_log_list = []
        self.stop = False

    def add_log(self, *text):
        if self.stop:
            raise '手动停止刮削'
        try:
            with self.log_lock:
                self.detail_log_list.append(f" ⏰ {time.strftime('%H:%M:%S', time.localtime())} {' '.join(text)}")
        except:
            pass

    def get_log(self):
        with self.log_lock:
            text = '\n'.join(self.detail_log_list)
            self.detail_log_list = []
        return text

    def show_traceback_log(self, text):
        print(text)
        self.add_log(text)

    def show_log_text(self, text):
        self.log_text.emit(text)

    def show_scrape_info(self, before_info=''):
        self.scrape_info.emit(before_info)

    def show_net_info(self, text):
        self.net_info.emit(text)

    def add_label_info(self, json_data):
        self.set_main_info.emit(json_data)

    def show_list_name(self, filename, result, json_data, real_number=''):
        self.exec_show_list_name.emit(filename, result, json_data, real_number)


signal = Signals()
