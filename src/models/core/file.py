"""
包括刮削过程所需的文件及路径相关操作, 不一定有实际 IO
"""

import os
import re
import shutil
import time
import traceback

from ..base.file import copy_file, delete_file, move_file, read_link, split_path
from ..base.number import (
    deal_actor_more,
    get_file_number,
    get_number_first_letter,
    get_number_letters,
    is_uncensored,
    remove_escape_string,
)
from ..base.path import showFilePath
from ..base.utils import convert_path, get_current_time, get_used_time
from ..config.consts import IS_MAC, IS_WINDOWS
from ..config.manager import config
from ..config.resources import resources
from ..entity.enums import FileMode
from ..signals import signal
from .flags import Flags
from .json_data import JsonData, LogBuffer, MoveContext, new_json_data
from .utils import get_movie_path_setting, get_new_release, nfd2c, render_name_template


def _need_clean(file_path: str, file_name: str, file_ext: str) -> bool:
    # 判断文件是否需清理
    if not config.can_clean:
        return False

    # 不清理的扩展名
    if file_ext in config.clean_ignore_ext_list:
        return False

    # 不清理的文件名包含
    for each in config.clean_ignore_contains_list:
        if each in file_name:
            return False

    # 清理的扩展名
    if file_ext in config.clean_ext_list:
        return True

    # 清理的文件名等于
    if file_name in config.clean_name_list:
        return True

    # 清理的文件名包含
    for each in config.clean_contains_list:
        if each in file_name:
            return True

    # 清理的文件大小<=(KB)
    if os.path.islink(file_path):
        file_path = os.readlink(file_path)
    if config.clean_size_list is not None:
        try:  # 路径太长时，此处会报错 FileNotFoundError: [WinError 3] 系统找不到指定的路径。
            if os.path.getsize(file_path) <= config.clean_size_list * 1024:
                return True
        except Exception:
            pass
    return False


def creat_folder(
    json_data: JsonData,
    folder_new_path: str,
    file_path: str,
    file_new_path: str,
    thumb_new_path_with_filename: str,
    poster_new_path_with_filename: str,
) -> bool:
    """判断是否创建文件夹，目标文件是否有重复文件。file_new_path是最终路径"""

    json_data["dont_move_movie"] = False  # 不需要移动和重命名视频
    json_data["del_file_path"] = False  # 在 move movie 时需要删除自己，自己是软链接，目标是原始文件
    dont_creat_folder = False  # 不需要创建文件夹

    # 正常模式、视频模式时，软连接关，成功后不移动文件开时，这时不创建文件夹
    if config.main_mode < 3 and config.soft_link == 0 and not config.success_file_move:
        dont_creat_folder = True

    # 更新模式、读取模式，选择更新c文件时，不创建文件夹
    if config.main_mode > 2 and config.update_mode == "c":
        dont_creat_folder = True

    # 如果不需要创建文件夹，当不重命名时，直接返回
    if dont_creat_folder:
        if not config.success_file_rename:
            json_data["dont_move_movie"] = True
            return True

    # 如果不存在目标文件夹，则创建文件夹
    elif not os.path.isdir(folder_new_path):
        try:
            os.makedirs(folder_new_path)
            LogBuffer.log().write("\n 🍀 Folder done! (new)")
            return True
        except Exception as e:
            if not os.path.exists(folder_new_path):
                LogBuffer.log().write(f"\n 🔴 Failed to create folder! \n    {str(e)}")
                if len(folder_new_path) > 250:
                    LogBuffer.log().write("\n    可能是目录名过长！！！建议限制目录名长度！！！越小越好！！！")
                    LogBuffer.error().write("创建文件夹失败！可能是目录名过长！")
                else:
                    LogBuffer.log().write("\n    请检查是否有写入权限！")
                    LogBuffer.error().write("创建文件夹失败！请检查是否有写入权限！")
                return False

    # 判断是否有重复文件（Windows、Mac大小写不敏感）
    convert_file_path = convert_path(file_path).lower()
    convert_file_new_path = convert_path(file_new_path).lower()

    # 当目标文件存在，是软链接时
    if os.path.islink(file_new_path):
        # 路径相同，是自己
        if convert_file_path == convert_file_new_path:
            json_data["dont_move_movie"] = True
        # 路径不同，删掉目标文件即可（不验证是否真实路径了，太麻烦）
        else:
            # 在移动时删除即可。delete_file(file_new_path)
            # 创建软链接前需要删除目标路径文件
            pass
        return True

    # 当目标文件存在，不是软链接时
    elif os.path.exists(file_new_path):
        # 待刮削的文件不是软链接
        if not os.path.islink(file_path):
            # 如果路径相同，则代表已经在成功文件夹里，不是重复文件（大小写不敏感）
            if convert_file_path == convert_file_new_path:
                json_data["dont_move_movie"] = True
                if os.path.exists(thumb_new_path_with_filename):
                    json_data["thumb_path"] = thumb_new_path_with_filename
                if os.path.exists(poster_new_path_with_filename):
                    json_data["poster_path"] = poster_new_path_with_filename
                return True

            # 路径不同
            else:
                try:
                    # 当都指向同一个文件时(此处路径不能用小写，因为Linux大小写敏感)
                    if os.stat(file_path).st_ino == os.stat(file_new_path).st_ino:
                        # 硬链接开时，不需要处理
                        if config.soft_link == 2:
                            json_data["dont_move_movie"] = True
                        # 非硬链接模式，删除目标文件
                        else:
                            # 在移动时删除即可。delete_file(file_new_path)
                            pass
                        return True
                except Exception:
                    pass

                # 路径不同，当指向不同文件时
                json_data["title"] = "Success folder already exists a same name file!"
                LogBuffer.error().write(
                    f"Success folder already exists a same name file! \n ❗️ Current file: {file_path} \n ❗️ Success folder already exists file: {file_new_path} "
                )
                return False

        # 待刮削文件是软链接
        else:
            # 看待刮削文件真实路径，路径相同，是同一个文件
            real_file_path = read_link(file_path)
            if convert_path(real_file_path).lower() == convert_file_new_path:
                # 非软硬链接时，标记删除待刮削文件自身
                if config.soft_link == 0:
                    json_data["del_file_path"] = True
                # 软硬链接时，标记不处理
                else:
                    json_data["dont_move_movie"] = True
                return True
            # 路径不同，是两个文件
            else:
                json_data["title"] = "Success folder already exists a same name file!"
                LogBuffer.error().write(
                    f"Success folder already exists a same name file! \n"
                    f" ❗️ Current file is symlink file: {file_path} \n"
                    f" ❗️ real file: {real_file_path} \n"
                    f" ❗️ Success folder already exists another real file: {file_new_path} "
                )
                return False

    # 目标文件不存在时
    return True


def move_trailer_video(
    json_data: JsonData, folder_old_path: str, folder_new_path: str, file_name: str, naming_rule: str
) -> None:
    if config.main_mode < 2:
        if not config.success_file_move and not config.success_file_rename:
            return
    if config.main_mode > 2:
        update_mode = config.update_mode
        if update_mode == "c" and not config.success_file_rename:
            return

    media_type_list = config.media_type.split("|")
    for media_type in media_type_list:
        trailer_old_path = os.path.join(folder_old_path, (file_name + "-trailer" + media_type))
        trailer_new_path = os.path.join(folder_new_path, (naming_rule + "-trailer" + media_type))
        if os.path.exists(trailer_old_path) and not os.path.exists(trailer_new_path):
            move_file(trailer_old_path, trailer_new_path)
            LogBuffer.log().write("\n 🍀 Trailer done!")


def move_bif(json_data: JsonData, folder_old_path: str, folder_new_path: str, file_name: str, naming_rule: str) -> None:
    # 更新模式 或 读取模式
    if config.main_mode == 3 or config.main_mode == 4:
        if config.update_mode == "c" and not config.success_file_rename:
            return

    elif not config.success_file_move and not config.success_file_rename:
        return
    bif_old_path = os.path.join(folder_old_path, (file_name + "-320-10.bif"))
    bif_new_path = os.path.join(folder_new_path, (naming_rule + "-320-10.bif"))
    if bif_old_path != bif_new_path and os.path.exists(bif_old_path) and not os.path.exists(bif_new_path):
        move_file(bif_old_path, bif_new_path)
        LogBuffer.log().write("\n 🍀 Bif done!")


def move_torrent(
    json_data: JsonData, folder_old_path: str, folder_new_path: str, file_name: str, movie_number: str, naming_rule: str
) -> None:
    # 更新模式 或 读取模式
    if config.main_mode == 3 or config.main_mode == 4:
        if config.update_mode == "c" and not config.success_file_rename:
            return

    # 软硬链接开时，不移动
    elif config.soft_link != 0:
        return

    elif not config.success_file_move and not config.success_file_rename:
        return
    torrent_file1 = os.path.join(folder_old_path, (file_name + ".torrent"))
    torrent_file2 = os.path.join(folder_old_path, (movie_number + ".torrent"))
    torrent_file1_new_path = os.path.join(folder_new_path, (naming_rule + ".torrent"))
    torrent_file2_new_path = os.path.join(folder_new_path, (movie_number + ".torrent"))
    if (
        os.path.exists(torrent_file1)
        and torrent_file1 != torrent_file1_new_path
        and not os.path.exists(torrent_file1_new_path)
    ):
        move_file(torrent_file1, torrent_file1_new_path)
        LogBuffer.log().write("\n 🍀 Torrent done!")

    if torrent_file2 != torrent_file1:
        if (
            os.path.exists(torrent_file2)
            and torrent_file2 != torrent_file2_new_path
            and not os.path.exists(torrent_file2_new_path)
        ):
            move_file(torrent_file2, torrent_file2_new_path)
            LogBuffer.log().write("\n 🍀 Torrent done!")


