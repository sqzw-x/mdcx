# 主程序路径
import os
import re


def get_path(movie_path: str, path: str) -> str:
    # 如果没有:并且首字母没有/，这样的目录视为包含在媒体目录下，需要拼接
    if ":" not in path and not re.search(
        "^/", path
    ):  # 示例：abc 或 aaa/a，这种目录在Windows和mac都视为包含在媒体目录中
        path = os.path.join(movie_path, path)

    # 首字母是/时(不是//)，需要判断Windows路径
    elif re.search("^/[^/]", path):  # 示例：/abc/a
        if (
            ":" in movie_path or "//" in movie_path
        ):  # movie_path有“:”或者“//”表示是windows，/abc这种目录视为包含在媒体目录下
            path = path.strip("/")
            path = os.path.join(movie_path, path)
    if path and path[-1] in ["/", "\\"]:
        path = path[:-1]
    return path  # path是路径的情况有 路径包含: 或者开头是//，或者非windows平台开头是/


def showFilePath(file_path: str) -> str:
    if len(file_path) > 55:
        show_file_path = file_path[-50:]
        show_file_path = ".." + show_file_path[show_file_path.find("/") :]
        if len(show_file_path) < 25:
            show_file_path = ".." + file_path[-40:]
    else:
        show_file_path = file_path
    return show_file_path
