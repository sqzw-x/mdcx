# 主程序路径
import os
import platform
import re
import sys
import traceback
from os.path import abspath, dirname, realpath

from models.signals import signal
from models.config.config import config


def get_main_path():
    try:
        main_path = realpath(__file__)
        for _ in range(4):  # 根据此文件路径确定根目录, 若移动此文件可能需要修改
            main_path = dirname(main_path)
    except Exception as e:
        signal.show_traceback_log('get_main_path ERROR: ' + str(e) + traceback.format_exc())
        main_path = abspath(sys.path[0])

        # 或sys.argv[0],取的是被初始执行的脚本的所在目录，打包后路径会变成\base_libarary.zip
        # base_path = abspath(".") 取的是起始执行目录，和os.getcwd()结果一样，不太准
    if getattr(sys, 'frozen', False):  # 是否Bundle Resource，是否打包成exe运行
        if platform.system() == 'Darwin':
            main_path = config.get_mac_default_config_folder()
        else:
            main_path = abspath("")  # 打包后，路径是准的
    return main_path


def get_path(movie_path, path):
    # 如果没有:并且首字母没有/，这样的目录视为包含在媒体目录下，需要拼接
    if ':' not in path and not re.search('^/', path):  # 示例：abc 或 aaa/a，这种目录在Windows和mac都视为包含在媒体目录中
        path = os.path.join(movie_path, path)

    # 首字母是/时(不是//)，需要判断Windows路径
    elif re.search('^/[^/]', path):  # 示例：/abc/a
        if ':' in movie_path or '//' in movie_path:  # movie_path有“:”或者“//”表示是windows，/abc这种目录视为包含在媒体目录下
            path = path.strip('/')
            path = os.path.join(movie_path, path)
    if path and path[-1] in ['/', '\\']:
        path = path[:-1]
    return path  # path是路径的情况有 路径包含: 或者开头是//，或者非windows平台开头是/


def showFilePath(file_path):
    if len(file_path) > 55:
        show_file_path = file_path[-50:]
        show_file_path = '..' + show_file_path[show_file_path.find('/'):]
        if len(show_file_path) < 25:
            show_file_path = '..' + file_path[-40:]
    else:
        show_file_path = file_path
    return show_file_path
