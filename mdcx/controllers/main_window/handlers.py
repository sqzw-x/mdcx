import time
import traceback

from mdcx.config.manager import config
from mdcx.signals import signal


def show_netstatus() -> None:
    signal.show_net_info(time.strftime("%Y-%m-%d %H:%M:%S").center(80, "="))
    proxy_type = ""
    retry_count = 0
    proxy = ""
    timeout = 0
    try:
        proxy_type, proxy, timeout, retry_count = config.type, config.proxy, config.timeout, config.retry
    except Exception:
        signal.show_traceback_log(traceback.format_exc())
        signal.show_net_info(traceback.format_exc())
    if proxy == "" or proxy_type == "" or proxy_type == "no":
        signal.show_net_info(
            f" 当前网络状态：❌ 未启用代理\n   类型： {str(proxy_type)}    地址：{str(proxy)}    超时时间：{str(timeout)}    重试次数：{str(retry_count)}"
        )
    else:
        signal.show_net_info(
            f" 当前网络状态：✅ 已启用代理\n   类型： {proxy_type}    地址：{proxy}    超时时间：{str(timeout)}    重试次数：{str(retry_count)}"
        )
    signal.show_net_info("=" * 80)
