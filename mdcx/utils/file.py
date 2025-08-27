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
    if p == Path():
        return False, "路径不能为空"
    try:
        p.unlink(missing_ok=True)
        return True, ""
    except Exception as e:
        error_info = f" 删除文件: {p}\n 错误: {e}\n{traceback.format_exc()}"
        signal.add_log(error_info)
        print(error_info)
    return False, error_info


def move_file_sync(old: str | Path, new: str | Path):
    old = Path(old)
    new = Path(new)
    try:
        if str(old).lower() != str(new).lower():
            delete_file_sync(new)
            shutil.move(old, new)
        return True, ""
    except Exception as e:
        error_info = f" 移动文件: {old}\n 目标: {new} \n 错误: {e}\n{traceback.format_exc()}\n"
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


def read_link_sync(p: str):
    # 获取符号链接的真实路径
    while os.path.islink(p):
        p = os.readlink(p)
    return p


def check_pic_sync(p: str):
    if os.path.exists(p):
        try:
            with Image.open(p) as img:  # 如果文件不是图片，报错
                img.load()  # 如果图片不完整，报错OSError: image file is truncated
                return img.size
        except Exception as e:
            signal.add_log(f"文件损坏: {p} \n Error: {e}")
            try:
                os.remove(p)
                signal.add_log("删除成功！")
            except Exception:
                signal.add_log("删除失败！")
    return False


def open_file_thread(p: Path, is_dir: bool) -> None:
    if IS_WINDOWS:
        if is_dir:
            # os.system(f'explorer /select,"{file_path}"')  pyinstall打包后打开文件时会闪现cmd窗口。
            # file_path路径必须转换为windows样式，并且加上引号（不加引号，文件名过长会截断）。select,后面不能有空格
            subprocess.Popen(f'explorer /select,"{p}"')
        else:
            subprocess.Popen(f'explorer "{p}"')
    elif IS_MAC:
        if is_dir:
            if p.is_symlink():
                p = p.parent
            subprocess.Popen(["open", "-R", str(p)])
        else:
            subprocess.Popen(["open", str(p)])
    else:
        if is_dir:
            if p.is_symlink():
                p = p.parent
            try:
                subprocess.Popen(["dolphin", "--select", p])
            except Exception:
                subprocess.Popen(["xdg-open", "-R", p])
        else:
            subprocess.Popen(["xdg-open", p])


async def delete_file_async(p: str | Path):
    """异步删除文件"""
    p = Path(p)
    if p == Path():
        return False, "路径不能为空"
    try:
        await asyncio.to_thread(p.unlink, missing_ok=True)
        return True, ""
    except Exception as e:
        error_info = f" 删除文件: {p}\n 错误: {e}\n{traceback.format_exc()}"
        signal.add_log(error_info)
        print(error_info)
        return False, error_info


async def move_file_async(old: str | Path, new: str | Path):
    """异步移动文件"""
    old = Path(old)
    new = Path(new)
    try:
        if str(old).lower() != str(new).lower():
            await delete_file_async(new)
        await asyncio.to_thread(shutil.move, str(old), str(new))
        return True, ""
    except Exception as e:
        error_info = f" 移动文件: {old}\n 目标: {new} \n 错误: {e}\n{traceback.format_exc()}"
        signal.add_log(error_info)
        print(error_info)
    return False, error_info


async def copy_file_async(old: str | Path, new: str | Path):
    """异步复制文件"""
    old = Path(old)
    new = Path(new)
    try:
        if not await aiofiles.os.path.exists(old):
            return False, f"不存在: {old}"
        elif str(old).lower() != str(new).lower():
            await delete_file_async(new)
        await asyncio.to_thread(shutil.copy, old, new)
        return True, ""
    except Exception as e:
        error_info = f" 复制文件: {old}\n 目标: {new} \n 错误: {e}\n{traceback.format_exc()}"
        signal.add_log(error_info)
        print(error_info)
    return False, error_info


def _check_pic_blocking(p: str | Path):
    """阻塞版本的图片检查，用于在线程中执行"""
    with Image.open(p) as img:  # 如果文件不是图片，报错
        img.load()  # 如果图片不完整，报错OSError: image file is truncated
        return img.size


async def check_pic_async(p: str | Path):
    """异步检查图片文件"""
    if await aiofiles.os.path.exists(p):
        try:
            # 在线程中执行PIL操作，因为PIL不支持异步
            result = await asyncio.to_thread(_check_pic_blocking, p)
            return result
        except Exception as e:
            signal.add_log(f"文件损坏: {p} \n Error: {e}")
            try:
                await aiofiles.os.remove(p)
                signal.add_log("删除成功！")
            except Exception:
                signal.add_log("删除失败！")
    return False
