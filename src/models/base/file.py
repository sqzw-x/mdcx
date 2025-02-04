import os
import shutil
import subprocess
import traceback

from PIL import Image

from models.config.config import config
from models.signals import signal


def delete_file(file_path):
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


def move_file(old_path, new_path):
    try:
        if old_path.lower().replace("\\", "/") != new_path.lower().replace("\\", "/"):
            delete_file(new_path)
            shutil.move(old_path, new_path)
        return True, ""
    except Exception as e:
        error_info = f" Move File: {old_path}\n To: {new_path} \n Error: {e}\n{traceback.format_exc()}\n"
        signal.add_log(error_info)
        print(error_info)
        return False, error_info


def copy_file(old_path, new_path):
    for _ in range(3):
        try:
            if not os.path.exists(old_path):
                return False, f"不存在: {old_path}"
            elif old_path.lower() != new_path.lower():
                delete_file(new_path)
            shutil.copy(old_path, new_path)
            return True, ""
        except Exception as e:
            error_info = f" Copy File: {old_path}\n To: {new_path} \n Error: {e}\n{traceback.format_exc()}"
            signal.add_log(error_info)
            print(error_info)
    return False, error_info


def read_link(path):
    # 获取符号链接的真实路径
    while os.path.islink(path):
        path = os.readlink(path)
    return path


def split_path(path):
    if "\\" in path:
        p, f = os.path.split(path.replace("\\", "/"))
        return p.replace("/", "\\"), f
    return os.path.split(path)


def open_image(pic_path):
    try:
        with Image.open(pic_path) as img:
            return True, img
    except Exception as e:
        error_info = f" Open: {pic_path}\n Error: {e}\n{traceback.format_exc()}"
        signal.add_log(error_info)
        print(error_info)
        return False, error_info


def check_pic(path_pic):
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
            except:
                signal.add_log("删除失败！")
    return False


def _open_file_thread(file_path, is_dir):
    if config.is_windows:
        if is_dir:
            # os.system(f'explorer /select,"{file_path}"')  pyinstall打包后打开文件时会闪现cmd窗口。
            # file_path路径必须转换为windows样式，并且加上引号（不加引号，文件名过长会截断）。select,后面不能有空格！！！
            subprocess.Popen(f'explorer /select,"{file_path}"')
        else:
            subprocess.Popen(f'explorer "{file_path}"')
    elif config.is_mac:
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
            except:
                subprocess.Popen(["xdg-open", "-R", file_path])
        else:
            subprocess.Popen(["xdg-open", file_path])
