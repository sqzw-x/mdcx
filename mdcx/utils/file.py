import asyncio
import os
import shutil
import subprocess
import traceback

import aiofiles.os
from PIL import Image

from mdcx.consts import IS_MAC, IS_WINDOWS
from mdcx.signals import signal
from mdcx.utils import split_path


def delete_file_sync(file_path: str):
    try:
        for _ in range(5):
            if os.path.islink(file_path):
                pass
            elif not os.path.exists(file_path):
                break
            os.remove(file_path)
        return True, ""
    except Exception as e:
        error_info = f" Delete File: {file_path}\n Error: {e}\n{traceback.format_exc()}"
        signal.add_log(error_info)
        print(error_info)
        return False, error_info


def move_file_sync(old_path: str, new_path: str):
    try:
        if old_path.lower().replace("\\", "/") != new_path.lower().replace("\\", "/"):
            delete_file_sync(new_path)
            shutil.move(old_path, new_path)
        return True, ""
    except Exception as e:
        error_info = f" Move File: {old_path}\n To: {new_path} \n Error: {e}\n{traceback.format_exc()}\n"
        signal.add_log(error_info)
        print(error_info)
        return False, error_info


def copy_file_sync(old_path: str, new_path: str):
    error_info = ""
    for _ in range(3):
        try:
            if not os.path.exists(old_path):
                return False, f"不存在: {old_path}"
            elif old_path.lower() != new_path.lower():
                delete_file_sync(new_path)
            shutil.copy(old_path, new_path)
            return True, ""
        except Exception as e:
            error_info = f" Copy File: {old_path}\n To: {new_path} \n Error: {e}\n{traceback.format_exc()}"
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


def open_file_thread(file_path: str, is_dir: bool):
    if IS_WINDOWS:
        if is_dir:
            # os.system(f'explorer /select,"{file_path}"')  pyinstall打包后打开文件时会闪现cmd窗口。
            # file_path路径必须转换为windows样式，并且加上引号（不加引号，文件名过长会截断）。select,后面不能有空格！！！
            subprocess.Popen(f'explorer /select,"{file_path}"')
        else:
            subprocess.Popen(f'explorer "{file_path}"')
    elif IS_MAC:
        if is_dir:
            if os.path.islink(file_path):
                file_path = split_path(file_path)[0]
            subprocess.Popen(["open", "-R", file_path])
        else:
            subprocess.Popen(["open", file_path])
    else:
        if is_dir:
            if os.path.islink(file_path):
                file_path = split_path(file_path)[0]
            try:
                subprocess.Popen(["dolphin", "--select", file_path])
            except Exception:
                subprocess.Popen(["xdg-open", "-R", file_path])
        else:
            subprocess.Popen(["xdg-open", file_path])


async def delete_file_async(file_path: str):
    """异步删除文件"""
    try:
        for _ in range(5):
            if await aiofiles.os.path.islink(file_path):
                pass
            elif not await aiofiles.os.path.exists(file_path):
                break
            await aiofiles.os.remove(file_path)
        return True, ""
    except Exception as e:
        error_info = f" Delete File: {file_path}\n Error: {e}\n{traceback.format_exc()}"
        signal.add_log(error_info)
        print(error_info)
        return False, error_info


async def move_file_async(old_path: str, new_path: str):
    """异步移动文件"""
    try:
        if old_path.lower().replace("\\", "/") != new_path.lower().replace("\\", "/"):
            await delete_file_async(new_path)
            await asyncio.to_thread(shutil.move, old_path, new_path)
        return True, ""
    except Exception as e:
        error_info = f" Move File: {old_path}\n To: {new_path} \n Error: {e}\n{traceback.format_exc()}\n"
        signal.add_log(error_info)
        print(error_info)
        return False, error_info


async def copy_file_async(old_path: str, new_path: str):
    """异步复制文件"""
    error_info = ""
    for _ in range(3):
        try:
            if not await aiofiles.os.path.exists(old_path):
                return False, f"不存在: {old_path}"
            elif old_path.lower() != new_path.lower():
                await delete_file_async(new_path)
            await asyncio.to_thread(shutil.copy, old_path, new_path)
            return True, ""
        except Exception as e:
            error_info = f" Copy File: {old_path}\n To: {new_path} \n Error: {e}\n{traceback.format_exc()}"
            signal.add_log(error_info)
            print(error_info)
    return False, error_info


async def read_link_async(path: str):
    """异步获取符号链接的真实路径"""
    while await aiofiles.os.path.islink(path):
        path = await aiofiles.os.readlink(path)
    return path


def _check_pic_blocking(path_pic: str):
    """阻塞版本的图片检查，用于在线程中执行"""
    with Image.open(path_pic) as img:  # 如果文件不是图片，报错
        img.load()  # 如果图片不完整，报错OSError: image file is truncated
        return img.size


async def check_pic_async(path_pic: str):
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
