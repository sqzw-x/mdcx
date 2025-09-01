import asyncio
import os
import re
import shutil
import time
import traceback
from pathlib import Path

import aiofiles
import aiofiles.os

from ..config.enums import DownloadableFile, NoEscape, Switch
from ..config.extend import get_movie_path_setting, need_clean
from ..config.manager import manager
from ..config.models import CleanAction
from ..config.resources import resources
from ..models.enums import FileMode
from ..models.flags import Flags
from ..models.log_buffer import LogBuffer
from ..signals import signal
from ..utils import executor, get_current_time, get_used_time
from ..utils.file import copy_file_async, copy_file_sync, delete_file_async, delete_file_sync, move_file_async


async def move_other_file(number: str, folder_old_path: Path, folder_new_path: Path, file_name: str, naming_rule: str):
    # 软硬链接模式不移动
    if manager.config.soft_link != 0:
        return

    # 目录相同不移动
    if folder_new_path == folder_old_path:
        return

    # 更新模式 或 读取模式
    if manager.config.main_mode == 3 or manager.config.main_mode == 4:
        if manager.config.update_mode == "c" and not manager.config.success_file_rename:
            return

    elif not manager.config.success_file_move and not manager.config.success_file_rename:
        return

    files = await aiofiles.os.listdir(folder_old_path)
    for old_file in files:
        if os.path.splitext(old_file)[1].lower() in manager.config.media_type:
            continue
        if (
            number in old_file or file_name in old_file or naming_rule in old_file
        ) and "-cd" not in old_file.lower():  # 避免多分集时，其他分级的内容被移走
            old_file_old_path = folder_old_path / old_file
            old_file_new_path = folder_new_path / old_file
            if (
                old_file_old_path != old_file_new_path
                and await aiofiles.os.path.exists(old_file_old_path)
                and not await aiofiles.os.path.exists(old_file_new_path)
            ):
                await move_file_async(old_file_old_path, old_file_new_path)
                LogBuffer.log().write(f"\n 🍀 Move {old_file} done!")


async def copy_trailer_to_theme_videos(folder_new_path: Path, naming_rule: str) -> None:
    start_time = time.time()
    download_files = manager.config.download_files
    keep_files = manager.config.keep_files
    theme_videos_folder_path = folder_new_path / "backdrops"
    theme_videos_new_path = theme_videos_folder_path / "theme_video.mp4"

    # 不保留不下载主题视频时，删除
    if DownloadableFile.THEME_VIDEOS not in download_files and DownloadableFile.THEME_VIDEOS not in keep_files:
        if await aiofiles.os.path.exists(theme_videos_folder_path):
            shutil.rmtree(theme_videos_folder_path, ignore_errors=True)
        return

    # 保留主题视频并存在时返回
    if DownloadableFile.THEME_VIDEOS in keep_files and await aiofiles.os.path.exists(theme_videos_folder_path):
        LogBuffer.log().write(f"\n 🍀 Theme video done! (old)({get_used_time(start_time)}s) ")
        return

    # 不下载主题视频时返回
    if DownloadableFile.THEME_VIDEOS not in download_files:
        return

    # 不存在预告片时返回
    trailer_name = manager.config.trailer_simple_name
    trailer_folder = None
    if trailer_name:
        trailer_folder = folder_new_path / "trailers"
        trailer_file_path = trailer_folder / "trailer.mp4"
    else:
        trailer_file_path = folder_new_path / (naming_rule + "-trailer.mp4")
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
    if DownloadableFile.TRAILER not in download_files and DownloadableFile.TRAILER not in manager.config.keep_files:
        await delete_file_async(trailer_file_path)
        if trailer_name and trailer_folder:
            shutil.rmtree(trailer_folder, ignore_errors=True)
        LogBuffer.log().write("\n 🍀 Trailer delete done!")