def check_file(json_data: JsonData, file_path: str, file_escape_size: float) -> tuple[bool, JsonData]:
    if os.path.islink(file_path):
        file_path = read_link(file_path)
        if "check_symlink" not in config.no_escape:
            return True, json_data

    if not os.path.exists(file_path):
        LogBuffer.error().write("文件不存在")
        LogBuffer.req().write("do_not_update_json_data_dic")
        json_data["outline"] = split_path(file_path)[1]
        json_data["tag"] = file_path
        return False, json_data
    if "no_skip_small_file" not in config.no_escape:
        file_size = os.path.getsize(file_path) / float(1024 * 1024)
        if file_size < file_escape_size:
            LogBuffer.error().write(
                f"文件小于 {file_escape_size} MB 被过滤!（实际大小 {round(file_size, 2)} MB）已跳过刮削！"
            )
            LogBuffer.req().write("do_not_update_json_data_dic")
            json_data["outline"] = split_path(file_path)[1]
            json_data["tag"] = file_path
            return False, json_data
    return True, json_data


def copy_trailer_to_theme_videos(json_data: JsonData, folder_new_path: str, naming_rule: str) -> None:
    start_time = time.time()
    download_files = config.download_files
    keep_files = config.keep_files
    theme_videos_folder_path = os.path.join(folder_new_path, "backdrops")
    theme_videos_new_path = os.path.join(theme_videos_folder_path, "theme_video.mp4")

    # 不保留不下载主题视频时，删除
    if "theme_videos" not in download_files and "theme_videos" not in keep_files:
        if os.path.exists(theme_videos_folder_path):
            shutil.rmtree(theme_videos_folder_path, ignore_errors=True)
        return

    # 保留主题视频并存在时返回
    if "theme_videos" in keep_files and os.path.exists(theme_videos_folder_path):
        LogBuffer.log().write(f"\n 🍀 Theme video done! (old)({get_used_time(start_time)}s) ")
        return

    # 不下载主题视频时返回
    if "theme_videos" not in download_files:
        return

    # 不存在预告片时返回
    trailer_name = config.trailer_simple_name
    trailer_folder = ""
    if trailer_name:
        trailer_folder = os.path.join(folder_new_path, "trailers")
        trailer_file_path = os.path.join(trailer_folder, "trailer.mp4")
    else:
        trailer_file_path = os.path.join(folder_new_path, naming_rule + "-trailer.mp4")
    if not os.path.exists(trailer_file_path):
        return

    # 存在预告片时复制
    if not os.path.exists(theme_videos_folder_path):
        os.makedirs(theme_videos_folder_path)
    if os.path.exists(theme_videos_new_path):
        delete_file(theme_videos_new_path)
    copy_file(trailer_file_path, theme_videos_new_path)
    LogBuffer.log().write("\n 🍀 Theme video done! (copy trailer)")

    # 不下载并且不保留预告片时，删除预告片
    if "trailer" not in download_files and "trailer" not in config.keep_files:
        delete_file(trailer_file_path)
        if trailer_name:
            shutil.rmtree(trailer_folder, ignore_errors=True)
        LogBuffer.log().write("\n 🍀 Trailer delete done!")


def move_other_file(
    json_data: JsonData, folder_old_path: str, folder_new_path: str, file_name: str, naming_rule: str
) -> None:
    # 软硬链接模式不移动
    if config.soft_link != 0:
        return

    # 目录相同不移动
    if convert_path(folder_new_path).lower() == convert_path(folder_old_path).lower():
        return

    # 更新模式 或 读取模式
    if config.main_mode == 3 or config.main_mode == 4:
        if config.update_mode == "c" and not config.success_file_rename:
            return

    elif not config.success_file_move and not config.success_file_rename:
        return

    files = os.listdir(folder_old_path)
    for old_file in files:
        if os.path.splitext(old_file)[1].lower() in config.media_type:
            continue
        if json_data["number"] in old_file or file_name in old_file or naming_rule in old_file:
            if "-cd" not in old_file.lower():  # 避免多分集时，其他分级的内容被移走
                old_file_old_path = os.path.join(folder_old_path, old_file)
                old_file_new_path = os.path.join(folder_new_path, old_file)
                if (
                    old_file_old_path != old_file_new_path
                    and os.path.exists(old_file_old_path)
                    and not os.path.exists(old_file_new_path)
                ):
                    move_file(old_file_old_path, old_file_new_path)
                    LogBuffer.log().write(f"\n 🍀 Move {old_file} done!")


def move_file_to_failed_folder(
    json_data: JsonData,
    file_path: str,
    folder_old_path: str,
) -> str:
    failed_folder = json_data["failed_folder"]

    # 更新模式、读取模式，不移动失败文件；不移动文件-关时，不移动； 软硬链接开时，不移动
    main_mode = config.main_mode
    if main_mode == 3 or main_mode == 4 or not config.failed_file_move or config.soft_link != 0:
        LogBuffer.log().write(f"\n 🙊 [Movie] {file_path}")
        return file_path

    # 创建failed文件夹
    if config.failed_file_move == 1 and not os.path.exists(failed_folder):
        try:
            os.makedirs(failed_folder)
        except Exception:
            signal.show_traceback_log(traceback.format_exc())
            signal.show_log_text(traceback.format_exc())

    # 获取文件路径
    file_full_name = split_path(file_path)[1]
    file_name, file_ext = os.path.splitext(file_full_name)
    trailer_old_path_no_filename = convert_path(os.path.join(folder_old_path, "trailers/trailer.mp4"))
    trailer_old_path_with_filename = file_path.replace(file_ext, "-trailer.mp4")

    # 重复改名
    file_new_path = convert_path(os.path.join(failed_folder, file_full_name))
    while os.path.exists(file_new_path) and file_new_path != convert_path(file_path):
        file_new_path = file_new_path.replace(file_ext, "@" + file_ext)

    # 移动
    try:
        move_file(file_path, file_new_path)
        LogBuffer.log().write("\n 🔴 Move file to the failed folder!")
        LogBuffer.log().write(f"\n 🙊 [Movie] {file_new_path}")
        json_data["file_path"] = file_new_path
        error_info = LogBuffer.error().get()
        LogBuffer.error().clear()
        LogBuffer.error().write(error_info.replace(file_path, file_new_path))

        # 同步移动预告片
        trailer_new_path = file_new_path.replace(file_ext, "-trailer.mp4")
        if not os.path.exists(trailer_new_path):
            try:
                has_trailer = False
                if os.path.exists(trailer_old_path_with_filename):
                    has_trailer = True
                    move_file(trailer_old_path_with_filename, trailer_new_path)
                elif os.path.exists(trailer_old_path_no_filename):
                    has_trailer = True
                    move_file(trailer_old_path_no_filename, trailer_new_path)
                if has_trailer:
                    LogBuffer.log().write("\n 🔴 Move trailer to the failed folder!")
                    LogBuffer.log().write(f"\n 🔴 [Trailer] {trailer_new_path}")
            except Exception as e:
                LogBuffer.log().write(f"\n 🔴 Failed to move trailer to the failed folder! \n    {str(e)}")

        # 同步移动字幕
        sub_type_list = config.sub_type.split("|")
        sub_type_new_list = []
        [sub_type_new_list.append(".chs" + i) for i in sub_type_list if ".chs" not in i]
        for sub in sub_type_new_list:
            sub_old_path = file_path.replace(os.path.splitext(file_path)[1], sub)
            sub_new_path = file_new_path.replace(os.path.splitext(file_new_path)[1], sub)
            if os.path.exists(sub_old_path) and not os.path.exists(sub_new_path):
                result, error_info = move_file(sub_old_path, sub_new_path)
                if not result:
                    LogBuffer.log().write(f"\n 🔴 Failed to move sub to the failed folder!\n     {error_info}")
                else:
                    LogBuffer.log().write("\n 💡 Move sub to the failed folder!")
                    LogBuffer.log().write(f"\n 💡 [Sub] {sub_new_path}")
        return file_new_path
    except Exception as e:
        LogBuffer.log().write(f"\n 🔴 Failed to move the file to the failed folder! \n    {str(e)}")
        return file_path


def move_movie(json_data: MoveContext, file_path: str, file_new_path: str) -> bool:
    # 明确不需要移动的，直接返回
    if json_data["dont_move_movie"]:
        LogBuffer.log().write(f"\n 🍀 Movie done! \n 🙉 [Movie] {file_path}")
        return True

    # 明确要删除自己的，删除后返回
    if json_data["del_file_path"]:
        delete_file(file_path)
        LogBuffer.log().write(f"\n 🍀 Movie done! \n 🙉 [Movie] {file_new_path}")
        json_data["file_path"] = file_new_path
        return True

    # 软链接模式开时，先删除目标文件，再创建软链接(需考虑自身是软链接的情况)
    if config.soft_link == 1:
        temp_path = file_path
        # 自身是软链接时，获取真实路径
        if os.path.islink(file_path):
            file_path = read_link(file_path)  # delete_file(temp_path)
        # 删除目标路径存在的文件，否则会创建失败，
        delete_file(file_new_path)
        try:
            os.symlink(file_path, file_new_path)
            json_data["file_path"] = file_new_path
            LogBuffer.log().write(
                f"\n 🍀 Softlink done! \n    Softlink file: {file_new_path} \n    Source file: {file_path}"
            )
            return True
        except Exception as e:
            if IS_WINDOWS:
                LogBuffer.log().write(
                    "\n 🥺 Softlink failed! (创建软连接失败！"
                    "注意：Windows 平台输出目录必须是本地磁盘！不支持挂载的 NAS 盘或网盘！"
                    f"如果是本地磁盘，请尝试以管理员身份运行！)\n{str(e)}\n 🙉 [Movie] {temp_path}"
                )
            else:
                LogBuffer.log().write(f"\n 🥺 Softlink failed! (创建软连接失败！)\n{str(e)}\n 🙉 [Movie] {temp_path}")
            signal.show_traceback_log(traceback.format_exc())
            signal.show_log_text(traceback.format_exc())
            return False

    # 硬链接模式开时，创建硬链接
    elif config.soft_link == 2:
        try:
            delete_file(file_new_path)
            os.link(file_path, file_new_path)
            json_data["file_path"] = file_new_path
            LogBuffer.log().write(
                f"\n 🍀 HardLink done! \n    HadrLink file: {file_new_path} \n    Source file: {file_path}"
            )
            return True
        except Exception as e:
            if IS_MAC:
                LogBuffer.log().write(
                    "\n 🥺 HardLink failed! (创建硬连接失败！"
                    "注意：硬链接要求待刮削文件和输出目录必须是同盘，不支持跨卷！"
                    "如要跨卷可以尝试软链接模式！另外，Mac 平台非本地磁盘不支持创建硬链接（权限问题），"
                    f"请选择软链接模式！)\n{str(e)} "
                )
            else:
                LogBuffer.log().write(
                    f"\n 🥺 HardLink failed! (创建硬连接失败！注意："
                    f"硬链接要求待刮削文件和输出目录必须是同盘，不支持跨卷！"
                    f"如要跨卷可以尝试软链接模式！)\n{str(e)} "
                )
            LogBuffer.error().write("创建硬连接失败！")
            signal.show_traceback_log(traceback.format_exc())
            signal.show_log_text(traceback.format_exc())
            return False

    # 其他情况，就移动文件
    result, error_info = move_file(file_path, file_new_path)
    if result:
        LogBuffer.log().write(f"\n 🍀 Movie done! \n 🙉 [Movie] {file_new_path}")
        if os.path.islink(file_new_path):
            LogBuffer.log().write(
                f"\n    It's a symlink file! Source file: \n    {read_link(file_new_path)}"  # win 不能用os.path.realpath()，返回的结果不准
            )
        json_data["file_path"] = file_new_path
        return True
    else:
        if "are the same file" in error_info.lower():  # 大小写不同，win10 用raidrive 挂载 google drive 改名会出错
            if json_data["cd_part"]:
                temp_folder, temp_file = split_path(file_new_path)
                if temp_file not in os.listdir(temp_folder):
                    move_file(file_path, file_new_path + ".MDCx.tmp")
                    move_file(file_new_path + ".MDCx.tmp", file_new_path)
            LogBuffer.log().write(f"\n 🍀 Movie done! \n 🙉 [Movie] {file_new_path}")
            json_data["file_path"] = file_new_path
            return True
        LogBuffer.log().write(f"\n 🔴 Failed to move movie file to success folder!\n    {error_info}")
        return False


