import asyncio
import os
import re
import shutil
import time
import traceback

import aiofiles
import aiofiles.os

from mdcx.config.extend import get_movie_path_setting, need_clean
from mdcx.config.manager import config
from mdcx.config.resources import resources
from mdcx.consts import IS_WINDOWS
from mdcx.models.enums import FileMode
from mdcx.models.flags import Flags
from mdcx.models.log_buffer import LogBuffer
from mdcx.signals import signal
from mdcx.utils import convert_path, get_current_time, get_used_time, nfd2c, split_path
from mdcx.utils.file import (
    copy_file_async,
    copy_file_sync,
    delete_file_async,
    delete_file_sync,
    move_file_async,
    read_link_async,
    read_link_sync,
)


async def move_other_file(number: str, folder_old_path: str, folder_new_path: str, file_name: str, naming_rule: str):
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

    files = await aiofiles.os.listdir(folder_old_path)
    for old_file in files:
        if os.path.splitext(old_file)[1].lower() in config.media_type:
            continue
        if number in old_file or file_name in old_file or naming_rule in old_file:
            if "-cd" not in old_file.lower():  # 避免多分集时，其他分级的内容被移走
                old_file_old_path = os.path.join(folder_old_path, old_file)
                old_file_new_path = os.path.join(folder_new_path, old_file)
                if (
                    old_file_old_path != old_file_new_path
                    and await aiofiles.os.path.exists(old_file_old_path)
                    and not await aiofiles.os.path.exists(old_file_new_path)
                ):
                    await move_file_async(old_file_old_path, old_file_new_path)
                    LogBuffer.log().write(f"\n 🍀 Move {old_file} done!")


async def copy_trailer_to_theme_videos(folder_new_path: str, naming_rule: str) -> None:
    start_time = time.time()
    download_files = config.download_files
    keep_files = config.keep_files
    theme_videos_folder_path = os.path.join(folder_new_path, "backdrops")
    theme_videos_new_path = os.path.join(theme_videos_folder_path, "theme_video.mp4")

    # 不保留不下载主题视频时，删除
    if "theme_videos" not in download_files and "theme_videos" not in keep_files:
        if await aiofiles.os.path.exists(theme_videos_folder_path):
            shutil.rmtree(theme_videos_folder_path, ignore_errors=True)
        return

    # 保留主题视频并存在时返回
    if "theme_videos" in keep_files and await aiofiles.os.path.exists(theme_videos_folder_path):
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
    if not await aiofiles.os.path.exists(trailer_file_path):
        return

    # 存在预告片时复制
    if not await aiofiles.os.path.exists(theme_videos_folder_path):
        await aiofiles.os.makedirs(theme_videos_folder_path)
    if await aiofiles.os.path.exists(theme_videos_new_path):
        await delete_file_async(theme_videos_new_path)
    await copy_file_async(trailer_file_path, theme_videos_new_path)
    LogBuffer.log().write("\n 🍀 Theme video done! (copy trailer)")

    # 不下载并且不保留预告片时，删除预告片
    if "trailer" not in download_files and "trailer" not in config.keep_files:
        await delete_file_async(trailer_file_path)
        if trailer_name:
            shutil.rmtree(trailer_folder, ignore_errors=True)
        LogBuffer.log().write("\n 🍀 Trailer delete done!")


async def pic_some_deal(number: str, thumb_final_path: str, fanart_final_path: str) -> None:
    """
    thumb、poster、fanart 删除冗余的图片
    """
    # 不保存thumb时，清理 thumb
    if "thumb" not in config.download_files and "thumb" not in config.keep_files:
        if await aiofiles.os.path.exists(fanart_final_path):
            Flags.file_done_dic[number].update({"thumb": fanart_final_path})
        else:
            Flags.file_done_dic[number].update({"thumb": ""})
        if await aiofiles.os.path.exists(thumb_final_path):
            await delete_file_async(thumb_final_path)
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


async def save_success_list(old_path: str = "", new_path: str = "") -> None:
    if old_path and config.record_success_file:
        # 软硬链接时，保存原路径；否则保存新路径
        if config.soft_link != 0:
            Flags.success_list.add(convert_path(old_path))
        else:
            Flags.success_list.add(convert_path(new_path))
            if await aiofiles.os.path.islink(new_path):
                Flags.success_list.add(convert_path(old_path))
                Flags.success_list.add(convert_path(await read_link_async(new_path)))
    if get_used_time(Flags.success_save_time) > 5 or not old_path:
        Flags.success_save_time = time.time()
        try:
            async with aiofiles.open(
                resources.userdata_path("success.txt"), "w", encoding="utf-8", errors="ignore"
            ) as f:
                temp = list(Flags.success_list)
                temp.sort()
                await f.write("\n".join(temp))
        except Exception as e:
            signal.show_log_text(f"  Save success list Error {str(e)}\n {traceback.format_exc()}")
        signal.view_success_file_settext.emit(f"查看 ({len(Flags.success_list)})")


