"""
基本工具函数, 此模块不应依赖任何项目代码
"""

import ctypes
import inspect
import os
import platform
import random
import re
import time
import traceback
from threading import Thread


def get_mac_default_config_folder() -> str:
    """
    获取macOS下默认的配置文件夹路径

    ~/.mdcx

    :return: 配置文件夹路径
    """

    home = os.path.expanduser("~")
    folder_name = ".mdcx"
    config_folder = os.path.join(home, folder_name)
    if not os.path.exists(config_folder):
        os.makedirs(config_folder, exist_ok=True, mode=0o755)
    return config_folder


def get_current_time() -> str:
    return time.strftime("%H:%M:%S", time.localtime())


def get_used_time(start_time: float) -> int:
    return round(
        (time.time() - start_time),
    )


def get_real_time(t) -> str:
    return time.strftime("%H:%M:%S", time.localtime(t))


def add_html(text: str) -> str:
    # 特殊字符转义
    text = text.replace("=http", "🔮🧿⚔️")  # 例外不转换的

    # 替换链接为超链接
    url_list = re.findall(r"http[s]?://\S+", text)
    if url_list:
        url_list = list(set(url_list))
        url_list.sort(key=lambda i: len(i), reverse=True)
        for each_url in url_list:
            new_url = f'<a href="{each_url}">{each_url}</a>'
            text = text.replace(each_url, new_url)
    text = text.replace("🔮🧿⚔️", "=http")  # 还原不转换的

    # 链接放在span里，避免点击后普通文本变超链接，设置样式为pre-wrap（保留空格换行）
    return f'<span style="white-space: pre-wrap;">{text}</span>'


def remove_repeat(a: str) -> str:
    if a:  # 转列表去空去重
        list1 = a.split(",")  # 转列表
        list2 = list(set(list1))  # 去重
        list3 = [each for each in list2 if each.strip()]  # 去空
        list3.sort(key=list1.index)  # 排序（保持原顺序）
        a = ",".join(map(str, list3))  # 转字符串
    return a


# noinspection PyUnresolvedReferences
def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = 1
    while res == 1:
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        # raise ValueError("invalid thread id")
        pass
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def kill_a_thread(t: Thread):
    try:
        while t.is_alive():
            _async_raise(t.ident, SystemExit)
    except Exception:
        print(traceback.format_exc())
        _async_raise(t.ident, SystemExit)


def get_user_agent() -> str:
    temp_l = random.randint(109, 129)
    temp_m = random.randint(1, 5563)
    temp_n = random.randint(1, 180)
    return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{temp_l}.0.{temp_m}.{temp_n} Safari/537.36"


