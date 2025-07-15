import os
import time
import traceback
from typing import cast

from PIL import Image, ImageFilter
from PyQt5.QtGui import QImageReader, QPixmap

from ..core.json_data import JsonData, LogBuffer
from ..signals import signal
from .file import check_pic, copy_file, delete_file
from .utils import get_used_time


def get_pixmap(pic_path: str, poster=True, pic_from=""):
    try:
        # 使用 QImageReader 加载，适合加载大文件，pixmap适合显示
        # 判断是否可读取
        img = QImageReader(pic_path)
        if img.canRead():
            img = img.read()
            pix = QPixmap(img)
            pic_width = img.size().width()
            pic_height = img.size().height()
            pic_file_size = int(os.path.getsize(pic_path) / 1024)
            if pic_width and pic_height:
                if poster:
                    if pic_width / pic_height > 156 / 220:
                        w = 156
                        h = int(156 * pic_height / pic_width)
                    else:
                        w = int(220 * pic_width / pic_height)
                        h = 220
                else:
                    if pic_width / pic_height > 328 / 220:
                        w = 328
                        h = int(328 * pic_height / pic_width)
                    else:
                        w = int(220 * pic_width / pic_height)
                        h = 220
                msg = f"{pic_from.title()}: {pic_width}*{pic_height}/{pic_file_size}KB"
                return [True, pix, msg, w, h]
        delete_file(pic_path)
        if poster:
            return [False, "", "封面图损坏", 156, 220]
        return [False, "", "缩略图损坏", 328, 220]
    except Exception:
        signal.show_log_text(traceback.format_exc())
        return [False, "", "加载失败", 156, 220]


def fix_size(path: str, naming_rule: str):
    poster_path = os.path.join(path, (naming_rule + "-poster.jpg"))
    pic = None
    try:
        if os.path.exists(poster_path):
            pic = Image.open(poster_path)
            (width, height) = pic.size
            if not 2 / 3 - 0.05 <= width / height <= 2 / 3 + 0.05:  # 仅处理会过度拉伸的图片
                fixed_pic = pic.resize((int(width), int(3 / 2 * width)))  # 拉伸图片
                fixed_pic = fixed_pic.filter(ImageFilter.GaussianBlur(radius=50))  # 高斯模糊
                fixed_pic.paste(pic, (0, int((3 / 2 * width - height) / 2)))  # 粘贴原图
                fixed_pic.save(poster_path, quality=95, subsampling=0)
    except Exception:
        signal.show_log_text(f"{traceback.format_exc()}\n Pic: {poster_path}")
    finally:
        if pic is not None:
            pic.close()


def cut_thumb_to_poster(
    json_data: JsonData,
    thumb_path: str,
    poster_path: str,
    image_cut="",
):
    start_time = time.time()
    if os.path.exists(poster_path):
        delete_file(poster_path)

    img = None
    img_new = None
    img_new_png = None
    # 打开图片, 获取图片尺寸
    try:
        img = Image.open(thumb_path)  # 返回一个Image对象
        img = cast(Image.Image, img)

        w, h = img.size
        prop = h / w

        # 判断裁剪方式
        if not image_cut:
            if prop >= 1.4:
                image_cut = "no"
            elif prop >= 1:
                image_cut = "center"
            else:
                image_cut = "right"
            json_data["image_cut"] = image_cut

        # 不裁剪
        if image_cut == "no":
            copy_file(thumb_path, poster_path)
            LogBuffer.log().write(f"\n 🍀 Poster done! (copy thumb)({get_used_time(start_time)}s)")
            json_data["poster_from"] = "copy thumb"
            img.close()
            return True

        # 中间裁剪
        elif image_cut == "center":
            json_data["poster_from"] = "thumb center"
            ax = int((w - h / 1.5) / 2)
            ay = 0
            bx = ax + int(h / 1.5)
            by = int(h)

        # 右边裁剪
        else:
            json_data["poster_from"] = "thumb right"
            ax, ay, bx, by = w / 1.9, 0, w, h
            if w == 800:
                if h == 439:
                    ax, ay, bx, by = 420, 0, w, h
                elif h >= 499 and h <= 503:
                    ax, ay, bx, by = 437, 0, w, h
                else:
                    ax, ay, bx, by = 421, 0, w, h
            elif w == 840:
                if h == 472:
                    ax, ay, bx, by = 473, 0, 788, h

        # 裁剪并保存
        img_new = img.convert("RGB")
        img_new = cast(Image.Image, img_new)
        img_new_png = img_new.crop((ax, ay, bx, by))
        img_new_png.save(poster_path, quality=95, subsampling=0)
        if check_pic(poster_path):
            LogBuffer.log().write(f"\n 🍀 Poster done! ({json_data['poster_from']})({get_used_time(start_time)}s)")
            return True
        LogBuffer.log().write(f"\n 🥺 Poster cut failed! ({json_data['poster_from']})({get_used_time(start_time)}s)")
    except Exception as e:
        LogBuffer.log().write(
            f"\n 🥺 Poster failed! ({json_data['poster_from']})({get_used_time(start_time)}s)\n    {str(e)}"
        )
        signal.show_traceback_log(traceback.format_exc())
        signal.show_log_text(f"{traceback.format_exc()}\n Pic: {thumb_path}")
        return False
    finally:
        if img_new_png:
            img_new_png.close()
        if img_new:
            img_new.close()
        if img:
            img.close()
    return False