def save_remain_list() -> None:
    """This function is intended to be sync."""
    if Flags.can_save_remain and "remain_task" in config.switch_on:
        try:
            with open(resources.userdata_path("remain.txt"), "w", encoding="utf-8", errors="ignore") as f:
                f.write("\n".join(Flags.remain_list))
                Flags.can_save_remain = False
        except Exception as e:
            signal.show_log_text(f"save remain list error: {str(e)}\n {traceback.format_exc()}")


async def _clean_empty_fodlers(path: str, file_mode: FileMode) -> None:
    start_time = time.time()
    if not config.del_empty_folder or file_mode == FileMode.Again:
        return
    signal.set_label_file_path.emit("🗑 正在清理空文件夹，请等待...")
    signal.show_log_text(" ⏳ Cleaning empty folders...")
    if "folder" in config.no_escape:
        escape_folder_list = ""
    else:
        escape_folder_list = get_movie_path_setting()[3]
    if not await aiofiles.os.path.exists(path):
        signal.show_log_text(f" 🍀 Clean done!({get_used_time(start_time)}s)")
        signal.show_log_text("=" * 80)
        return

    def task():
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
                delete_file_sync(hidden_file_mac)  # 删除隐藏文件
            if os.path.exists(hidden_file_windows):
                delete_file_sync(hidden_file_windows)  # 删除隐藏文件
            try:
                if not os.listdir(folder):
                    os.rmdir(folder)
                    signal.show_log_text(f" 🗑 Clean empty folder: {convert_path(folder)}")
            except Exception as e:
                signal.show_traceback_log(traceback.format_exc())
                signal.show_log_text(f" 🔴 Delete empty folder error: {str(e)}")

    await asyncio.to_thread(task)
    signal.show_log_text(f" 🍀 Clean done!({get_used_time(start_time)}s)")
    signal.show_log_text("=" * 80)