def _get_folder_path(file_path: str, success_folder: str, json_data: JsonData) -> str:
    folder_name: str = config.folder_name.replace("\\", "/")  # 设置-命名-视频目录名
    folder_path, file_name = split_path(file_path)  # 当前文件的目录和文件名

    # 更新模式 或 读取模式
    if config.main_mode == 3 or config.main_mode == 4:
        if config.update_mode == "c":
            folder_name = split_path(folder_path)[1]
            json_data["folder_name"] = folder_name
            return folder_path
        elif "bc" in config.update_mode:
            folder_name = config.update_b_folder
            success_folder = split_path(folder_path)[0]
            if "a" in config.update_mode:
                success_folder = split_path(success_folder)[0]
                folder_name = os.path.join(config.update_a_folder, config.update_b_folder).replace("\\", "/").strip("/")
        elif config.update_mode == "d":
            folder_name = config.update_d_folder
            success_folder = split_path(file_path)[0]

    # 正常模式 或 整理模式
    else:
        # 关闭软连接，并且成功后移动文件关时，使用原来文件夹
        if config.soft_link == 0 and not config.success_file_move:
            folder_path = split_path(file_path)[0]
            json_data["folder_name"] = folder_name
            return folder_path

    # 当根据刮削模式得到的视频目录名为空时，使用成功输出目录
    if not folder_name:
        json_data["folder_name"] = ""
        return success_folder

    show_4k = "folder" in config.show_4k
    show_cnword = config.folder_cnword
    show_moword = "folder" in config.show_moword
    should_escape_result = True
    folder_new_name, folder_name, number, originaltitle, outline, title = render_name_template(folder_name, file_path, json_data, show_4k, show_cnword, show_moword, should_escape_result)

    # 去除各种乱七八糟字符后，文件夹名为空时，使用number显示
    folder_name_temp = re.sub(r'[\\/:*?"<>|\r\n]+', "", folder_new_name)
    folder_name_temp = folder_name_temp.replace("//", "/").replace("--", "-").strip("-")
    if not folder_name_temp:
        folder_new_name = number

    # 判断文件夹名长度，超出长度时，截短标题名
    folder_name_max = int(config.folder_name_max)
    if len(folder_new_name) > folder_name_max:
        cut_index = folder_name_max - len(folder_new_name)
        if "originaltitle" in folder_name:
            LogBuffer.log().write(
                f"\n 💡 当前目录名长度：{len(folder_new_name)}，最大允许长度：{folder_name_max}，目录命名时将去除原标题后{abs(cut_index)}个字符!"
            )
            folder_new_name = folder_new_name.replace(originaltitle, originaltitle[0:cut_index])
        elif "title" in folder_name:
            LogBuffer.log().write(
                f"\n 💡 当前目录名长度：{len(folder_new_name)}，最大允许长度：{folder_name_max}，目录命名时将去除标题后{abs(cut_index)}个字符!"
            )
            folder_new_name = folder_new_name.replace(title, title[0:cut_index])
        elif "outline" in folder_name:
            LogBuffer.log().write(
                f"\n 💡 当前目录名长度：{len(folder_new_name)}，最大允许长度：{folder_name_max}，目录命名时将去除简介后{abs(cut_index)}个字符!"
            )
            folder_new_name = folder_new_name.replace(outline, outline[0:cut_index])

    # 替换一些字符
    folder_new_name = folder_new_name.replace("--", "-").strip("-").strip("- .")

    # 用在保存文件时的名字，需要过滤window异常字符 特殊字符
    folder_new_name = re.sub(r'[\\:*?"<>|\r\n]+', "", folder_new_name).strip(" /")

    # 过滤文件夹名字前后的空格
    folder_new_name = folder_new_name.replace(" /", "/").replace(" \\", "\\").replace("/ ", "/").replace("\\ ", "\\")

    # 日文浊音转换（mac的坑,osx10.12以下使用nfd）
    folder_new_name = nfd2c(folder_new_name)

    # 生成文件夹名
    folder_new_path = os.path.join(success_folder, folder_new_name)
    folder_new_path = convert_path(folder_new_path)
    folder_new_path = nfd2c(folder_new_path)

    json_data["folder_name"] = folder_new_name

    return folder_new_path.strip().replace(" /", "/")


def _generate_file_name(file_path: str, json_data: JsonData) -> str:
    file_full_name = split_path(file_path)[1]
    file_name, file_ex = os.path.splitext(file_full_name)

    # 如果成功后不重命名，则返回原来名字
    if not config.success_file_rename:
        return file_name

    # 获取文件信息
    cd_part = json_data["cd_part"]

    show_4k = "file" in config.show_4k
    show_cnword = config.file_cnword
    show_moword = "file" in config.show_moword
    should_escape_result = True
    file_name, naming_file, number, originaltitle, outline, title = render_name_template(config.naming_file, file_path, json_data, show_4k, show_cnword, show_moword, should_escape_result)

    file_name += cd_part

    # 去除各种乱七八糟字符后，文件名为空时，使用number显示
    file_name_temp = re.sub(r'[\\/:*?"<>|\r\n]+', "", file_name)
    file_name_temp = file_name_temp.replace("//", "/").replace("--", "-").strip("-")
    if not file_name_temp:
        file_name = number

    # 插入防屏蔽字符（115）
    prevent_char = config.prevent_char
    if prevent_char:
        file_char_list = list(file_name)
        file_name = prevent_char.join(file_char_list)

    # 判断文件名长度，超出长度时，截短文件名
    file_name_max = int(config.file_name_max)
    if len(file_name) > file_name_max:
        cut_index = file_name_max - len(file_name) - len(file_ex)

        # 如果没有防屏蔽字符，截短标题或者简介，这样不影响其他字段阅读
        if not prevent_char:
            if "originaltitle" in naming_file:
                LogBuffer.log().write(
                    f"\n 💡 当前文件名长度：{len(file_name)}，"
                    f"最大允许长度：{file_name_max}，文件命名时将去除原标题后{abs(cut_index)}个字符!"
                )
                file_name = file_name.replace(originaltitle, originaltitle[:cut_index])
            elif "title" in naming_file:
                LogBuffer.log().write(
                    f"\n 💡 当前文件名长度：{len(file_name)}，"
                    f"最大允许长度：{file_name_max}，文件命名时将去除标题后{abs(cut_index)}个字符!"
                )
                file_name = file_name.replace(title, title[:cut_index])
            elif "outline" in naming_file:
                LogBuffer.log().write(
                    f"\n 💡 当前文件名长度：{len(file_name)}，"
                    f"最大允许长度：{file_name_max}，文件命名时将去除简介后{abs(cut_index)}个字符!"
                )
                file_name = file_name.replace(outline, outline[:cut_index])

        # 加了防屏蔽字符，直接截短
        else:
            file_name = file_name[:cut_index]

    # 替换一些字符
    file_name = file_name.replace("//", "/").replace("--", "-").strip("-")

    # 用在保存文件时的名字，需要过滤window异常字符 特殊字符
    file_name = re.sub(r'[\\/:*?"<>|\r\n]+', "", file_name).strip()

    # 过滤文件名字前后的空格
    file_name = file_name.replace(" /", "/").replace(" \\", "\\").replace("/ ", "/").replace("\\ ", "\\").strip()

    # 日文浊音转换（mac的坑,osx10.12以下使用nfd）
    file_name = nfd2c(file_name)

    return file_name


