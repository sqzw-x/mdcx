"""
基本工具函数, 此模块不应依赖任何项目代码
"""
import ctypes
import inspect
import platform
import random
import re
import time
import traceback


def get_current_time():
    return time.strftime("%H:%M:%S", time.localtime())


def get_used_time(start_time):
    return round((time.time() - start_time), )


def get_real_time(t):
    return time.strftime("%H:%M:%S", time.localtime(t))


def add_html(text):
    # 特殊字符转义
    text = text.replace('=http', '🔮🧿⚔️')  # 例外不转换的

    # 替换链接为超链接
    url_list = re.findall(r'http[s]?://\S+', text)
    if url_list:
        url_list = list(set(url_list))
        url_list.sort(key=lambda i: len(i), reverse=True)
        for each_url in url_list:
            new_url = f'<a href="{each_url}">{each_url}</a>'
            text = text.replace(each_url, new_url)
    text = text.replace('🔮🧿⚔️', '=http')  # 还原不转换的

    # 链接放在span里，避免点击后普通文本变超链接，设置样式为pre-wrap（保留空格换行）
    return '<span style="white-space: pre-wrap;">%s</span>' % text


def remove_repeat(a: str):
    if a:  # 转列表去空去重
        list1 = a.split(',')  # 转列表
        list2 = list(set(list1))  # 去重
        list3 = [each for each in list2 if each.strip()]  # 去空
        list3.sort(key=list1.index)  # 排序（保持原顺序）
        a = ','.join(map(str, list3))  # 转字符串
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


def kill_a_thread(t):
    try:
        while t.is_alive():
            _async_raise(t.ident, SystemExit)
    except:
        print(traceback.format_exc())
        _async_raise(t.ident, SystemExit)


def get_user_agent():
    temp_l = random.randint(109, 129)
    temp_m = random.randint(1, 5563)
    temp_n = random.randint(1, 180)
    return f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{temp_l}.0.{temp_m}.{temp_n} Safari/537.36'


def convert_path(path):
    is_windows = platform.system() == 'Windows'
    if is_windows:
        path = path.replace('/', '\\')
    else:
        path = path.replace('\\', '/')
    return path


def singleton(cls):
    _instance = {}

    def inner():
        if cls not in _instance:
            _instance[cls] = cls()
        return _instance[cls]

    return inner