async def check_and_clean_files() -> None:
    signal.change_buttons_status.emit()
    start_time = time.time()
    movie_path = get_movie_path_setting()[0]
    signal.show_log_text("🍯 🍯 🍯 NOTE: START CHECKING AND CLEAN FILE NOW!!!")
    signal.show_log_text(f"\n ⏰ Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    signal.show_log_text(f" 🖥 Movie path: {movie_path} \n ⏳ Checking all videos and cleaning, Please wait...")
    total = 0
    succ = 0
    fail = 0
    # 只有主界面点击会运行此函数, 因此此 walk 无需后台执行
    for root, dirs, files in os.walk(movie_path, topdown=True):
        for f in files:
            # 判断清理文件
            path = os.path.join(root, f)
            file_type_current = os.path.splitext(f)[1]
            if need_clean(path, f, file_type_current):
                total += 1
                result, error_info = delete_file_sync(path)
                if result:
                    succ += 1
                    signal.show_log_text(f" 🗑 Clean: {path} ")
                else:
                    fail += 1
                    signal.show_log_text(f" 🗑 Clean error: {error_info} ")
    signal.show_log_text(f" 🍀 Clean done!({get_used_time(start_time)}s)")
    signal.show_log_text("================================================================================")
    await _clean_empty_fodlers(movie_path, FileMode.Default)
    signal.set_label_file_path.emit("🗑 清理完成！")
    signal.show_log_text(
        f" 🎉🎉🎉 All finished!!!({get_used_time(start_time)}s) Total {total} , Success {succ} , Failed {fail} "
    )
    signal.show_log_text("================================================================================")
    signal.reset_buttons_status.emit()


def get_success_list() -> None:
    """This function is intended to be sync"""
    Flags.success_save_time = time.time()
    if os.path.isfile(resources.userdata_path("success.txt")):
        with open(resources.userdata_path("success.txt"), encoding="utf-8", errors="ignore") as f:
            temp = f.read()
            Flags.success_list = set(temp.split("\n")) if temp.strip() else set()
            if "" in Flags.success_list:
                Flags.success_list.remove("")
            config.executor.run(save_success_list())
    signal.view_success_file_settext.emit(f"查看 ({len(Flags.success_list)})")


async def movie_lists(escape_folder_list: list[str], movie_type: str, movie_path: str) -> list[str]:
    start_time = time.time()
    total = []
    media_type = movie_type.split("|")
    skip_list = ["skip", ".skip", ".ignore"]
    not_skip_success = bool("skip_success_file" not in config.no_escape)

    signal.show_traceback_log("🔎 遍历待刮削目录....")

    def task():
        i = 100
        skip = 0
        skip_repeat_softlink = 0
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
                    file_name, file_ext = os.path.splitext(f)

                    # 跳过隐藏文件、预告片、主题视频
                    if re.search(r"^\..+", file_name):
                        continue
                    if "trailer." in f or "trailers." in f:
                        continue
                    if "theme_video." in f:
                        continue

                    # 判断清理文件
                    path = os.path.join(root, f)
                    if need_clean(path, f, file_ext):
                        result, error_info = delete_file_sync(path)
                        if result:
                            signal.show_log_text(f" 🗑 Clean: {path} ")
                        else:
                            signal.show_log_text(f" 🗑 Clean error: {error_info} ")
                        continue

                    # 添加文件
                    temp_total = []
                    if file_ext.lower() in media_type:
                        if os.path.islink(path):
                            real_path = read_link_sync(path)
                            # 清理失效的软链接文件
                            if "check_symlink" in config.no_escape and not os.path.exists(real_path):
                                result, error_info = delete_file_sync(path)
                                if result:
                                    signal.show_log_text(f" 🗑 Clean dead link: {path} ")
                                else:
                                    signal.show_log_text(f" 🗑 Clean dead link error: {error_info} ")
                                continue
                            if real_path in temp_total:
                                skip_repeat_softlink += 1
                                delete_file_sync(path)
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
        return total, skip, skip_repeat_softlink

    total, skip, skip_repeat_softlink = await asyncio.to_thread(task)

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


async def get_movie_list(file_mode: FileMode, movie_path: str, escape_folder_list: list[str]) -> list[str]:
    movie_list = []
    if file_mode == FileMode.Default:  # 刮削默认视频目录的文件
        movie_path = convert_path(movie_path)
        if not await aiofiles.os.path.exists(movie_path):
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
                # 获取所有需要刮削的影片列表
                movie_list = await movie_lists(escape_folder_list, config.media_type, movie_path)
            except Exception:
                signal.show_traceback_log(traceback.format_exc())
                signal.show_log_text(traceback.format_exc())
            count_all = len(movie_list)
            signal.show_log_text(" 📺 Find " + str(count_all) + " movies")

    elif file_mode == FileMode.Single:  # 刮削单文件（工具页面）
        file_path = Flags.single_file_path.strip()
        if not await aiofiles.os.path.exists(file_path):
            signal.show_log_text(" 🔴 Movie file does not exist!")
        else:
            movie_list.append(file_path)  # 把文件路径添加到movie_list
            signal.show_log_text(" 🖥 File path: " + file_path)
            if Flags.appoint_url:
                signal.show_log_text(" 🌐 File url: " + Flags.appoint_url)

    return movie_list


async def newtdisk_creat_symlink(copy_flag: bool, netdisk_path: str = "", local_path: str = "") -> None:
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
        if not netdisk_path or not local_path:
            signal.show_log_text(f" 🔴 网盘目录和本地目录不能为空！请重新设置！({get_used_time(start_time)}s)")
            signal.show_log_text("================================================================================")
            if from_tool:
                signal.reset_buttons_status.emit()
            return
        copy_exts = [".nfo", ".jpg", ".png"] + config.sub_type.split("|")
        file_exts = config.media_type.lower().split("|") + copy_exts + config.sub_type.split("|")

        def task():
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
                        copy_file_sync(net_file, local_file)
                        signal.show_log_text(f" {total} 🍀 Copy done!\n {net_file} ")
                        copy_num += 1
                        continue
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
            return total, copy_num, link_num, skip_num, fail_num

        total, copy_num, link_num, skip_num, fail_num = await asyncio.to_thread(task)
        signal.show_log_text(
            f"\n 🎉🎉🎉 All finished!!!({get_used_time(start_time)}s) Total {total} , "
            f"Linked {link_num} , Copied {copy_num} , Skiped {skip_num} , Failed {fail_num} "
        )
    except Exception:
        print(traceback.format_exc())
        signal.show_log_text(traceback.format_exc())

    signal.show_log_text("================================================================================")
    if from_tool:
        signal.reset_buttons_status.emit()


async def move_file_to_failed_folder(failed_folder: str, file_path: str, folder_old_path: str) -> str:
    # 更新模式、读取模式，不移动失败文件；不移动文件-关时，不移动； 软硬链接开时，不移动
    main_mode = config.main_mode
    if main_mode == 3 or main_mode == 4 or not config.failed_file_move or config.soft_link != 0:
        LogBuffer.log().write(f"\n 🙊 [Movie] {file_path}")
        return file_path

    # 创建failed文件夹
    if config.failed_file_move == 1 and not await aiofiles.os.path.exists(failed_folder):
        try:
            await aiofiles.os.makedirs(failed_folder)
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
    while await aiofiles.os.path.exists(file_new_path) and file_new_path != convert_path(file_path):
        file_new_path = file_new_path.replace(file_ext, "@" + file_ext)

    # 移动
    try:
        await move_file_async(file_path, file_new_path)
        LogBuffer.log().write("\n 🔴 Move file to the failed folder!")
        LogBuffer.log().write(f"\n 🙊 [Movie] {file_new_path}")
        error_info = LogBuffer.error().get()
        LogBuffer.error().clear()
        LogBuffer.error().write(error_info.replace(file_path, file_new_path))

        # 同步移动预告片
        trailer_new_path = file_new_path.replace(file_ext, "-trailer.mp4")
        if not await aiofiles.os.path.exists(trailer_new_path):
            try:
                has_trailer = False
                if await aiofiles.os.path.exists(trailer_old_path_with_filename):
                    has_trailer = True
                    await move_file_async(trailer_old_path_with_filename, trailer_new_path)
                elif await aiofiles.os.path.exists(trailer_old_path_no_filename):
                    has_trailer = True
                    await move_file_async(trailer_old_path_no_filename, trailer_new_path)
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
            if await aiofiles.os.path.exists(sub_old_path) and not await aiofiles.os.path.exists(sub_new_path):
                result, error_info = await move_file_async(sub_old_path, sub_new_path)
                if not result:
                    LogBuffer.log().write(f"\n 🔴 Failed to move sub to the failed folder!\n     {error_info}")
                else:
                    LogBuffer.log().write("\n 💡 Move sub to the failed folder!")
                    LogBuffer.log().write(f"\n 💡 [Sub] {sub_new_path}")
        return file_new_path
    except Exception as e:
        LogBuffer.log().write(f"\n 🔴 Failed to move the file to the failed folder! \n    {str(e)}")
        return file_path


async def check_file(file_path: str, file_escape_size: float) -> bool:
    if await aiofiles.os.path.islink(file_path):
        file_path = await read_link_async(file_path)
        if "check_symlink" not in config.no_escape:
            return True

    if not await aiofiles.os.path.exists(file_path):
        LogBuffer.error().write("文件不存在")
        LogBuffer.req().write("do_not_update_json_data_dic")
        return False
    if "no_skip_small_file" not in config.no_escape:
        file_size = await aiofiles.os.path.getsize(file_path) / float(1024 * 1024)
        if file_size < file_escape_size:
            LogBuffer.error().write(
                f"文件小于 {file_escape_size} MB 被过滤!（实际大小 {round(file_size, 2)} MB）已跳过刮削！"
            )
            LogBuffer.req().write("do_not_update_json_data_dic")
            return False
    return True


async def move_torrent(folder_old_path: str, folder_new_path: str, file_name: str, movie_number: str, naming_rule: str):
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
        await aiofiles.os.path.exists(torrent_file1)
        and torrent_file1 != torrent_file1_new_path
        and not await aiofiles.os.path.exists(torrent_file1_new_path)
    ):
        await move_file_async(torrent_file1, torrent_file1_new_path)
        LogBuffer.log().write("\n 🍀 Torrent done!")

    if torrent_file2 != torrent_file1:
        if (
            await aiofiles.os.path.exists(torrent_file2)
            and torrent_file2 != torrent_file2_new_path
            and not await aiofiles.os.path.exists(torrent_file2_new_path)
        ):
            await move_file_async(torrent_file2, torrent_file2_new_path)
            LogBuffer.log().write("\n 🍀 Torrent done!")


async def move_bif(folder_old_path: str, folder_new_path: str, file_name: str, naming_rule: str) -> None:
    # 更新模式 或 读取模式
    if config.main_mode == 3 or config.main_mode == 4:
        if config.update_mode == "c" and not config.success_file_rename:
            return

    elif not config.success_file_move and not config.success_file_rename:
        return
    bif_old_path = os.path.join(folder_old_path, (file_name + "-320-10.bif"))
    bif_new_path = os.path.join(folder_new_path, (naming_rule + "-320-10.bif"))
    if (
        bif_old_path != bif_new_path
        and await aiofiles.os.path.exists(bif_old_path)
        and not await aiofiles.os.path.exists(bif_new_path)
    ):
        await move_file_async(bif_old_path, bif_new_path)
        LogBuffer.log().write("\n 🍀 Bif done!")


async def move_trailer_video(folder_old_path: str, folder_new_path: str, file_name: str, naming_rule: str) -> None:
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
        if await aiofiles.os.path.exists(trailer_old_path) and not await aiofiles.os.path.exists(trailer_new_path):
            await move_file_async(trailer_old_path, trailer_new_path)
            LogBuffer.log().write("\n 🍀 Trailer done!")
