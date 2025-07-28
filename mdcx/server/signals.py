from collections.abc import Callable
from typing import Literal

from mdcx.models.types import ShowData


class Signal[*T = *tuple[()]]:
    def __init__(self, fn: Callable[[*T], None]):
        self.fn = fn

    def emit(self, *args: *T):
        self.fn(*args)


class ServerSignals:
    log_text: Signal[str]
    scrape_info: Signal[str]
    net_info: Signal[str]
    exec_set_main_info: Signal[ShowData]
    change_buttons_status: Signal
    reset_buttons_status: Signal
    set_label_file_path: Signal[str]
    label_result: Signal[str]
    logs_failed_settext: Signal[str]
    view_success_file_settext: Signal[str]
    exec_set_processbar: Signal[int]
    exec_exit_app: Signal
    view_failed_list_settext: Signal[str]
    exec_show_list_name: Signal[str, ShowData, str]
    logs_failed_show: Signal[str]
    stop: bool

    def __init__(self): ...

    def add_log(self, *text): ...

    def show_traceback_log(self, text): ...

    def show_log_text(self, text): ...

    def show_scrape_info(self, before_info=""): ...
    def show_net_info(self, text): ...
    def set_main_info(self, show_data=None): ...
    def show_list_name(self, status: Literal["succ", "fail"], show_data: ShowData, real_number=""): ...