def get_output_name(
    json_data: JsonData, file_path: str, success_folder: str, file_ex: str
) -> tuple[str, str, str, str, str, str, str, str, str, str]:
    # =====================================================================================更新输出文件夹名
    folder_new_path = _get_folder_path(file_path, success_folder, json_data)
    folder_new_path = _deal_path_name(folder_new_path)
    # =====================================================================================更新实体文件命名规则
    naming_rule = _generate_file_name(file_path, json_data)
    naming_rule = _deal_path_name(naming_rule)
    # =====================================================================================生成文件和nfo新路径
    file_new_name = naming_rule + file_ex.lower()
    nfo_new_name = naming_rule + ".nfo"
    file_new_path = convert_path(os.path.join(folder_new_path, file_new_name))
    nfo_new_path = convert_path(os.path.join(folder_new_path, nfo_new_name))
    # =====================================================================================生成图片下载路径
    poster_new_name = naming_rule + "-poster.jpg"
    thumb_new_name = naming_rule + "-thumb.jpg"
    fanart_new_name = naming_rule + "-fanart.jpg"
    poster_new_path_with_filename = convert_path(os.path.join(folder_new_path, poster_new_name))
    thumb_new_path_with_filename = convert_path(os.path.join(folder_new_path, thumb_new_name))
    fanart_new_path_with_filename = convert_path(os.path.join(folder_new_path, fanart_new_name))
    # =====================================================================================生成图片最终路径
    # 如果图片命名规则不加文件名并且视频目录不为空
    if config.pic_simple_name and json_data["folder_name"].replace(" ", ""):
        poster_final_name = "poster.jpg"
        thumb_final_name = "thumb.jpg"
        fanart_final_name = "fanart.jpg"
    else:
        poster_final_name = naming_rule + "-poster.jpg"
        thumb_final_name = naming_rule + "-thumb.jpg"
        fanart_final_name = naming_rule + "-fanart.jpg"
    poster_final_path = convert_path(os.path.join(folder_new_path, poster_final_name))
    thumb_final_path = convert_path(os.path.join(folder_new_path, thumb_final_name))
    fanart_final_path = convert_path(os.path.join(folder_new_path, fanart_final_name))

    return (
        folder_new_path,
        file_new_path,
        nfo_new_path,
        poster_new_path_with_filename,
        thumb_new_path_with_filename,
        fanart_new_path_with_filename,
        naming_rule,
        poster_final_path,
        thumb_final_path,
        fanart_final_path,
    )