async def pic_some_deal(number: str, thumb_final_path: Path, fanart_final_path: Path) -> None:
    """
    thumb、poster、fanart 删除冗余的图片
    """
    # 不保存thumb时，清理 thumb
    if (
        DownloadableFile.THUMB not in manager.config.download_files
        and DownloadableFile.THUMB not in manager.config.keep_files
    ):
        if await aiofiles.os.path.exists(fanart_final_path):
            Flags.file_done_dic[number].update(thumb=fanart_final_path)
        else:
            Flags.file_done_dic[number].update(thumb=None)
        if await aiofiles.os.path.exists(thumb_final_path):
            await delete_file_async(thumb_final_path)
            LogBuffer.log().write("\n 🍀 Thumb delete done!")


async def save_success_list(old_path: Path | None = None, new_path: Path | None = None) -> None:
    if old_path and NoEscape.RECORD_SUCCESS_FILE in manager.config.no_escape:
        # 软硬链接时，保存原路径；否则保存新路径
        if manager.config.soft_link != 0:
            Flags.success_list.add(old_path)
        elif new_path:
            Flags.success_list.add(new_path)
            if await aiofiles.os.path.islink(new_path):
                Flags.success_list.add(old_path)
                Flags.success_list.add(new_path.resolve())
    if get_used_time(Flags.success_save_time) > 5 or not old_path:
        Flags.success_save_time = time.time()
        try:
            async with aiofiles.open(resources.u("success.txt"), "w", encoding="utf-8", errors="ignore") as f:
                await f.writelines(sorted(str(p) + "\n" for p in Flags.success_list))
        except Exception as e:
            signal.show_log_text(f"  Save success list Error {str(e)}\n {traceback.format_exc()}")
        signal.view_success_file_settext.emit(f"查看 ({len(Flags.success_list)})")


def save_remain_list() -> None:
    """This function is intended to be sync."""
    if Flags.can_save_remain and Switch.REMAIN_TASK in manager.config.switch_on:
        try:
            with open(resources.u("remain.txt"), "w", encoding="utf-8", errors="ignore") as f:
                f.writelines(sorted(str(p) + "\n" for p in Flags.success_list))
                Flags.can_save_remain = False
        except Exception as e:
            signal.show_log_text(f"save remain list error: {str(e)}\n {traceback.format_exc()}")


async def _clean_empty_fodlers(path: Path, file_mode: FileMode) -> None:
    start_time = time.time()
    if not manager.config.del_empty_folder or file_mode == FileMode.Again:
        return
    signal.set_label_file_path.emit("🗑 正在清理空文件夹，请等待...")
    signal.show_log_text(" ⏳ Cleaning empty folders...")

    if NoEscape.FOLDER in manager.config.no_escape:
        ignore_dirs = []
    else:
        ignore_dirs = get_movie_path_setting().ignore_dirs

    if not await aiofiles.os.path.exists(path):
        signal.show_log_text(f" 🍀 Clean done!({get_used_time(start_time)}s)")
        signal.show_log_text("=" * 80)
        return

    def task():
        folders: list[Path] = []
        for root, dirs, files in path.walk(top_down=True):
            if (root / "skip").exists():  # 是否有skip文件
                dirs[:] = []  # 忽略当前文件夹子目录
                continue
            if root in ignore_dirs:
                dirs[:] = []  # 忽略当前文件夹子目录
                continue
            dirs_list = [root / d for d in dirs]
            folders.extend(dirs_list)
        folders.sort(reverse=True)
        for folder in folders:
            hidden_file_mac = folder / ".DS_Store"
            hidden_file_windows = folder / "Thumbs.db"
            if os.path.exists(hidden_file_mac):
                delete_file_sync(hidden_file_mac)  # 删除隐藏文件
            if os.path.exists(hidden_file_windows):
                delete_file_sync(hidden_file_windows)  # 删除隐藏文件
            try:
                if not os.listdir(folder):
                    os.rmdir(folder)
                    signal.show_log_text(f" 🗑 Clean empty folder: {folder}")
            except Exception as e:
                signal.show_traceback_log(traceback.format_exc())
                signal.show_log_text(f" 🔴 Delete empty folder error: {str(e)}")

    await asyncio.to_thread(task)
    signal.show_log_text(f" 🍀 Clean done!({get_used_time(start_time)}s)")
    signal.show_log_text("=" * 80)


