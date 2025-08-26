"""
刮削过程所需图片操作
"""

import os
import time
import traceback
from pathlib import Path
from typing import cast

from PIL import Image

from ..base.image import add_mark_thread
from ..config.enums import DownloadableFile, MarkType
from ..config.manager import manager
from ..models.log_buffer import LogBuffer
from ..models.types import CrawlersResult, FileInfo, OtherInfo
from ..signals import signal
from ..utils import executor, get_used_time
from ..utils.file import check_pic_async, copy_file_sync, delete_file_sync


async def add_mark(json_data: OtherInfo, file_info: FileInfo, mosaic: str):
    poster_marked = json_data.poster_marked
    thumb_marked = json_data.thumb_marked
    fanart_marked = json_data.fanart_marked
    download_files = manager.config.download_files
    mark_type = manager.config.mark_type
    has_sub = file_info.has_sub
    definition = file_info.definition
    mark_list = []
    if ("K" in definition or "UHD" in definition) and MarkType.HD in mark_type:
        if "8" in definition:
            mark_list.append("8K")
        else:
            mark_list.append("4K")
    if has_sub and "sub" in mark_type:
        mark_list.append("字幕")

    if mosaic == "有码" or mosaic == "有碼":
        if MarkType.YOUMA in mark_type:
            mark_list.append("有码")
    elif mosaic == "无码破解" or mosaic == "無碼破解":
        if MarkType.UMR in mark_type:
            mark_list.append("破解")
        elif MarkType.UNCENSORED in mark_type:
            mark_list.append("无码")
    elif mosaic == "无码流出" or mosaic == "無碼流出":
        if MarkType.LEAK in mark_type:
            mark_list.append("流出")
        elif MarkType.UNCENSORED in mark_type:
            mark_list.append("无码")
    elif (mosaic == "无码" or mosaic == "無碼") and "uncensored" in mark_type:
        mark_list.append("无码")

    if mark_list:
        download_files = manager.config.download_files
        mark_show_type = ",".join(mark_list)
        poster_path = json_data.poster_path
        thumb_path = json_data.thumb_path
        fanart_path = json_data.fanart_path

        if (
            manager.config.thumb_mark == 1
            and DownloadableFile.THUMB in download_files
            and thumb_path
            and not thumb_marked
        ):
            await add_mark_thread(thumb_path, mark_list)
            LogBuffer.log().write(f"\n 🍀 Thumb add watermark: {mark_show_type}!")
        if (
            manager.config.poster_mark == 1
            and DownloadableFile.POSTER in download_files
            and poster_path
            and not poster_marked
        ):
            await add_mark_thread(poster_path, mark_list)
            LogBuffer.log().write(f"\n 🍀 Poster add watermark: {mark_show_type}!")
        if (
            manager.config.fanart_mark == 1
            and DownloadableFile.FANART in download_files
            and fanart_path
            and not fanart_marked
        ):
            await add_mark_thread(fanart_path, mark_list)
            LogBuffer.log().write(f"\n 🍀 Fanart add watermark: {mark_show_type}!")


def cut_thumb_to_poster(json_data: CrawlersResult, thumb_path: Path, poster_path: Path, image_cut):
    start_time = time.time()
    if os.path.exists(poster_path):
        delete_file_sync(poster_path)

    img = None
    img_new = None
    img_new_png = None
    # 打开图片, 获取图片尺寸
    try:
        img = Image.open(thumb_path)  # 返回一个Image对象
        img = cast("Image.Image", img)

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

        # 不裁剪
        if image_cut == "no":
            copy_file_sync(thumb_path, poster_path)
            LogBuffer.log().write(f"\n 🍀 Poster done! (copy thumb)({get_used_time(start_time)}s)")
            json_data.poster_from = "copy thumb"
            img.close()
            return True

        # 中间裁剪
        elif image_cut == "center":
            json_data.poster_from = "thumb center"
            ax = int((w - h / 1.5) / 2)
            ay = 0
            bx = ax + int(h / 1.5)
            by = int(h)

        # 右边裁剪
        else:
            json_data.poster_from = "thumb right"
            ax, ay, bx, by = w / 1.9, 0, w, h
            if w == 800:
                if h == 439:
                    ax, ay, bx, by = 420, 0, w, h
                elif h >= 499 and h <= 503:
                    ax, ay, bx, by = 437, 0, w, h
                else:
                    ax, ay, bx, by = 421, 0, w, h
            elif w == 840 and h == 472:
                ax, ay, bx, by = 473, 0, 788, h

        # 裁剪并保存
        img_new = img.convert("RGB")
        img_new = cast("Image.Image", img_new)
        img_new_png = img_new.crop((ax, ay, bx, by))
        img_new_png.save(poster_path, quality=95, subsampling=0)
        if executor.run(check_pic_async(poster_path)):
            LogBuffer.log().write(f"\n 🍀 Poster done! ({json_data.poster_from})({get_used_time(start_time)}s)")
            return True
        LogBuffer.log().write(f"\n 🥺 Poster cut failed! ({json_data.poster_from})({get_used_time(start_time)}s)")
    except Exception as e:
        LogBuffer.log().write(
            f"\n 🥺 Poster failed! ({json_data.poster_from})({get_used_time(start_time)}s)\n    {str(e)}"
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