def cut_pic(pic_path: str):
    # 打开图片, 获取图片尺寸
    img = None
    img_new = None
    img_new_png = None
    try:
        img = Image.open(pic_path)  # 返回一个Image对象

        w, h = img.size
        prop = h / w

        # 判断裁剪方式
        if prop < 1.4:  # 胖，裁剪左右
            ax = int((w - h / 1.5) / 2)
            ay = 0
            bx = int(ax + h / 1.5)
            by = int(h)
        elif prop > 1.6:  # 瘦，裁剪上下
            ax = 0
            ay = int((h - 1.5 * w) / 2)
            bx = int(w)
            by = int(h - ay)
        else:
            img.close()
            return

        # 裁剪并保存
        img_new = img.convert("RGB")
        img_new_png = img_new.crop((ax, ay, bx, by))
        img_new_png.save(pic_path, quality=95, subsampling=0)
    except Exception:
        signal.show_traceback_log(traceback.format_exc())
        signal.show_log_text(traceback.format_exc())
    finally:
        if img_new_png:
            img_new_png.close()
        if img_new:
            img_new.close()
        if img:
            img.close()


def fix_pic(pic_path: str, new_path: str):
    pic = None
    try:
        pic = Image.open(pic_path)
        (w, h) = pic.size
        prop = w / h
        if prop < 1.156:  # 左右居中
            backdrop_w = int(1.156 * h)  # 背景宽度
            backdrop_h = int(h)  # 背景宽度
            foreground_x = int((backdrop_w - w) / 2)  # 前景x点
            foreground_y = 0  # 前景y点
        else:  # 下面对齐
            ax, ay, bx, by = int(w * 0.0155), int(h * 0.0888), int(w * 0.9833), int(h * 0.9955)
            pic_new = pic.convert("RGB")
            pic = pic_new.crop((ax, ay, bx, by))
            backdrop_w = bx - ax
            backdrop_h = int((bx - ax) / 1.156)
            foreground_x = 0
            foreground_y = int(backdrop_h - (by - ay))
        fixed_pic = pic.resize((backdrop_w, backdrop_h))  # 背景拉伸
        fixed_pic = fixed_pic.filter(ImageFilter.GaussianBlur(radius=50))  # 背景高斯模糊
        fixed_pic.paste(pic, (foreground_x, foreground_y))  # 粘贴原图
        fixed_pic = fixed_pic.convert("RGB")
        fixed_pic.save(new_path, quality=95, subsampling=0)
    except Exception:
        signal.show_log_text(f"{traceback.format_exc()}\n Pic: {pic_path}")
        signal.show_traceback_log(traceback.format_exc())
    finally:
        if pic is not None:
            pic.close()
