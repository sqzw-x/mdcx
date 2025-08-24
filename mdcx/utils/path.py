import os
from pathlib import Path


def showFilePath(file_path: str) -> str:
    if len(file_path) > 55:
        show_file_path = file_path[-50:]
        show_file_path = ".." + show_file_path[show_file_path.find("/") :]
        if len(show_file_path) < 25:
            show_file_path = ".." + file_path[-40:]
    else:
        show_file_path = file_path
    return show_file_path


def is_descendant(p: str | Path, parent: str | Path) -> bool:
    """
    检查 p 是否是 parent 或者 parent 的后代.

    Raises:
        OSError: 存在循环的符号链接, 无访问权限等
    """
    p = os.path.realpath(p, strict=os.path.ALLOW_MISSING)
    parent = os.path.realpath(parent, strict=os.path.ALLOW_MISSING)
    # parent = /foo/bar, p = /foo/barbar 使得简单的前缀判断失效
    # os.path.commonpath 可以处理这种情况
    return os.path.commonpath([p, parent]) == str(parent)


def is_any_descendant(p: str | Path, *parents: str | Path) -> bool:
    """
    检查 p 是否是 parents 中某路径的后代.
    """
    return any(is_descendant(p, parent) for parent in parents)
