import asyncio
import os
import shutil
import subprocess
import traceback
from pathlib import Path

import aiofiles.os
from PIL import Image

from ..consts import IS_MAC, IS_WINDOWS
from ..signals import signal


def delete_file_sync(p: str | Path):
    p = Path(p)
    try:
        if not p.exists(follow_symlinks=True):  # 不删除无效的符号链接
            return True, ""
        p.unlink()
        return True, ""
    except Exception as e:
        error_info = f" 删除文件: {p}\n 错误: {e}\n{traceback.format_exc()}"
        signal.add_log(error_info)
        print(error_info)
    return False, error_info


def move_file_sync(old_path: str | Path, new_path: str | Path):
    old_path = Path(old_path)
    new_path = Path(new_path)
    try:
        if str(old_path).lower() != str(new_path).lower():
            delete_file_sync(new_path)
            shutil.move(old_path, new_path)
        return True, ""
    except Exception as e:
        error_info = f" 移动文件: {old_path}\n 目标: {new_path} \n 错误: {e}\n{traceback.format_exc()}\n"
        signal.add_log(error_info)
        print(error_info)
    return False, error_info


def copy_file_sync(old: Path | str, new: Path | str):
    old = Path(old)
    new = Path(new)
    try:
        if not old.exists():
            return False, f"不存在: {old}"
        elif new.exists() and old.samefile(new):
            return True, ""
        delete_file_sync(new)
        shutil.copy(old, new)
        return True, ""
    except Exception as e:
        error_info = f" 复制文件: {old}\n 目标: {new} \n 错误: {e}\n{traceback.format_exc()}"
        signal.add_log(error_info)
        print(error_info)
    return False, error_info


def read_link_sync(path: str):
    # 获取符号链接的真实路径
    while os.path.islink(path):
        path = os.readlink(path)
    return path


def check_pic_sync(path_pic: str):
    if os.path.exists(path_pic):
        try:
            with Image.open(path_pic) as img:  # 如果文件不是图片，报错
                img.load()  # 如果图片不完整，报错OSError: image file is truncated
                return img.size
        except Exception as e:
            signal.add_log(f"文件损坏: {path_pic} \n Error: {e}")
            try:
                os.remove(path_pic)
                signal.add_log("删除成功！")
            except Exception:
                signal.add_log("删除失败！")
    return False


def open_file_thread(file_path: Path, is_dir: bool) -> None:
    if IS_WINDOWS:
        if is_dir:
            # os.system(f'explorer /select,"{file_path}"')  pyinstall打包后打开文件时会闪现cmd窗口。
            # file_path路径必须转换为windows样式，并且加上引号（不加引号，文件名过长会截断）。select,后面不能有空格
            subprocess.Popen(f'explorer /select,"{file_path}"')
        else:
            subprocess.Popen(f'explorer "{file_path}"')
    elif IS_MAC:
        if is_dir:
            if file_path.is_symlink():
                file_path = file_path.parent
            subprocess.Popen(["open", "-R", str(file_path)])
        else:
            subprocess.Popen(["open", str(file_path)])
    else:
        if is_dir:
            if file_path.is_symlink():
                file_path = file_path.parent
            try:
                subprocess.Popen(["dolphin", "--select", file_path])
            except Exception:
                subprocess.Popen(["xdg-open", "-R", file_path])
        else:
            subprocess.Popen(["xdg-open", file_path])


async def delete_file_async(file_path: str | Path):
    """异步删除文件"""
    file_path = Path(file_path)
    try:
        if not file_path.exists(follow_symlinks=False):  # 不删除无效的符号链接
            return True, ""
        file_path.unlink()
        return True, ""
    except Exception as e:
        error_info = f" 删除文件: {file_path}\n 错误: {e}\n{traceback.format_exc()}"
        signal.add_log(error_info)
        print(error_info)
        return False, error_info


async def move_file_async(old_path: str | Path, new_path: str | Path):
    """异步移动文件"""
    old_path = Path(old_path)
    new_path = Path(new_path)
    try:
        if str(old_path).lower() != str(new_path).lower():
            await delete_file_async(new_path)
        await asyncio.to_thread(shutil.move, str(old_path), str(new_path))
        return True, ""
    except Exception as e:
        error_info = f" 移动文件: {old_path}\n 目标: {new_path} \n 错误: {e}\n{traceback.format_exc()}"
        signal.add_log(error_info)
        print(error_info)
    return False, error_info


async def copy_file_async(old_path: str | Path, new_path: str | Path):
    """异步复制文件"""
    old_path = Path(old_path)
    new_path = Path(new_path)
    try:
        if not await aiofiles.os.path.exists(old_path):
            return False, f"不存在: {old_path}"
        elif str(old_path).lower() != str(new_path).lower():
            await delete_file_async(new_path)
        await asyncio.to_thread(shutil.copy, old_path, new_path)
        return True, ""
    except Exception as e:
        error_info = f" 复制文件: {old_path}\n 目标: {new_path} \n 错误: {e}\n{traceback.format_exc()}"
        signal.add_log(error_info)
        print(error_info)
    return False, error_info


def _check_pic_blocking(path_pic: str | Path):
    """阻塞版本的图片检查，用于在线程中执行"""
    with Image.open(path_pic) as img:  # 如果文件不是图片，报错
        img.load()  # 如果图片不完整，报错OSError: image file is truncated
        return img.size


async def check_pic_async(path_pic: str | Path):
    """异步检查图片文件"""
    if await aiofiles.os.path.exists(path_pic):
        try:
            # 在线程中执行PIL操作，因为PIL不支持异步
            result = await asyncio.to_thread(_check_pic_blocking, path_pic)
            return result
        except Exception as e:
            signal.add_log(f"文件损坏: {path_pic} \n Error: {e}")
            try:
                await aiofiles.os.remove(path_pic)
                signal.add_log("删除成功！")
            except Exception:
                signal.add_log("删除失败！")
    return False