def get_random_headers() -> dict:
    """
    随机生成复杂的HTTP headers
    包括随机的User-Agent、Accept、Accept-Language等字段
    字段的存在与否和具体值都会随机变化
    """

    # 各种浏览器的User-Agent池
    user_agents = [
        # Chrome Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.0.{}.{} Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.0.{}.{} Safari/537.36",
        # Chrome Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.0.{}.{} Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.0.{}.{} Safari/537.36",
        # Firefox Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{}.0) Gecko/20100101 Firefox/{}.0",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:{}.0) Gecko/20100101 Firefox/{}.0",
        # Firefox Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:{}.0) Gecko/20100101 Firefox/{}.0",
        # Safari Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.{}.{} Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.{}.{} Safari/605.1.15",
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.0.{}.{} Safari/537.36 Edg/{}.0.{}.{}",
        # Mobile Chrome
        "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.0.{}.{} Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1",
    ]

    # 生成随机版本号
    def get_chrome_version():
        major = random.randint(100, 130)
        minor = random.randint(0, 5)
        build = random.randint(1000, 9999)
        patch = random.randint(100, 999)
        return major, minor, build, patch

    def get_firefox_version():
        version = random.randint(90, 120)
        return version, version

    def get_safari_version():
        major = random.randint(14, 17)
        minor = random.randint(0, 9)
        patch = random.randint(0, 9)
        return major, minor, patch

    # 随机选择User-Agent模板并填充版本号
    ua_template = random.choice(user_agents)

    if "Chrome" in ua_template and "Firefox" not in ua_template:
        if "Edg" in ua_template:
            # Edge浏览器
            chrome_ver = get_chrome_version()
            edge_ver = get_chrome_version()
            ua = ua_template.format(*chrome_ver, *edge_ver)
        else:
            # Chrome浏览器
            chrome_ver = get_chrome_version()
            ua = ua_template.format(*chrome_ver)
    elif "Firefox" in ua_template:
        # Firefox浏览器
        ff_ver = get_firefox_version()
        ua = ua_template.format(*ff_ver)
    elif "Safari" in ua_template and "Chrome" not in ua_template:
        # Safari浏览器
        safari_ver = get_safari_version()
        ua = ua_template.format(*safari_ver)
    else:
        ua = ua_template

    # 基础headers
    headers = {"User-Agent": ua}

    # Accept字段选项
    accept_options = [
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "application/json,text/plain,*/*",
        "*/*",
    ]

    # Accept-Language字段选项
    accept_language_options = [
        "zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7",
        "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "zh-CN,zh;q=0.9",
        "en-US,en;q=0.9",
        "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
        "en-US,en;q=0.5",
    ]

    # Accept-Encoding字段选项
    accept_encoding_options = ["gzip, deflate, br", "gzip, deflate", "gzip, deflate, br, zstd", "identity"]

    # Connection字段选项
    connection_options = ["keep-alive", "close"]

    # Cache-Control字段选项
    cache_control_options = ["no-cache", "max-age=0", "no-store", "must-revalidate"]

    # Sec-Fetch系列字段选项
    sec_fetch_dest_options = ["document", "empty", "image", "script", "style"]
    sec_fetch_mode_options = ["navigate", "cors", "no-cors", "same-origin"]
    sec_fetch_site_options = ["none", "same-origin", "same-site", "cross-site"]

    # 随机添加可选字段（每个字段都有一定概率被包含）
    optional_headers = [
        ("Accept", accept_options, 0.8),
        ("Accept-Language", accept_language_options, 0.9),
        ("Accept-Encoding", accept_encoding_options, 0.7),
        ("Connection", connection_options, 0.6),
        ("DNT", ["1"], 0.3),
        ("Upgrade-Insecure-Requests", ["1"], 0.5),
        ("Cache-Control", cache_control_options, 0.4),
        ("Pragma", ["no-cache"], 0.2),
        ("Sec-Fetch-Dest", sec_fetch_dest_options, 0.4),
        ("Sec-Fetch-Mode", sec_fetch_mode_options, 0.4),
        ("Sec-Fetch-Site", sec_fetch_site_options, 0.4),
        ("Sec-Fetch-User", ["?1"], 0.3),
        ("Sec-CH-UA", ['"Google Chrome";v="130", "Chromium";v="130", "Not?A_Brand";v="99"'], 0.3),
        ("Sec-CH-UA-Mobile", ["?0"], 0.3),
        ("Sec-CH-UA-Platform", ['"Windows"', '"macOS"', '"Linux"'], 0.3),
    ]

    # 随机添加字段
    for header_name, options, probability in optional_headers:
        if random.random() < probability:
            headers[header_name] = random.choice(options)

    # 随机添加一些自定义字段
    custom_headers = [
        ("X-Requested-With", ["XMLHttpRequest"], 0.2),
        ("Origin", ["https://www.google.com", "https://www.bing.com"], 0.1),
        ("Referer", ["https://www.google.com/", "https://www.bing.com/"], 0.3),
        (
            "X-Forwarded-For",
            [f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"],
            0.1,
        ),
    ]

    for header_name, options, probability in custom_headers:
        if random.random() < probability:
            if header_name == "X-Forwarded-For":
                # 生成随机IP
                ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
                headers[header_name] = ip
            else:
                headers[header_name] = random.choice(options)

    return headers


def convert_path(path: str) -> str:
    is_windows = platform.system() == "Windows"
    if is_windows:
        path = path.replace("/", "\\")
    else:
        path = path.replace("\\", "/")
    return path


def singleton(cls):
    _instance = {}

    def inner():
        if cls not in _instance:
            _instance[cls] = cls()
        return _instance[cls]

    return inner