async def check_and_clean_files() -> None:
    signal.change_buttons_status.emit()
    start_time = time.time()
    movie_path = get_movie_path_setting().movie_path
    signal.show_log_text("🍯 🍯 🍯 NOTE: START CHECKING AND CLEAN FILE NOW!!!")
    signal.show_log_text(f"\n ⏰ Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    signal.show_log_text(f" 🖥 Movie path: {movie_path} \n ⏳ Checking all videos and cleaning, Please wait...")
    total = 0
    succ = 0
    fail = 0
    # 只有主界面点击会运行此函数, 因此此 walk 无需后台执行
    for root, dirs, files in Path(movie_path).walk(top_down=True):
        for f in files:
            # 判断清理文件
            path = root / f
            file_type_current = os.path.splitext(f)[1]
            if need_clean(path, f, file_type_current):
                total += 1
                result, error_info = delete_file_sync(path)
                if result:
                    succ += 1
                    signal.show_log_text(f" 🗑 Clean: {str(path)} ")
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
    if os.path.isfile(resources.u("success.txt")):
        with open(resources.u("success.txt"), encoding="utf-8", errors="ignore") as f:
            paths = f.readlines()
            Flags.success_list = {
                p for path in paths if path.strip() and (p := Path(path.strip())).is_file(follow_symlinks=False)
            }
            executor.run(save_success_list())
    signal.view_success_file_settext.emit(f"查看 ({len(Flags.success_list)})")


async def movie_lists(ignore_dirs: list[Path], media_type: list[str], movie_path: Path) -> list[Path]:
    start_time = time.time()
    total = []
    skip_list = ["skip", ".skip", ".ignore"]
    not_skip_success = NoEscape.SKIP_SUCCESS_FILE not in manager.config.no_escape

    signal.show_traceback_log("🔎 遍历待刮削目录....")

    def task():
        i = 100
        skip = 0
        skip_repeat_softlink = 0
        for root, dirs, files in movie_path.walk(top_down=True):
            for d in dirs.copy():
                if root / d in ignore_dirs or "behind the scenes" in d:
                    dirs.remove(d)

            # 文件夹是否存在跳过文件
            for skip_key in skip_list:
                if skip_key in files:
                    dirs.clear()
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
                    path = root / f
                    if CleanAction.AUTO_CLEAN in manager.config.clean_enable and need_clean(path, f, file_ext):
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
                            real_path = path.readlink()
                            # 清理失效的软链接文件
                            if NoEscape.CHECK_SYMLINK in manager.config.no_escape and not os.path.exists(real_path):
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
                        if not_skip_success or path not in Flags.success_list:
                            total.append(path)
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


async def get_movie_list(file_mode: FileMode, movie_path: Path, ignore_dirs: list[Path]) -> list[Path]:
    movie_list = []
    if file_mode == FileMode.Default:  # 刮削默认视频目录的文件
        if not await aiofiles.os.path.exists(movie_path):
            signal.show_log_text("\n 🔴 Movie folder does not exist!")
        else:
            signal.show_log_text(f" 🖥 Movie path: {movie_path}")
            signal.show_log_text(" 🔎 Searching all videos, Please wait...")
            signal.set_label_file_path.emit(f"正在遍历待刮削视频目录中的所有视频，请等待...\n {movie_path}")
            if (
                NoEscape.FOLDER in manager.config.no_escape
                or manager.config.main_mode == 3
                or manager.config.main_mode == 4
            ):
                ignore_dirs = []
            try:
                # 获取所有需要刮削的影片列表
                movie_list = await movie_lists(ignore_dirs, manager.config.media_type, movie_path)
            except Exception:
                signal.show_traceback_log(traceback.format_exc())
                signal.show_log_text(traceback.format_exc())
            count_all = len(movie_list)
            signal.show_log_text(" 📺 Find " + str(count_all) + " movies")

    elif file_mode == FileMode.Single:  # 刮削单文件（工具页面）
        file_path = Flags.single_file_path
        if not await aiofiles.os.path.exists(file_path):
            signal.show_log_text(" 🔴 Movie file does not exist!")
        else:
            movie_list.append(file_path)  # 把文件路径添加到movie_list
            signal.show_log_text(f" 🖥 File path: {file_path}")
            if Flags.appoint_url:
                signal.show_log_text(" 🌐 File url: " + Flags.appoint_url)

    return movie_list


async def newtdisk_creat_symlink(
    copy_flag: bool,
    netdisk_path: Path | None = None,
    local_path: Path | None = None,
) -> None:
    from_tool = False
    if not netdisk_path:
        from_tool = True
        signal.change_buttons_status.emit()
    start_time = time.time()
    if not netdisk_path:
        netdisk_path = Path(manager.config.netdisk_path)
    if not local_path:
        local_path = Path(manager.config.localdisk_path)
    signal.show_log_text("🍯 🍯 🍯 开始创建符号链接")
    signal.show_log_text(f" 📁 源路径: {netdisk_path} \n 📁 目标路径：{local_path} \n")
    try:
        if not netdisk_path or not local_path:
            signal.show_log_text(f" 🔴 网盘目录和本地目录不能为空！请重新设置！({get_used_time(start_time)}s)")
            signal.show_log_text("================================================================================")
            if from_tool:
                signal.reset_buttons_status.emit()
            return
        copy_exts = [".nfo", ".jpg", ".png"] + manager.config.sub_type
        file_exts = "|".join(manager.config.media_type).lower().split("|") + copy_exts + manager.config.sub_type

        def task():
            total = 0
            copy_num = 0
            link_num = 0
            fail_num = 0
            skip_num = 0
            done = set()
            for root, _, files in netdisk_path.walk(top_down=True):
                if root == local_path:
                    continue

                local_dir = local_path / root.relative_to(netdisk_path)
                if not local_dir.is_dir():
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
                    net_file = root / f
                    local_file = local_dir / f
                    if local_file.is_file():
                        signal.show_log_text(f" {total} 🟠 跳过: 已存在文件或有效的符号链接\n {net_file} ")
                        skip_num += 1
                        continue
                    if local_file.is_symlink():
                        signal.show_log_text(f" {total} 🔴 删除: 无效的符号链接\n {net_file} ")
                        local_file.unlink()

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


async def move_file_to_failed_folder(failed_folder: Path, file_path: Path, folder_old_path: Path) -> Path:
    # 更新模式、读取模式，不移动失败文件；不移动文件-关时，不移动； 软硬链接开时，不移动
    main_mode = manager.config.main_mode
    if main_mode == 3 or main_mode == 4 or not manager.config.failed_file_move or manager.config.soft_link != 0:
        LogBuffer.log().write(f"\n 🙊 [Movie] {file_path}")
        return file_path

    # 创建failed文件夹
    if manager.config.failed_file_move == 1 and not await aiofiles.os.path.exists(failed_folder):
        try:
            await aiofiles.os.makedirs(failed_folder)
        except Exception:
            signal.show_traceback_log(traceback.format_exc())
            signal.show_log_text(traceback.format_exc())

    # 获取文件路径
    file_full_name = file_path.name
    file_ext = file_path.suffix
    trailer_old_path_no_filename = folder_old_path / "trailers/trailer.mp4"
    trailer_old_path_with_filename = file_path.with_name(file_path.stem + "-trailer.mp4")

    # 重复改名
    file_new_path = failed_folder / file_full_name
    while await aiofiles.os.path.exists(file_new_path) and file_new_path != file_path:
        file_new_path = file_new_path.with_name(file_new_path.stem + "@" + file_ext)

    # 移动
    try:
        await move_file_async(file_path, file_new_path)
        LogBuffer.log().write("\n 🔴 Move file to the failed folder!")
        LogBuffer.log().write(f"\n 🙊 [Movie] {file_new_path}")
        error_info = LogBuffer.error().get()
        LogBuffer.error().clear()
        LogBuffer.error().write(error_info.replace(str(file_path), str(file_new_path)))

        # 同步移动预告片
        trailer_new_path = file_new_path.with_name(file_new_path.stem + "-trailer.mp4")
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
        sub_types = [".chs" + i for i in manager.config.sub_type if ".chs" not in i]
        for sub in sub_types:
            sub_old_path = file_path.with_suffix(sub)
            sub_new_path = file_new_path.with_suffix(sub)
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


async def check_file(file_path: Path, file_escape_size: float) -> bool:
    if await aiofiles.os.path.islink(file_path):
        file_path = file_path.resolve()
        if NoEscape.CHECK_SYMLINK not in manager.config.no_escape:
            return True

    if not await aiofiles.os.path.exists(file_path):
        LogBuffer.error().write("文件不存在")
        return False
    if NoEscape.NO_SKIP_SMALL_FILE not in manager.config.no_escape:
        file_size = await aiofiles.os.path.getsize(file_path) / float(1024 * 1024)
        if file_size < file_escape_size:
            LogBuffer.error().write(
                f"文件小于 {file_escape_size} MB 被过滤!（实际大小 {round(file_size, 2)} MB）已跳过刮削！"
            )
            return False
    return True


async def move_torrent(old_dir: Path, new_dir: Path, file_name: str, number: str, naming_rule: str):
    # 更新模式 或 读取模式
    if manager.config.main_mode == 3 or manager.config.main_mode == 4:
        if manager.config.update_mode == "c" and not manager.config.success_file_rename:
            return

    # 软硬链接开时，不移动
    elif (
        manager.config.soft_link != 0 or not manager.config.success_file_move and not manager.config.success_file_rename
    ):
        return
    torrent_file1 = old_dir / (file_name + ".torrent")
    torrent_file2 = old_dir / (number + ".torrent")
    torrent_file1_new_path = new_dir / (naming_rule + ".torrent")
    torrent_file2_new_path = new_dir / (number + ".torrent")
    if (
        await aiofiles.os.path.exists(torrent_file1)
        and torrent_file1 != torrent_file1_new_path
        and not await aiofiles.os.path.exists(torrent_file1_new_path)
    ):
        await move_file_async(torrent_file1, torrent_file1_new_path)
        LogBuffer.log().write("\n 🍀 Torrent done!")

    if torrent_file2 != torrent_file1 and (
        await aiofiles.os.path.exists(torrent_file2)
        and torrent_file2 != torrent_file2_new_path
        and not await aiofiles.os.path.exists(torrent_file2_new_path)
    ):
        await move_file_async(torrent_file2, torrent_file2_new_path)
        LogBuffer.log().write("\n 🍀 Torrent done!")


async def move_bif(old_dir: Path, new_dir: Path, file_name: str, naming_rule: str) -> None:
    # 更新模式 或 读取模式
    if manager.config.main_mode == 3 or manager.config.main_mode == 4:
        if manager.config.update_mode == "c" and not manager.config.success_file_rename:
            return

    elif not manager.config.success_file_move and not manager.config.success_file_rename:
        return
    bif_old_path = old_dir / (file_name + "-320-10.bif")
    bif_new_path = new_dir / (naming_rule + "-320-10.bif")
    if (
        bif_old_path != bif_new_path
        and await aiofiles.os.path.exists(bif_old_path)
        and not await aiofiles.os.path.exists(bif_new_path)
    ):
        await move_file_async(bif_old_path, bif_new_path)
        LogBuffer.log().write("\n 🍀 Bif done!")


async def move_trailer_video(old_dir: Path, new_dir: Path, file_name: str, naming_rule: str) -> None:
    if manager.config.main_mode < 2 and not manager.config.success_file_move and not manager.config.success_file_rename:
        return
    if manager.config.main_mode > 2:
        update_mode = manager.config.update_mode
        if update_mode == "c" and not manager.config.success_file_rename:
            return

    for media_type in manager.config.media_type:
        trailer_old_path = old_dir / (file_name + "-trailer" + media_type)
        trailer_new_path = new_dir / (naming_rule + "-trailer" + media_type)
        if await aiofiles.os.path.exists(trailer_old_path) and not await aiofiles.os.path.exists(trailer_new_path):
            await move_file_async(trailer_old_path, trailer_new_path)
            LogBuffer.log().write("\n 🍀 Trailer done!")
