import time
import traceback

from mdcx.config.manager import manager
from mdcx.signals import signal_qt


def show_netstatus() -> None:
    signal_qt.show_net_info(time.strftime("%Y-%m-%d %H:%M:%S").center(80, "="))
    proxy_type = ""
    retry_count = 0
    proxy = ""
    timeout = 0
    try:
        proxy_type, proxy, timeout, retry_count = (
            manager.config_v1.type,
            manager.config_v1.proxy,
            manager.config_v1.timeout,
            manager.config_v1.retry,
        )
    except Exception:
        signal_qt.show_traceback_log(traceback.format_exc())
        signal_qt.show_net_info(traceback.format_exc())
    if proxy == "" or proxy_type == "" or proxy_type == "no":
        signal_qt.show_net_info(
            f" 当前网络状态：❌ 未启用代理\n   类型： {str(proxy_type)}    地址：{str(proxy)}    超时时间：{str(timeout)}    重试次数：{str(retry_count)}"
        )
    else:
        signal_qt.show_net_info(
            f" 当前网络状态：✅ 已启用代理\n   类型： {proxy_type}    地址：{proxy}    超时时间：{str(timeout)}    重试次数：{str(retry_count)}"
        )
    signal_qt.show_net_info("=" * 80)