def newtdisk_creat_symlink(copy_flag: bool, netdisk_path: str = "", local_path: str = "") -> None:
    from_tool = False
    if not netdisk_path:
        from_tool = True
        signal.change_buttons_status.emit()
    start_time = time.time()
    if not netdisk_path:
        netdisk_path = convert_path(config.netdisk_path)
    if not local_path:
        local_path = convert_path(config.localdisk_path)
    signal.show_log_text("🍯 🍯 🍯 NOTE: Begining creat symlink!!!")
    signal.show_log_text("\n ⏰ Start time: " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    signal.show_log_text(f" 📁 Source path: {netdisk_path} \n 📁 Softlink path: {local_path} \n")
    try:
        if netdisk_path and local_path:
            copy_exts = [".nfo", ".jpg", ".png"] + config.sub_type.split("|")
            file_exts = config.media_type.lower().split("|") + copy_exts + config.sub_type.split("|")
            total = 0
            copy_num = 0
            link_num = 0
            fail_num = 0
            skip_num = 0
            done = set()
            for root, _, files in os.walk(netdisk_path, topdown=True):
                if convert_path(root) == convert_path(local_path):
                    continue

                local_dir = convert_path(os.path.join(local_path, root.replace(netdisk_path, "", 1).strip("/\\")))
                local_dir = (
                    re.sub(r"\s", " ", local_dir).replace(" \\", "\\").replace("\\ ", "\\").strip().replace("■", "")
                )
                if not os.path.isdir(local_dir):
                    os.makedirs(local_dir)
                for f in files:
                    # 跳过隐藏文件、预告片、主题视频
                    if f.startswith("."):
                        continue
                    if "trailer." in f or "trailers." in f:
                        continue
                    if "theme_video." in f:
                        continue
                    # 跳过未知扩展名
                    ext = os.path.splitext(f)[1].lower()
                    if ext not in file_exts:
                        continue

                    total += 1
                    net_file = convert_path(os.path.join(root, f))
                    local_file = convert_path(os.path.join(local_dir, f.strip()))
                    local_file = re.sub(r"\s", " ", local_file).strip().replace("■", "")

                    if os.path.exists(local_file):
                        signal.show_log_text(f" {total} 🟠 Skip: a file or valid symlink already exists\n {net_file} ")
                        skip_num += 1
                        continue
                    if os.path.islink(local_file):  # invalid symlink
                        os.remove(local_file)

                    if ext in copy_exts:  # 直接复制的文件
                        if not copy_flag:
                            continue
                        copy_file(net_file, local_file)
                        signal.show_log_text(f" {total} 🍀 Copy done!\n {net_file} ")
                        copy_num += 1
                    else:
                        # 不对原文件进行有效性检查以减小可能的网络 IO 开销
                        if net_file in done:
                            signal.show_log_text(
                                f" {total} 🟠 Link skip! Source file already linked, this file is duplicate!\n {net_file} "
                            )
                            skip_num += 1
                            continue
                        done.add(net_file)

                        try:
                            os.symlink(net_file, local_file)
                            signal.show_log_text(f" {total} 🍀 Link done!\n {net_file} ")
                            link_num += 1
                        except Exception as e:
                            print(traceback.format_exc())
                            error_info = ""
                            if "symbolic link privilege not held" in str(e):
                                error_info = "   \n没有创建权限，请尝试管理员权限！或按照教程开启用户权限： https://www.jianshu.com/p/0e307bfe8770"
                            signal.show_log_text(f" {total} 🔴 Link failed!{error_info} \n {net_file} ")
                            signal.show_log_text(traceback.format_exc())
                            fail_num += 1

            signal.show_log_text(
                f"\n 🎉🎉🎉 All finished!!!({get_used_time(start_time)}s) Total {total} , "
                f"Linked {link_num} , Copied {copy_num} , Skiped {skip_num} , Failed {fail_num} "
            )
        else:
            signal.show_log_text(f" 🔴 网盘目录和本地目录不能为空！请重新设置！({get_used_time(start_time)}s)")
    except Exception:
        print(traceback.format_exc())
        signal.show_log_text(traceback.format_exc())

    signal.show_log_text("================================================================================")
    if from_tool:
        signal.reset_buttons_status.emit()


def movie_lists(escape_folder_list: list[str], movie_type: str, movie_path: str) -> list[str]:
    start_time = time.time()
    total = []
    file_type = movie_type.split("|")
    skip_list = ["skip", ".skip", ".ignore"]
    not_skip_success = bool("skip_success_file" not in config.no_escape)
    i = 100
    skip = 0
    skip_repeat_softlink = 0
    signal.show_traceback_log("🔎 遍历待刮削目录....")
    for root, dirs, files in os.walk(movie_path):
        # 文件夹是否在排除目录
        root = os.path.join(root, "").replace("\\", "/")
        if "behind the scenes" in root or root in escape_folder_list:
            dirs[:] = []  # 忽略当前文件夹子目录
            continue

        # 文件夹是否存在跳过文件
        for skip_key in skip_list:
            if skip_key in files:
                dirs[:] = []
                break
        else:
            # 处理文件列表
            for f in files:
                file_name, file_type_current = os.path.splitext(f)

                # 跳过隐藏文件、预告片、主题视频
                if re.search(r"^\..+", file_name):
                    continue
                if "trailer." in f or "trailers." in f:
                    continue
                if "theme_video." in f:
                    continue

                # 判断清理文件
                path = os.path.join(root, f)
                if _need_clean(path, f, file_type_current):
                    result, error_info = delete_file(path)
                    if result:
                        signal.show_log_text(f" 🗑 Clean: {path} ")
                    else:
                        signal.show_log_text(f" 🗑 Clean error: {error_info} ")
                    continue

                # 添加文件
                temp_total = []
                if file_type_current.lower() in file_type:
                    if os.path.islink(path):
                        real_path = read_link(path)
                        # 清理失效的软链接文件
                        if "check_symlink" in config.no_escape and not os.path.exists(real_path):
                            result, error_info = delete_file(path)
                            if result:
                                signal.show_log_text(f" 🗑 Clean dead link: {path} ")
                            else:
                                signal.show_log_text(f" 🗑 Clean dead link error: {error_info} ")
                            continue
                        if real_path in temp_total:
                            skip_repeat_softlink += 1
                            delete_file(path)
                            continue
                        else:
                            temp_total.append(real_path)

                    if path in temp_total:
                        skip_repeat_softlink += 1
                        continue
                    else:
                        temp_total.append(path)
                    # mac 转换成 NFC，因为mac平台nfc和nfd指向同一个文件，windows平台指向不同文件
                    if not IS_WINDOWS:
                        path = nfd2c(path)
                    new_path = convert_path(path)
                    if not_skip_success or new_path not in Flags.success_list:
                        total.append(new_path)
                    else:
                        skip += 1

        found_count = len(total)
        if found_count >= i:
            i = found_count + 100
            signal.show_traceback_log(
                f"✅ Found ({found_count})! "
                f"Skip successfully scraped ({skip}) repeat softlink ({skip_repeat_softlink})! "
                f"({get_used_time(start_time)}s)... Still searching, please wait... \u3000"
            )
            signal.show_log_text(
                f"    {get_current_time()} Found ({found_count})! "
                f"Skip successfully scraped ({skip}) repeat softlink ({skip_repeat_softlink})! "
                f"({get_used_time(start_time)}s)... Still searching, please wait... \u3000"
            )

    total.sort()
    signal.show_traceback_log(
        f"🎉 Done!!! Found ({len(total)})! "
        f"Skip successfully scraped ({skip}) repeat softlink ({skip_repeat_softlink})! "
        f"({get_used_time(start_time)}s) \u3000"
    )
    signal.show_log_text(
        f"    Done!!! Found ({len(total)})! "
        f"Skip successfully scraped ({skip}) repeat softlink ({skip_repeat_softlink})! "
        f"({get_used_time(start_time)}s) \u3000"
    )
    return total


def get_file_info(file_path: str, copy_sub: bool = True) -> tuple[JsonData, str, str, str, str, list[str], str, str]:
    json_data = new_json_data()
    json_data["version"] = config.version
    movie_number = ""
    has_sub = False
    c_word = ""
    cd_part = ""
    destroyed = ""
    leak = ""
    wuma = ""
    youma = ""
    mosaic = ""
    sub_list = []
    cnword_style = config.cnword_style
    if Flags.file_mode == FileMode.Again and file_path in Flags.new_again_dic:
        temp_number, temp_url, temp_website = Flags.new_again_dic[file_path]
        if temp_number:  # 如果指定了番号，则使用指定番号
            movie_number = temp_number
            json_data["appoint_number"] = temp_number
        if temp_url:
            json_data["appoint_url"] = temp_url
            json_data["website_name"] = temp_website
    elif Flags.file_mode == FileMode.Single:  # 刮削单文件（工具页面）
        json_data["appoint_url"] = Flags.appoint_url

    # 获取显示路径
    file_path = file_path.replace("\\", "/")
    file_show_path = showFilePath(file_path)

    # 获取文件名
    folder_path, file_full_name = split_path(file_path)  # 获取去掉文件名的路径、完整文件名（含扩展名）
    file_name, file_ex = os.path.splitext(file_full_name)  # 获取文件名（不含扩展名）、扩展名(含有.)
    file_name_temp = file_name + "."
    nfo_old_name = file_name + ".nfo"
    nfo_old_path = os.path.join(folder_path, nfo_old_name)
    file_show_name = file_name

    # 软链接时，获取原身路径(用来查询原身文件目录是否有字幕)
    file_ori_path_no_ex = ""
    if os.path.islink(file_path):
        file_ori_path = read_link(file_path)
        file_ori_path_no_ex = os.path.splitext(file_ori_path)[0]

    try:
        # 清除防屏蔽字符
        prevent_char = config.prevent_char
        if prevent_char:
            file_path = file_path.replace(prevent_char, "")
            file_name = file_name.replace(prevent_char, "")

        # 获取番号
        if not movie_number:
            movie_number = get_file_number(file_path)

        # 259LUXU-1111, 非mgstage、avsex去除前面的数字前缀
        temp_n = re.findall(r"\d{3,}([a-zA-Z]+-\d+)", movie_number)
        json_data["short_number"] = temp_n[0] if temp_n else ""

        # 去掉各种乱七八糟的字符
        file_name_cd = remove_escape_string(file_name, "-").replace(movie_number, "-").replace("--", "-").strip()

        # 替换分隔符为-
        cd_char = config.cd_char
        if "underline" in cd_char:
            file_name_cd = file_name_cd.replace("_", "-")
        if "space" in cd_char:
            file_name_cd = file_name_cd.replace(" ", "-")
        if "point" in cd_char:
            file_name_cd = file_name_cd.replace(".", "-")
        file_name_cd = file_name_cd.lower() + "."  # .作为结尾

        # 获取分集(排除‘番号-C’和‘番号C’作为字幕标识的情况)
        # if '-C' in config.cnword_char:
        #     file_name_cd = file_name_cd.replace('-c.', '.')
        # else:
        #     file_name_cd = file_name_cd.replace('-c.', '-cd3.')
        # if 'C.' in config.cnword_char and file_name_cd.endswith('c.'):
        #     file_name_cd = file_name_cd[:-2] + '.'

        temp_cd = re.compile(r"(vol|case|no|cwp|cwpbd|act)[-\.]?\d+")
        temp_cd_filename = re.sub(temp_cd, "", file_name_cd)
        cd_path_1 = re.findall(r"[-_ .]{1}(cd|part|hd)([0-9]{1,2})", temp_cd_filename)
        cd_path_2 = re.findall(r"-([0-9]{1,2})\.?$", temp_cd_filename)
        cd_path_3 = re.findall(r"(-|\d{2,}|\.)([a-o]{1})\.?$", temp_cd_filename)
        cd_path_4 = re.findall(r"-([0-9]{1})[^a-z0-9]", temp_cd_filename)
        if cd_path_1 and int(cd_path_1[0][1]) > 0:
            cd_part = cd_path_1[0][1]
        elif cd_path_2:
            if len(cd_path_2[0]) == 1 or "digital" in cd_char:
                cd_part = str(int(cd_path_2[0]))
        elif cd_path_3 and "letter" in cd_char:
            letter_list = [
                "",
                "a",
                "b",
                "c",
                "d",
                "e",
                "f",
                "g",
                "h",
                "i",
                "j",
                "k",
                "l",
                "m",
                "n",
                "o",
                "p",
                "q",
                "r",
                "s",
                "t",
                "u",
                "v",
                "w",
                "x",
                "y",
                "z",
            ]
            if cd_path_3[0][1] != "c" or "endc" in cd_char:
                cd_part = str(letter_list.index(cd_path_3[0][1]))
        elif cd_path_4 and "middle_number" in cd_char:
            cd_part = str(int(cd_path_4[0]))

        # 判断分集命名规则
        if cd_part:
            cd_name = config.cd_name
            if int(cd_part) == 0:
                cd_part = ""
            elif cd_name == 0:
                cd_part = "-cd" + str(cd_part)
            elif cd_name == 1:
                cd_part = "-CD" + str(cd_part)
            else:
                cd_part = "-" + str(cd_part)

        # 判断是否是马赛克破坏版
        umr_style = str(config.umr_style)
        if (
            "-uncensored." in file_path.lower()
            or "umr." in file_path.lower()
            or "破解" in file_path
            or "克破" in file_path
            or (umr_style and umr_style in file_path)
            or "-u." in file_path.lower()
            or "-uc." in file_path.lower()
        ):
            destroyed = umr_style
            mosaic = "无码破解"

        # 判断是否国产
        if not mosaic:
            if "国产" in file_path or "麻豆" in file_path or "國產" in file_path:
                mosaic = "国产"
            else:
                md_list = [
                    "国产",
                    "國產",
                    "麻豆",
                    "传媒",
                    "傳媒",
                    "皇家华人",
                    "皇家華人",
                    "精东",
                    "精東",
                    "猫爪影像",
                    "貓爪影像",
                    "91CM",
                    "91MS",
                    "导演系列",
                    "導演系列",
                    "MDWP",
                    "MMZ",
                    "MLT",
                    "MSM",
                    "LAA",
                    "MXJ",
                    "SWAG",
                ]
                for each in md_list:
                    if each in file_path:
                        mosaic = "国产"

        # 判断是否流出
        leak_style = str(config.leak_style)
        if not mosaic:
            if "流出" in file_path or "leaked" in file_path.lower() or (leak_style and leak_style in file_path):
                leak = leak_style
                mosaic = "无码流出"

        # 判断是否无码
        wuma_style = str(config.wuma_style)
        if not mosaic:
            if (
                "无码" in file_path
                or "無碼" in file_path
                or "無修正" in file_path
                or "uncensored" in file_path.lower()
                or is_uncensored(movie_number)
            ):
                wuma = wuma_style
                mosaic = "无码"

        # 判断是否有码
        youma_style = str(config.youma_style)
        if not mosaic:
            if "有码" in file_path or "有碼" in file_path:
                youma = youma_style
                mosaic = "有码"

        # 查找本地字幕文件
        cnword_list = config.cnword_char.replace("，", ",").split(",")
        if "-C." in str(cnword_list).upper():
            cnword_list.append("-C ")
        sub_type_list = config.sub_type.split("|")  # 本地字幕后缀
        for sub_type in sub_type_list:  # 查找本地字幕, 可能多个
            sub_type_chs = ".chs" + sub_type
            sub_path_chs = os.path.join(folder_path, (file_name + sub_type_chs))
            sub_path = os.path.join(folder_path, (file_name + sub_type))
            if os.path.exists(sub_path_chs):
                sub_list.append(sub_type_chs)
                c_word = cnword_style  # 中文字幕影片后缀
                has_sub = True
            if os.path.exists(sub_path):
                sub_list.append(sub_type)
                c_word = cnword_style  # 中文字幕影片后缀
                has_sub = True
            if file_ori_path_no_ex:  # 原身路径
                sub_path2 = file_ori_path_no_ex + sub_type
                if os.path.exists(sub_path2):
                    c_word = cnword_style  # 中文字幕影片后缀
                    has_sub = True

        # 判断路径名是否有中文字幕字符
        if not has_sub:
            cnword_list.append("-uc.")
            file_name_temp = file_name_temp.upper().replace("CD", "").replace("CARIB", "")  # 去掉cd/carib，避免-c误判
            if "letter" in cd_char and "endc" in cd_char:
                file_name_temp = re.sub(r"(-|\d{2,}|\.)C\.$", ".", file_name_temp)

            for each in cnword_list:
                if each.upper() in file_name_temp:
                    if "無字幕" not in file_path and "无字幕" not in file_path:
                        c_word = cnword_style  # 中文字幕影片后缀
                        has_sub = True
                        break

        # 判断nfo中是否有中文字幕、马赛克
        if (not has_sub or not mosaic) and os.path.exists(nfo_old_path):
            try:
                with open(nfo_old_path, encoding="utf-8") as f:
                    nfo_content = f.read()
                if not has_sub:
                    if ">中文字幕</" in nfo_content:
                        c_word = cnword_style  # 中文字幕影片后缀
                        has_sub = True
                if not mosaic:
                    if ">无码流出</" in nfo_content or ">無碼流出</" in nfo_content:
                        leak = leak_style
                        mosaic = "无码流出"
                    elif ">无码破解</" in nfo_content or ">無碼破解</" in nfo_content:
                        destroyed = umr_style
                        mosaic = "无码破解"
                    elif ">无码</" in nfo_content or ">無碼</" in nfo_content:
                        wuma = wuma_style
                        mosaic = "无码"
                    elif ">有碼</" in nfo_content or ">有碼</" in nfo_content:
                        youma = youma_style
                        mosaic = "有码"
                    elif ">国产</" in nfo_content or ">國產</" in nfo_content:
                        youma = youma_style
                        mosaic = "国产"
                    elif ">里番</" in nfo_content or ">裏番</" in nfo_content:
                        youma = youma_style
                        mosaic = "里番"
                    elif ">动漫</" in nfo_content or ">動漫</" in nfo_content:
                        youma = youma_style
                        mosaic = "动漫"
            except Exception:
                signal.show_traceback_log(traceback.format_exc())

        if not has_sub and os.path.exists(nfo_old_path):
            try:
                with open(nfo_old_path, encoding="utf-8") as f:
                    nfo_content = f.read()
                if "<genre>中文字幕</genre>" in nfo_content or "<tag>中文字幕</tag>" in nfo_content:
                    c_word = cnword_style  # 中文字幕影片后缀
                    has_sub = True
            except Exception:
                signal.show_traceback_log(traceback.format_exc())

        # 查找字幕包目录字幕文件
        subtitle_add = config.subtitle_add
        if not has_sub and copy_sub and subtitle_add:
            subtitle_folder = config.subtitle_folder
            subtitle_add = config.subtitle_add
            if subtitle_add and subtitle_folder:  # 复制字幕开
                for sub_type in sub_type_list:
                    sub_path_1 = os.path.join(subtitle_folder, (movie_number + cd_part + sub_type))
                    sub_path_2 = os.path.join(subtitle_folder, file_name + sub_type)
                    sub_path_list = [sub_path_1, sub_path_2]
                    sub_file_name = file_name + sub_type
                    if config.subtitle_add_chs:
                        sub_file_name = file_name + ".chs" + sub_type
                        sub_type = ".chs" + sub_type
                    sub_new_path = os.path.join(folder_path, sub_file_name)
                    for sub_path in sub_path_list:
                        if os.path.exists(sub_path):
                            copy_file(sub_path, sub_new_path)
                            LogBuffer.log().write(f"\n\n 🍉 Sub file '{sub_file_name}' copied successfully! ")
                            sub_list.append(sub_type)
                            c_word = cnword_style  # 中文字幕影片后缀
                            has_sub = True
                            break

        file_show_name = movie_number
        suffix_sort_list = config.suffix_sort.split(",")
        for each in suffix_sort_list:
            if each == "moword":
                file_show_name += destroyed + leak + wuma + youma
            elif each == "cnword":
                file_show_name += c_word
        file_show_name += cd_part

    except Exception:
        signal.show_traceback_log(file_path)
        signal.show_traceback_log(traceback.format_exc())
        signal.show_log_text(traceback.format_exc())
        LogBuffer.log().write("\n" + file_path)
        LogBuffer.log().write("\n" + traceback.format_exc())

    # 车牌前缀
    letters = get_number_letters(movie_number)

    json_data["number"] = movie_number
    json_data["letters"] = letters
    json_data["has_sub"] = has_sub
    json_data["c_word"] = c_word
    json_data["cd_part"] = cd_part
    json_data["destroyed"] = destroyed
    json_data["leak"] = leak
    json_data["wuma"] = wuma
    json_data["youma"] = youma
    json_data["mosaic"] = mosaic
    json_data["_4K"] = ""
    json_data["tag"] = ""
    json_data["actor_href"] = ""
    json_data["all_actor"] = ""
    json_data["definition"] = ""
    json_data["file_path"] = convert_path(file_path)

    return json_data, movie_number, folder_path, file_name, file_ex, sub_list, file_show_name, file_show_path


def get_movie_list(file_mode: FileMode, movie_path: str, escape_folder_list: list[str]) -> list[str]:
    movie_list = []
    if file_mode == FileMode.Default:  # 刮削默认视频目录的文件
        movie_path = convert_path(movie_path)
        if not os.path.exists(movie_path):
            signal.show_log_text("\n 🔴 Movie folder does not exist!")
        else:
            signal.show_log_text(" 🖥 Movie path: " + movie_path)
            signal.show_log_text(" 🔎 Searching all videos, Please wait...")
            signal.set_label_file_path.emit(f"正在遍历待刮削视频目录中的所有视频，请等待...\n {movie_path}")
            if "folder" in config.no_escape:
                escape_folder_list = []
            elif config.main_mode == 3 or config.main_mode == 4:
                escape_folder_list = []
            try:
                movie_list = movie_lists(
                    escape_folder_list, config.media_type, movie_path
                )  # 获取所有需要刮削的影片列表
            except Exception:
                signal.show_traceback_log(traceback.format_exc())
                signal.show_log_text(traceback.format_exc())
            count_all = len(movie_list)
            signal.show_log_text(" 📺 Find " + str(count_all) + " movies")

    elif file_mode == FileMode.Single:  # 刮削单文件（工具页面）
        file_path = Flags.single_file_path.strip()
        if not os.path.exists(file_path):
            signal.show_log_text(" 🔴 Movie file does not exist!")
        else:
            movie_list.append(file_path)  # 把文件路径添加到movie_list
            signal.show_log_text(" 🖥 File path: " + file_path)
            if Flags.appoint_url:
                signal.show_log_text(" 🌐 File url: " + Flags.appoint_url)

    return movie_list


def _clean_empty_fodlers(path: str, file_mode: FileMode) -> None:
    start_time = time.time()
    if not config.del_empty_folder or file_mode == FileMode.Again:
        return
    signal.set_label_file_path.emit("🗑 正在清理空文件夹，请等待...")
    signal.show_log_text(" ⏳ Cleaning empty folders...")
    if "folder" in config.no_escape:
        escape_folder_list = ""
    else:
        escape_folder_list = get_movie_path_setting()[3]
    if os.path.exists(path):
        all_info = os.walk(path, topdown=True)
        all_folder_list = []
        for root, dirs, files in all_info:
            if os.path.exists(os.path.join(root, "skip")):  # 是否有skip文件
                dirs[:] = []  # 忽略当前文件夹子目录
                continue
            root = os.path.join(root, "").replace("\\", "/")  # 是否在排除目录
            if root in escape_folder_list:
                dirs[:] = []  # 忽略当前文件夹子目录
                continue
            dirs_list = [os.path.join(root, dir) for dir in dirs]
            all_folder_list.extend(dirs_list)
        all_folder_list.sort(reverse=True)
        for folder in all_folder_list:
            hidden_file_mac = os.path.join(folder, ".DS_Store")
            hidden_file_windows = os.path.join(folder, "Thumbs.db")
            if os.path.exists(hidden_file_mac):
                delete_file(hidden_file_mac)  # 删除隐藏文件
            if os.path.exists(hidden_file_windows):
                delete_file(hidden_file_windows)  # 删除隐藏文件
            try:
                if not os.listdir(folder):
                    os.rmdir(folder)
                    signal.show_log_text(f" 🗑 Clean empty folder: {convert_path(folder)}")
            except Exception as e:
                signal.show_traceback_log(traceback.format_exc())
                signal.show_log_text(f" 🔴 Delete empty folder error: {str(e)}")

    signal.show_log_text(f" 🍀 Clean done!({get_used_time(start_time)}s)")
    signal.show_log_text("=" * 80)


def get_success_list() -> None:
    Flags.success_save_time = time.time()
    if os.path.isfile(resources.userdata_path("success.txt")):
        with open(resources.userdata_path("success.txt"), encoding="utf-8", errors="ignore") as f:
            temp = f.read()
            Flags.success_list = set(temp.split("\n")) if temp.strip() else set()
            if "" in Flags.success_list:
                Flags.success_list.remove("")
            save_success_list()
    signal.view_success_file_settext.emit(f"查看 ({len(Flags.success_list)})")


def deal_old_files(
    json_data: JsonData,
    folder_old_path: str,
    folder_new_path: str,
    file_path: str,
    file_new_path: str,
    thumb_new_path_with_filename: str,
    poster_new_path_with_filename: str,
    fanart_new_path_with_filename: str,
    nfo_new_path: str,
    file_ex: str,
    poster_final_path: str,
    thumb_final_path: str,
    fanart_final_path: str,
) -> tuple[bool, bool]:
    """
    处理本地已存在的thumb、poster、fanart、nfo
    """
    # 转换文件路径
    file_path = convert_path(file_path)
    nfo_old_path = file_path.replace(file_ex, ".nfo")
    nfo_new_path = convert_path(nfo_new_path)
    folder_old_path = convert_path(folder_old_path)
    folder_new_path = convert_path(folder_new_path)
    extrafanart_old_path = convert_path(os.path.join(folder_old_path, "extrafanart"))
    extrafanart_new_path = convert_path(os.path.join(folder_new_path, "extrafanart"))
    extrafanart_folder = config.extrafanart_folder
    extrafanart_copy_old_path = convert_path(os.path.join(folder_old_path, extrafanart_folder))
    extrafanart_copy_new_path = convert_path(os.path.join(folder_new_path, extrafanart_folder))
    trailer_name = config.trailer_simple_name
    trailer_old_folder_path = convert_path(os.path.join(folder_old_path, "trailers"))
    trailer_new_folder_path = convert_path(os.path.join(folder_new_path, "trailers"))
    trailer_old_file_path = convert_path(os.path.join(trailer_old_folder_path, "trailer.mp4"))
    trailer_new_file_path = convert_path(os.path.join(trailer_new_folder_path, "trailer.mp4"))
    trailer_old_file_path_with_filename = convert_path(nfo_old_path.replace(".nfo", "-trailer.mp4"))
    trailer_new_file_path_with_filename = convert_path(nfo_new_path.replace(".nfo", "-trailer.mp4"))
    theme_videos_old_path = convert_path(os.path.join(folder_old_path, "backdrops"))
    theme_videos_new_path = convert_path(os.path.join(folder_new_path, "backdrops"))
    extrafanart_extra_old_path = convert_path(os.path.join(folder_old_path, "behind the scenes"))
    extrafanart_extra_new_path = convert_path(os.path.join(folder_new_path, "behind the scenes"))

    # 图片旧路径转换路径
    poster_old_path_with_filename = file_path.replace(file_ex, "-poster.jpg")
    thumb_old_path_with_filename = file_path.replace(file_ex, "-thumb.jpg")
    fanart_old_path_with_filename = file_path.replace(file_ex, "-fanart.jpg")
    poster_old_path_no_filename = convert_path(os.path.join(folder_old_path, "poster.jpg"))
    thumb_old_path_no_filename = convert_path(os.path.join(folder_old_path, "thumb.jpg"))
    fanart_old_path_no_filename = convert_path(os.path.join(folder_old_path, "fanart.jpg"))
    file_path_list = {
        nfo_old_path,
        nfo_new_path,
        thumb_old_path_with_filename,
        thumb_old_path_no_filename,
        thumb_new_path_with_filename,
        thumb_final_path,
        poster_old_path_with_filename,
        poster_old_path_no_filename,
        poster_new_path_with_filename,
        poster_final_path,
        fanart_old_path_with_filename,
        fanart_old_path_no_filename,
        fanart_new_path_with_filename,
        fanart_final_path,
        trailer_old_file_path_with_filename,
        trailer_new_file_path_with_filename,
    }
    folder_path_list = {
        extrafanart_old_path,
        extrafanart_new_path,
        extrafanart_copy_old_path,
        extrafanart_copy_new_path,
        trailer_old_folder_path,
        trailer_new_folder_path,
        theme_videos_old_path,
        theme_videos_new_path,
        extrafanart_extra_old_path,
        extrafanart_extra_new_path,
    }

    # 视频模式进行清理
    main_mode = config.main_mode
    if main_mode == 2 and "sort_del" in config.switch_on:
        for each in file_path_list:
            if os.path.exists(each):
                delete_file(each)
        for each in folder_path_list:
            if os.path.isdir(each):
                shutil.rmtree(each, ignore_errors=True)
        return False, False

    # 非视频模式，将本地已有的图片、剧照等文件，按照命名规则，重新命名和移动。这个环节仅应用设置-命名设置，没有应用设置-下载的设置
    # 抢占图片的处理权
    single_folder_catched = False  # 剧照、剧照副本、主题视频 这些单文件夹的处理权，他们只需要处理一次
    pic_final_catched = False  # 最终图片（poster、thumb、fanart）的处理权
    with Flags.lock:
        if thumb_new_path_with_filename not in Flags.pic_catch_set:
            if thumb_final_path != thumb_new_path_with_filename:
                if thumb_final_path not in Flags.pic_catch_set:  # 不带文件名的图片的下载权利（下载权利只给它一个）
                    Flags.pic_catch_set.add(thumb_final_path)
                    pic_final_catched = True
            else:
                pic_final_catched = (
                    True  # 带文件名的图片，下载权利给每一个。（如果有一个下载好了，未下载的可以直接复制）
                )
        # 处理 extrafanart、extrafanart副本、主题视频、附加视频
        if pic_final_catched and extrafanart_new_path not in Flags.extrafanart_deal_set:
            Flags.extrafanart_deal_set.add(extrafanart_new_path)
            single_folder_catched = True
    """
    需要考虑旧文件分集情况（带文件名、不带文件名）、旧文件不同扩展名情况，他们如何清理或保留
    需要考虑新文件分集情况（带文件名、不带文件名）
    需要考虑分集同时刮削如何节省流量
    需要考虑分集带文件名图片是否会有重复水印问题
    """

    # poster_marked True 不加水印，避免二次加水印,；poster_exists 是不是存在本地图片
    json_data["poster_marked"] = True
    json_data["thumb_marked"] = True
    json_data["fanart_marked"] = True
    poster_exists = True
    thumb_exists = True
    fanart_exists = True
    trailer_exists = True

    # 软硬链接模式，不处理旧的图片
    if config.soft_link != 0:
        return pic_final_catched, single_folder_catched

    """
    保留图片或删除图片说明：
    图片保留的前提条件：非整理模式，并且满足（在保留名单 或 读取模式 或 图片已下载）。此时不清理 poster.jpg thumb.jpg fanart.jpg（在del_noname_pic中清理）。
    图片保留的命名方式：保留时会保留为最终路径 和 文件名-thumb.jpg (thumb 需要复制一份为 文件名-thumb.jpg，避免 poster 没有，要用 thumb 裁剪，或者 fanart 要复制 thumb)
    图片下载的命名方式：新下载的则都保存为 文件名-thumb.jpg（因为多分集同时下载为 thumb.jpg 时会冲突）
    图片下载的下载条件：如果最终路径有内容，则不下载。如果 文件名-thumb.jpg 有内容，也不下载。
    图片下载的复制条件：如果不存在 文件名-thumb.jpg，但是存在 thumb.jpg，则复制 thumb.jpg 为 文件名-thumb.jpg
    最终的图片处理：在最终的 rename pic 环节，如果最终路径有内容，则删除非最终路径的内容；如果最终路径没内容，表示图片是刚下载的，要改成最终路径。
    """

    # poster 处理：寻找对应文件放到最终路径上。这样避免刮削失败时，旧的图片被删除
    done_poster_path = Flags.file_done_dic.get(json_data["number"], {}).get("poster")
    done_poster_path_copy = True
    try:
        # 图片最终路径等于已下载路径时，图片是已下载的，不需要处理
        if (
            done_poster_path
            and os.path.exists(done_poster_path)
            and split_path(done_poster_path)[0] == split_path(poster_final_path)[0]
        ):  # 如果存在已下载完成的文件，尝试复制
            done_poster_path_copy = False  # 标记未复制！此处不复制，在poster download中复制
        elif os.path.exists(poster_final_path):
            pass  # windows、mac大小写不敏感，暂不解决
        elif poster_new_path_with_filename != poster_final_path and os.path.exists(poster_new_path_with_filename):
            move_file(poster_new_path_with_filename, poster_final_path)
        elif poster_old_path_with_filename != poster_final_path and os.path.exists(poster_old_path_with_filename):
            move_file(poster_old_path_with_filename, poster_final_path)
        elif poster_old_path_no_filename != poster_final_path and os.path.exists(poster_old_path_no_filename):
            move_file(poster_old_path_no_filename, poster_final_path)
        else:
            poster_exists = False

        if poster_exists:
            Flags.file_done_dic[json_data["number"]].update({"local_poster": poster_final_path})
            # 清理旧图片
            if poster_old_path_with_filename.lower() != poster_final_path.lower() and os.path.exists(
                poster_old_path_with_filename
            ):
                delete_file(poster_old_path_with_filename)
            if poster_old_path_no_filename.lower() != poster_final_path.lower() and os.path.exists(
                poster_old_path_no_filename
            ):
                delete_file(poster_old_path_no_filename)
            if poster_new_path_with_filename.lower() != poster_final_path.lower() and os.path.exists(
                poster_new_path_with_filename
            ):
                delete_file(poster_new_path_with_filename)
        elif Flags.file_done_dic[json_data["number"]]["local_poster"]:
            copy_file(Flags.file_done_dic[json_data["number"]]["local_poster"], poster_final_path)

    except Exception:
        signal.show_log_text(traceback.format_exc())

    # thumb 处理：寻找对应文件放到最终路径上。这样避免刮削失败时，旧的图片被删除
    done_thumb_path = Flags.file_done_dic.get(json_data["number"], {}).get("thumb")
    done_thumb_path_copy = True
    try:
        # 图片最终路径等于已下载路径时，图片是已下载的，不需要处理
        if (
            done_thumb_path
            and os.path.exists(done_thumb_path)
            and split_path(done_thumb_path)[0] == split_path(thumb_final_path)[0]
        ):
            done_thumb_path_copy = False  # 标记未复制！此处不复制，在 thumb download中复制
        elif os.path.exists(thumb_final_path):
            pass
        elif thumb_new_path_with_filename != thumb_final_path and os.path.exists(thumb_new_path_with_filename):
            move_file(thumb_new_path_with_filename, thumb_final_path)
        elif thumb_old_path_with_filename != thumb_final_path and os.path.exists(thumb_old_path_with_filename):
            move_file(thumb_old_path_with_filename, thumb_final_path)
        elif thumb_old_path_no_filename != thumb_final_path and os.path.exists(thumb_old_path_no_filename):
            move_file(thumb_old_path_no_filename, thumb_final_path)
        else:
            thumb_exists = False

        if thumb_exists:
            Flags.file_done_dic[json_data["number"]].update({"local_thumb": thumb_final_path})
            # 清理旧图片
            if thumb_old_path_with_filename.lower() != thumb_final_path.lower() and os.path.exists(
                thumb_old_path_with_filename
            ):
                delete_file(thumb_old_path_with_filename)
            if thumb_old_path_no_filename.lower() != thumb_final_path.lower() and os.path.exists(
                thumb_old_path_no_filename
            ):
                delete_file(thumb_old_path_no_filename)
            if thumb_new_path_with_filename.lower() != thumb_final_path.lower() and os.path.exists(
                thumb_new_path_with_filename
            ):
                delete_file(thumb_new_path_with_filename)
        elif Flags.file_done_dic[json_data["number"]]["local_thumb"]:
            copy_file(Flags.file_done_dic[json_data["number"]]["local_thumb"], thumb_final_path)

    except Exception:
        signal.show_log_text(traceback.format_exc())

    # fanart 处理：寻找对应文件放到最终路径上。这样避免刮削失败时，旧的图片被删除
    done_fanart_path = Flags.file_done_dic.get(json_data["number"], {}).get("fanart")
    done_fanart_path_copy = True
    try:
        # 图片最终路径等于已下载路径时，图片是已下载的，不需要处理
        if (
            done_fanart_path
            and os.path.exists(done_fanart_path)
            and split_path(done_fanart_path)[0] == split_path(fanart_final_path)[0]
        ):
            done_fanart_path_copy = False  # 标记未复制！此处不复制，在 fanart download中复制
        elif os.path.exists(fanart_final_path):
            pass
        elif fanart_new_path_with_filename != fanart_final_path and os.path.exists(fanart_new_path_with_filename):
            move_file(fanart_new_path_with_filename, fanart_final_path)
        elif fanart_old_path_with_filename != fanart_final_path and os.path.exists(fanart_old_path_with_filename):
            move_file(fanart_old_path_with_filename, fanart_final_path)
        elif fanart_old_path_no_filename != fanart_final_path and os.path.exists(fanart_old_path_no_filename):
            move_file(fanart_old_path_no_filename, fanart_final_path)
        else:
            fanart_exists = False

        if fanart_exists:
            Flags.file_done_dic[json_data["number"]].update({"local_fanart": fanart_final_path})
            # 清理旧图片
            if fanart_old_path_with_filename.lower() != fanart_final_path.lower() and os.path.exists(
                fanart_old_path_with_filename
            ):
                delete_file(fanart_old_path_with_filename)
            if fanart_old_path_no_filename.lower() != fanart_final_path.lower() and os.path.exists(
                fanart_old_path_no_filename
            ):
                delete_file(fanart_old_path_no_filename)
            if fanart_new_path_with_filename.lower() != fanart_final_path.lower() and os.path.exists(
                fanart_new_path_with_filename
            ):
                delete_file(fanart_new_path_with_filename)
        elif Flags.file_done_dic[json_data["number"]]["local_fanart"]:
            copy_file(Flags.file_done_dic[json_data["number"]]["local_fanart"], fanart_final_path)

    except Exception:
        signal.show_log_text(traceback.format_exc())

    # 更新图片地址
    json_data["poster_path"] = poster_final_path if poster_exists and done_poster_path_copy else ""
    json_data["thumb_path"] = thumb_final_path if thumb_exists and done_thumb_path_copy else ""
    json_data["fanart_path"] = fanart_final_path if fanart_exists and done_fanart_path_copy else ""

    # nfo 处理
    try:
        if os.path.exists(nfo_new_path):
            if nfo_old_path.lower() != nfo_new_path.lower() and os.path.exists(nfo_old_path):
                delete_file(nfo_old_path)
        elif nfo_old_path != nfo_new_path and os.path.exists(nfo_old_path):
            move_file(nfo_old_path, nfo_new_path)
    except Exception:
        signal.show_log_text(traceback.format_exc())

    # trailer
    if trailer_name:  # 预告片名字不含视频文件名
        # trailer最终路径等于已下载路径时，trailer是已下载的，不需要处理
        if os.path.exists(trailer_new_file_path):
            if os.path.exists(trailer_old_file_path_with_filename):
                delete_file(trailer_old_file_path_with_filename)
            elif os.path.exists(trailer_new_file_path_with_filename):
                delete_file(trailer_new_file_path_with_filename)
        elif trailer_old_file_path != trailer_new_file_path and os.path.exists(trailer_old_file_path):
            if not os.path.exists(trailer_new_folder_path):
                os.makedirs(trailer_new_folder_path)
            move_file(trailer_old_file_path, trailer_new_file_path)
        elif os.path.exists(trailer_new_file_path_with_filename):
            if not os.path.exists(trailer_new_folder_path):
                os.makedirs(trailer_new_folder_path)
            move_file(trailer_new_file_path_with_filename, trailer_new_file_path)
        elif os.path.exists(trailer_old_file_path_with_filename):
            if not os.path.exists(trailer_new_folder_path):
                os.makedirs(trailer_new_folder_path)
            move_file(trailer_old_file_path_with_filename, trailer_new_file_path)

        # 删除旧文件夹，用不到了
        if trailer_old_folder_path != trailer_new_folder_path and os.path.exists(trailer_old_folder_path):
            shutil.rmtree(trailer_old_folder_path, ignore_errors=True)
        # 删除带文件名文件，用不到了
        if os.path.exists(trailer_old_file_path_with_filename):
            delete_file(trailer_old_file_path_with_filename)
        if trailer_new_file_path_with_filename != trailer_old_file_path_with_filename and os.path.exists(
            trailer_new_file_path_with_filename
        ):
            delete_file(trailer_new_file_path_with_filename)
    else:
        # 目标文件带文件名
        if os.path.exists(trailer_new_file_path_with_filename):
            if trailer_old_file_path_with_filename != trailer_new_file_path_with_filename and os.path.exists(
                trailer_old_file_path_with_filename
            ):
                delete_file(trailer_old_file_path_with_filename)
        elif trailer_old_file_path_with_filename != trailer_new_file_path_with_filename and os.path.exists(
            trailer_old_file_path_with_filename
        ):
            move_file(trailer_old_file_path_with_filename, trailer_new_file_path_with_filename)
        elif os.path.exists(trailer_old_file_path):
            move_file(trailer_old_file_path, trailer_new_file_path_with_filename)
        elif trailer_new_file_path != trailer_old_file_path and os.path.exists(trailer_new_file_path):
            move_file(trailer_new_file_path, trailer_new_file_path_with_filename)
        else:
            trailer_exists = False

        if trailer_exists:
            Flags.file_done_dic[json_data["number"]].update({"local_trailer": trailer_new_file_path_with_filename})
            # 删除旧、新文件夹，用不到了(分集使用local trailer复制即可)
            if os.path.exists(trailer_old_folder_path):
                shutil.rmtree(trailer_old_folder_path, ignore_errors=True)
            if trailer_new_folder_path != trailer_old_folder_path and os.path.exists(trailer_new_folder_path):
                shutil.rmtree(trailer_new_folder_path, ignore_errors=True)
            # 删除带文件名旧文件，用不到了
            if trailer_old_file_path_with_filename != trailer_new_file_path_with_filename and os.path.exists(
                trailer_old_file_path_with_filename
            ):
                delete_file(trailer_old_file_path_with_filename)
        else:
            local_trailer = Flags.file_done_dic.get(json_data["number"], {}).get("local_trailer")
            if local_trailer and os.path.exists(local_trailer):
                copy_file(local_trailer, trailer_new_file_path_with_filename)

    # 处理 extrafanart、extrafanart副本、主题视频、附加视频
    if single_folder_catched:
        # 处理 extrafanart
        try:
            if os.path.exists(extrafanart_new_path):
                if extrafanart_old_path.lower() != extrafanart_new_path.lower() and os.path.exists(
                    extrafanart_old_path
                ):
                    shutil.rmtree(extrafanart_old_path, ignore_errors=True)
            elif os.path.exists(extrafanart_old_path):
                move_file(extrafanart_old_path, extrafanart_new_path)
        except Exception:
            signal.show_log_text(traceback.format_exc())

        # extrafanart副本
        try:
            if os.path.exists(extrafanart_copy_new_path):
                if extrafanart_copy_old_path.lower() != extrafanart_copy_new_path.lower() and os.path.exists(
                    extrafanart_copy_old_path
                ):
                    shutil.rmtree(extrafanart_copy_old_path, ignore_errors=True)
            elif os.path.exists(extrafanart_copy_old_path):
                move_file(extrafanart_copy_old_path, extrafanart_copy_new_path)
        except Exception:
            signal.show_log_text(traceback.format_exc())

        # 主题视频
        if os.path.exists(theme_videos_new_path):
            if theme_videos_old_path.lower() != theme_videos_new_path.lower() and os.path.exists(theme_videos_old_path):
                shutil.rmtree(theme_videos_old_path, ignore_errors=True)
        elif os.path.exists(theme_videos_old_path):
            move_file(theme_videos_old_path, theme_videos_new_path)

        # 附加视频
        if os.path.exists(extrafanart_extra_new_path):
            if extrafanart_extra_old_path.lower() != extrafanart_extra_new_path.lower() and os.path.exists(
                extrafanart_extra_old_path
            ):
                shutil.rmtree(extrafanart_extra_old_path, ignore_errors=True)
        elif os.path.exists(extrafanart_extra_old_path):
            move_file(extrafanart_extra_old_path, extrafanart_extra_new_path)

    return pic_final_catched, single_folder_catched


def _pic_some_deal(json_data: JsonData, thumb_final_path: str, fanart_final_path: str) -> None:
    """
    thumb、poster、fanart 删除冗余的图片
    """
    # 不保存thumb时，清理 thumb
    if "thumb" not in config.download_files and "thumb" not in config.keep_files:
        if os.path.exists(fanart_final_path):
            Flags.file_done_dic[json_data["number"]].update({"thumb": fanart_final_path})
        else:
            Flags.file_done_dic[json_data["number"]].update({"thumb": ""})
        if os.path.exists(thumb_final_path):
            delete_file(thumb_final_path)
            LogBuffer.log().write("\n 🍀 Thumb delete done!")


def _deal_path_name(path: str) -> str:
    # Windows 保留文件名
    if IS_WINDOWS:
        windows_keep_name = ["CON", "PRN", "NUL", "AUX"]
        temp_list = re.split(r"[/\\]", path)
        for i in range(len(temp_list)):
            if temp_list[i].upper() in windows_keep_name:
                temp_list[i] += "☆"
        return convert_path("/".join(temp_list))
    return path


def save_success_list(old_path: str = "", new_path: str = "") -> None:
    if old_path and config.record_success_file:
        # 软硬链接时，保存原路径；否则保存新路径
        if config.soft_link != 0:
            Flags.success_list.add(convert_path(old_path))
        else:
            Flags.success_list.add(convert_path(new_path))
            if os.path.islink(new_path):
                Flags.success_list.add(convert_path(old_path))
                Flags.success_list.add(convert_path(read_link(new_path)))
    if get_used_time(Flags.success_save_time) > 5 or not old_path:
        Flags.success_save_time = time.time()
        try:
            with open(resources.userdata_path("success.txt"), "w", encoding="utf-8", errors="ignore") as f:
                temp = list(Flags.success_list)
                temp.sort()
                f.write("\n".join(temp))
        except Exception as e:
            signal.show_log_text(f"  Save success list Error {str(e)}\n {traceback.format_exc()}")
        signal.view_success_file_settext.emit(f"查看 ({len(Flags.success_list)})")


def save_remain_list() -> None:
    if Flags.can_save_remain and "remain_task" in config.switch_on:
        try:
            with open(resources.userdata_path("remain.txt"), "w", encoding="utf-8", errors="ignore") as f:
                f.write("\n".join(Flags.remain_list))
                Flags.can_save_remain = False
        except Exception as e:
            signal.show_log_text(f"save remain list error: {str(e)}\n {traceback.format_exc()}")


def check_and_clean_files() -> None:
    signal.change_buttons_status.emit()
    start_time = time.time()
    movie_path = get_movie_path_setting()[0]
    signal.show_log_text("🍯 🍯 🍯 NOTE: START CHECKING AND CLEAN FILE NOW!!!")
    signal.show_log_text(f"\n ⏰ Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    signal.show_log_text(f" 🖥 Movie path: {movie_path} \n ⏳ Checking all videos and cleaning, Please wait...")
    total = 0
    succ = 0
    fail = 0
    for root, dirs, files in os.walk(movie_path, topdown=True):
        for f in files:
            # 判断清理文件
            path = os.path.join(root, f)
            file_type_current = os.path.splitext(f)[1]
            if _need_clean(path, f, file_type_current):
                total += 1
                result, error_info = delete_file(path)
                if result:
                    succ += 1
                    signal.show_log_text(f" 🗑 Clean: {path} ")
                else:
                    fail += 1
                    signal.show_log_text(f" 🗑 Clean error: {error_info} ")
    signal.show_log_text(f" 🍀 Clean done!({get_used_time(start_time)}s)")
    signal.show_log_text("================================================================================")
    _clean_empty_fodlers(movie_path, FileMode.Default)
    signal.set_label_file_path.emit("🗑 清理完成！")
    signal.show_log_text(
        f" 🎉🎉🎉 All finished!!!({get_used_time(start_time)}s) Total {total} , Success {succ} , Failed {fail} "
    )
    signal.show_log_text("================================================================================")
    signal.reset_buttons_status.emit()
