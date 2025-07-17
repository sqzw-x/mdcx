import asyncio
import os
import re
import time
import traceback
from typing import Optional, cast

import aiofiles.os
from PyQt5.QtWidgets import QMessageBox

from mdcx.utils import convert_path, get_current_time, get_real_time, get_used_time, split_path
from mdcx.utils.file import copy_file_async, move_file_async, read_link_async

from ...signals import signal
from ..base.file import (
    _clean_empty_fodlers,
    check_file,
    copy_trailer_to_theme_videos,
    get_movie_list,
    move_bif,
    move_file_to_failed_folder,
    move_other_file,
    move_torrent,
    newtdisk_creat_symlink,
    pic_some_deal,
    save_success_list,
)
from ..config.extend import get_movie_path_setting
from ..config.manager import config, manager
from ..config.resources import resources
from ..entity.enums import FileMode
from ..json_data import JsonData
from ..log_buffer import LogBuffer
from ..tools.emby_actor_image import update_emby_actor_photo
from ..tools.emby_actor_info import creat_kodi_actors
from .crawler import crawl
from .file import (
    creat_folder,
    deal_old_files,
    get_file_info,
    get_output_name,
    move_movie,
)
from .flags import Flags
from .image import add_mark, extrafanart_copy2, extrafanart_extras_copy
from .nfo import get_nfo_data, write_nfo
from .translate import translate_actor, translate_info, translate_title_outline
from .utils import (
    deal_some_field,
    get_video_size,
    replace_special_word,
    replace_word,
    show_data_result,
    show_movie_info,
)
from .web import extrafanart_download, fanart_download, poster_download, thumb_download, trailer_download


async def _scrape_one_file(file_path: str, file_info: tuple, file_mode: FileMode) -> tuple[bool, JsonData]:
    # 处理单个文件刮削
    # 初始化所需变量
    start_time = time.time()
    read_mode = config.read_mode
    file_escape_size = float(config.file_size)
    file_path = convert_path(file_path)

    # 获取文件信息
    json_data, movie_number, folder_old_path, file_name, file_ex, sub_list, file_show_name, file_show_path = file_info
    json_data = cast(JsonData, json_data)

    # 获取设置的媒体目录、失败目录、成功目录
    _, success_folder, *_ = get_movie_path_setting(file_path)

    # 检查文件大小
    result = await check_file(file_path, file_escape_size)
    if not result:
        json_data["outline"] = split_path(file_path)[1]
        json_data["tag"] = file_path
        return False, json_data

    # 读取模式
    file_can_download = True
    nfo_can_translate = True
    nfo_update = False
    if config.main_mode == 4:
        result, nfo_data = await get_nfo_data(file_path, movie_number)
        json_data.update(dict(nfo_data))
        if result:  # 有nfo
            movie_number = nfo_data["number"]
            nfo_update = True
            if "has_nfo_update" not in read_mode:  # 不更新并返回
                show_data_result(json_data, start_time)
                show_movie_info(json_data)
                LogBuffer.log().write(f"\n 🙉 [Movie] {file_path}")
                await save_success_list(file_path, file_path)  # 保存成功列表
                return True, json_data

            # 读取模式要不要下载
            if "read_download_again" not in read_mode:
                file_can_download = False

            # 读取模式要不要翻译
            if "read_translate_again" not in read_mode:
                nfo_can_translate = False
            else:
                # 启用翻译时，tag使用纯tag的内容
                json_data["tag"] = nfo_data["tag_only"]
        else:
            if "no_nfo_scrape" not in read_mode:  # 无nfo，没有勾选「无nfo时，刮削并执行更新模式」
                return False, json_data

    # 刮削json_data
    # 获取已刮削的json_data
    if "." in movie_number or json_data["mosaic"] in ["国产"]:
        pass
    elif movie_number not in Flags.json_get_set:
        Flags.json_get_set.add(movie_number)
    elif not Flags.json_data_dic.get(movie_number):
        while not Flags.json_data_dic.get(movie_number):
            await asyncio.sleep(1)

    json_data_old = Flags.json_data_dic.get(movie_number)
    if (
        json_data_old and "." not in movie_number and json_data["mosaic"] not in ["国产"]
    ):  # 已存在该番号数据时直接使用该数据
        json_data_new = {}
        json_data_new.update(json_data_old)
        json_data_new["cd_part"] = json_data["cd_part"]
        json_data_new["has_sub"] = json_data["has_sub"]
        json_data_new["c_word"] = json_data["c_word"]
        json_data_new["destroyed"] = json_data["destroyed"]
        json_data_new["leak"] = json_data["leak"]
        json_data_new["wuma"] = json_data["wuma"]
        json_data_new["youma"] = json_data["youma"]
        json_data_new["_4K"] = ""

        def deal_tag_data(tag):
            for each in [
                "中文字幕",
                "无码流出",
                "無碼流出",
                "无码破解",
                "無碼破解",
                "无码",
                "無碼",
                "有码",
                "有碼",
                "国产",
                "國產",
                "里番",
                "裏番",
                "动漫",
                "動漫",
            ]:
                tag = tag.replace(each, "")
            return tag.replace(",,", ",")

        json_data_new["tag"] = deal_tag_data(json_data_old["tag"])
        json_data_new["file_path"] = json_data["file_path"]

        if "破解" in json_data_old["mosaic"] or "流出" in json_data_old["mosaic"]:
            json_data_new["mosaic"] = json_data["mosaic"] if json_data["mosaic"] else "有码"
        elif "破解" in json_data["mosaic"] or "流出" in json_data["mosaic"]:
            json_data_new["mosaic"] = json_data["mosaic"]
        json_data.update(json_data_new)
    elif not nfo_update:
        res = await crawl(json_data, file_mode)
        json_data.update(**res)

    # 显示json_data结果或日志
    if not show_data_result(json_data, start_time):
        return False, json_data  # 返回MDCx1_1main, 继续处理下一个文件

    # 映射或翻译
    # 当不存在已刮削数据，或者读取模式允许翻译映射时才进行映射翻译
    if not json_data_old and nfo_can_translate:
        deal_some_field(json_data)  # 处理字段
        replace_special_word(json_data)  # 替换特殊字符
        await translate_title_outline(json_data, movie_number)  # 翻译json_data（标题/介绍）
        deal_some_field(json_data)  # 再处理一遍字段，翻译后可能出现要去除的内容
        await translate_actor(json_data)  # 映射输出演员名/信息
        translate_info(json_data)  # 映射输出标签等信息
        replace_word(json_data)

    # 更新视频分辨率
    await get_video_size(json_data, file_path)

    # 显示json_data内容
    show_movie_info(json_data)

    # 生成输出文件夹和输出文件的路径
    (
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
    ) = get_output_name(json_data, file_path, success_folder, file_ex)

    # 判断输出文件的路径是否重复
    if config.soft_link == 0:
        done_file_new_path_list = Flags.file_new_path_dic.get(file_new_path)
        if not done_file_new_path_list:  # 如果字典中不存在同名的情况，存入列表，继续刮削
            Flags.file_new_path_dic[file_new_path] = [file_path]
        else:
            done_file_new_path_list.append(file_path)  # 已存在时，添加到列表，停止刮削
            done_file_new_path_list.sort(reverse=True)
            LogBuffer.error().write(
                "存在重复文件（指刮削后的文件路径相同！），请检查:\n    🍁 " + "\n    🍁 ".join(done_file_new_path_list)
            )
            json_data["outline"] = split_path(file_path)[1]
            json_data["tag"] = file_path
            return False, json_data

    # 判断输出文件夹和文件是否已存在，如无则创建输出文件夹
    if not await creat_folder(
        json_data,
        folder_new_path,
        file_path,
        file_new_path,
        thumb_new_path_with_filename,
        poster_new_path_with_filename,
    ):
        return False, json_data  # 返回MDCx1_1main, 继续处理下一个文件

    # 初始化图片已下载地址的字典
    if not Flags.file_done_dic.get(json_data["number"]):
        Flags.file_done_dic[json_data["number"]] = {
            "poster": "",
            "thumb": "",
            "fanart": "",
            "trailer": "",
            "local_poster": "",
            "local_thumb": "",
            "local_fanart": "",
            "local_trailer": "",
        }

    # 视频模式（原来叫整理模式）
    # 视频模式（仅根据刮削数据把电影命名为番号并分类到对应目录名称的文件夹下）
    if config.main_mode == 2:
        # 移动文件
        if await move_movie(json_data, file_path, file_new_path):
            if "sort_del" in config.switch_on:
                await deal_old_files(
                    json_data,
                    folder_old_path,
                    folder_new_path,
                    file_path,
                    file_new_path,
                    thumb_new_path_with_filename,
                    poster_new_path_with_filename,
                    fanart_new_path_with_filename,
                    nfo_new_path,
                    file_ex,
                    poster_final_path,
                    thumb_final_path,
                    fanart_final_path,
                )  # 清理旧的thumb、poster、fanart、nfo
            await save_success_list(file_path, file_new_path)  # 保存成功列表
            return True, json_data
        else:
            # 返回MDCx1_1main, 继续处理下一个文件
            return False, json_data

    # 清理旧的thumb、poster、fanart、extrafanart、nfo
    pic_final_catched, single_folder_catched = await deal_old_files(
        json_data,
        folder_old_path,
        folder_new_path,
        file_path,
        file_new_path,
        thumb_new_path_with_filename,
        poster_new_path_with_filename,
        fanart_new_path_with_filename,
        nfo_new_path,
        file_ex,
        poster_final_path,
        thumb_final_path,
        fanart_final_path,
    )

    # 如果 final_pic_path 没处理过，这时才需要下载和加水印
    if pic_final_catched:
        if file_can_download:
            # 下载thumb
            if not await thumb_download(json_data, folder_new_path, thumb_final_path):
                return False, json_data  # 返回MDCx1_1main, 继续处理下一个文件

            # 下载艺术图
            await fanart_download(json_data, fanart_final_path)

            # 下载poster
            if not await poster_download(json_data, folder_new_path, poster_final_path):
                return False, json_data  # 返回MDCx1_1main, 继续处理下一个文件

            # 清理冗余图片
            await pic_some_deal(json_data["number"], thumb_final_path, fanart_final_path)

            # 加水印
            await add_mark(json_data, json_data["poster_marked"], json_data["thumb_marked"], json_data["fanart_marked"])

            # 下载剧照和剧照副本
            if single_folder_catched:
                await extrafanart_download(json_data, folder_new_path)
                await extrafanart_copy2(folder_new_path)
                await extrafanart_extras_copy(folder_new_path)

            # 下载trailer、复制主题视频
            # 因为 trailer也有带文件名，不带文件名两种情况，不能使用pic_final_catched。比如图片不带文件名，trailer带文件名这种场景需要支持每个分集去下载trailer
            await trailer_download(json_data, folder_new_path, folder_old_path, naming_rule)
            await copy_trailer_to_theme_videos(folder_new_path, naming_rule)

    # 生成nfo文件
    await write_nfo(
        json_data, nfo_new_path, folder_new_path, file_path, edit_mode=False, nfo_can_translate=nfo_can_translate
    )

    # 移动字幕、种子、bif、trailer、其他文件
    if json_data["has_sub"]:
        await move_sub(folder_old_path, folder_new_path, file_name, sub_list, naming_rule)
    await move_torrent(folder_old_path, folder_new_path, file_name, movie_number, naming_rule)
    await move_bif(folder_old_path, folder_new_path, file_name, naming_rule)
    # self.move_trailer_video(folder_old_path, folder_new_path, file_name, naming_rule)
    await move_other_file(json_data["number"], folder_old_path, folder_new_path, file_name, naming_rule)

    # 移动文件
    if not await move_movie(json_data, file_path, file_new_path):
        return False, json_data  # 返回MDCx1_1main, 继续处理下一个文件
    await save_success_list(file_path, file_new_path)  # 保存成功列表

    # 创建软链接及复制文件
    if config.auto_link:
        target_dir = os.path.join(config.localdisk_path, os.path.relpath(folder_new_path, success_folder))
        await newtdisk_creat_symlink("copy_netdisk_nfo" in config.switch_on, folder_new_path, target_dir)

    # json添加封面缩略图路径
    # json_data['number'] = movie_number
    json_data["poster_path"] = poster_final_path
    json_data["thumb_path"] = thumb_final_path
    json_data["fanart_path"] = fanart_final_path
    if not await aiofiles.os.path.exists(thumb_final_path) and await aiofiles.os.path.exists(fanart_final_path):
        json_data["thumb_path"] = fanart_final_path

    return True, json_data


async def _scrape_exec_thread(task: tuple[str, int, int]) -> None:
    # 获取顺序
    file_path, count, count_all = task
    Flags.counting_order += 1
    count = Flags.counting_order

    # 名字缩写
    file_name_temp = split_path(file_path)[1]
    if len(file_name_temp) > 40:
        file_name_temp = file_name_temp[:40] + "..."

    # 处理间歇任务
    while (
        config.main_mode != 4
        and "rest_scrape" in config.switch_on
        and count - Flags.rest_now_begin_count > config.rest_count
    ):
        _check_stop(file_name_temp)
        await asyncio.sleep(1)

    # 非第一个加延时
    Flags.scrape_starting += 1
    count = Flags.scrape_starting
    thread_time = config.thread_time
    if count == 1 or thread_time == 0 or config.main_mode == 4:
        Flags.next_start_time = time.time()
        signal.show_log_text(f" 🕷 {get_current_time()} 开始刮削：{Flags.scrape_starting}/{count_all} {file_name_temp}")
        thread_time = 0
    else:
        Flags.next_start_time += thread_time

    # 计算本线程开始剩余时间, 休眠并定时检查是否手动停止
    remain_time = int(Flags.next_start_time - time.time())
    if remain_time > 0:
        signal.show_log_text(
            f" ⏱ {get_current_time()}（{remain_time}）秒后开始刮削：{count}/{count_all} {file_name_temp}"
        )
        for i in range(remain_time):
            _check_stop(file_name_temp)
            await asyncio.sleep(1)

    Flags.scrape_started += 1
    if count > 1 and thread_time != 0:
        signal.show_log_text(f" 🕷 {get_current_time()} 开始刮削：{Flags.scrape_started}/{count_all} {file_name_temp}")

    start_time = time.time()
    file_mode = Flags.file_mode

    # 获取文件基础信息
    file_info = await get_file_info(file_path)
    json_data, movie_number, folder_old_path, file_name, file_ex, sub_list, file_show_name, file_show_path = file_info

    # 显示刮削信息
    progress_value = Flags.scrape_started / count_all * 100
    progress_percentage = f"{progress_value:.2f}%"
    signal.exec_set_processbar.emit(int(progress_value))
    signal.set_label_file_path.emit(
        f"正在刮削： {Flags.scrape_started}/{count_all} {progress_percentage} \n {convert_path(file_show_path)}"
    )
    signal.label_result.emit(
        f" 刮削中：{Flags.scrape_started - Flags.succ_count - Flags.fail_count} 成功：{Flags.succ_count} 失败：{Flags.fail_count}"
    )
    LogBuffer.log().write("\n" + "👆" * 50)
    LogBuffer.log().write("\n 🙈 [Movie] " + convert_path(file_path))
    LogBuffer.log().write("\n 🚘 [Number] " + movie_number)

    # 如果指定了单一网站，进行提示
    website_single = config.website_single
    if config.scrape_like == "single" and file_mode != FileMode.Single and config.main_mode != 4:
        LogBuffer.log().write(f"\n 😸 [Note] You specified 「 {website_single} 」, some videos may not have results! ")

    # 获取刮削数据
    try:
        result, json_data = await _scrape_one_file(file_path, file_info, file_mode)
        if LogBuffer.req().get() != "do_not_update_json_data_dic":
            Flags.json_data_dic.update({movie_number: json_data})
    except Exception as e:
        _check_stop(file_name_temp)
        signal.show_traceback_log(traceback.format_exc())
        signal.show_log_text(traceback.format_exc())
        LogBuffer.error().write("scrape file error: " + str(e))
        LogBuffer.log().write("\n" + traceback.format_exc())
        result = False

    # 显示刮削数据
    try:
        if result:
            Flags.succ_count += 1
            succ_show_name = (
                str(Flags.count_claw)
                + "-"
                + str(Flags.succ_count)
                + "."
                + file_show_name.replace(movie_number, json_data["number"])
                + json_data["_4K"]
            )
            signal.show_list_name(succ_show_name, "succ", json_data, movie_number)
        else:
            Flags.fail_count += 1
            fail_show_name = (
                str(Flags.count_claw)
                + "-"
                + str(Flags.fail_count)
                + "."
                + file_show_name.replace(movie_number, json_data["number"])
                + json_data["_4K"]
            )
            signal.show_list_name(fail_show_name, "fail", json_data, movie_number)
            if e := LogBuffer.error().get():
                LogBuffer.log().write(f"\n 🔴 [Failed] Reason: {e}")
                if "WinError 5" in e:
                    LogBuffer.log().write(
                        "\n 🔴 该问题为权限问题：请尝试以管理员身份运行，同时关闭其他正在运行的Python脚本！"
                    )
            _, _, failed_folder, *_ = get_movie_path_setting(file_path)
            fail_file_path = await move_file_to_failed_folder(failed_folder, file_path, folder_old_path)
            Flags.failed_list.append([fail_file_path, LogBuffer.error().get()])
            Flags.failed_file_list.append(fail_file_path)
            await _failed_file_info_show(str(Flags.fail_count), fail_file_path, LogBuffer.error().get())
            signal.view_failed_list_settext.emit(f"失败 {Flags.fail_count}")
    except Exception as e:
        _check_stop(file_name_temp)
        signal.show_traceback_log(traceback.format_exc())
        signal.show_log_text(traceback.format_exc())
        signal.show_log_text(str(e))

    # 显示刮削结果
    try:
        Flags.scrape_done += 1
        count = Flags.scrape_done
        progress_value = count / count_all * 100
        progress_percentage = f"{progress_value:.2f}%"
        used_time = get_used_time(start_time)
        scrape_info_begin = f"{count:d}/{count_all:d} ({progress_percentage}) round({Flags.count_claw}) {split_path(file_path)[1]}    新的刮削线程"
        scrape_info_begin = "\n\n\n" + "👇" * 50 + "\n" + scrape_info_begin
        scrape_info_after = (
            f"\n 🕷 {get_current_time()} {count}/{count_all} {split_path(file_path)[1]} 刮削完成！用时 {used_time} 秒！"
        )
        signal.show_log_text(scrape_info_begin + LogBuffer.log().get() + scrape_info_after)
        remain_count = Flags.scrape_started - count
        if Flags.scrape_started == count_all:
            signal.show_log_text(f" 🕷 剩余正在刮削的线程：{remain_count}")
        signal.label_result.emit(f" 刮削中：{remain_count} 成功：{Flags.succ_count} 失败：{Flags.fail_count}")
        signal.show_scrape_info(f"🔎 已刮削 {count}/{count_all}")
    except Exception as e:
        _check_stop(file_name_temp)
        signal.show_traceback_log(traceback.format_exc())
        signal.show_log_text(traceback.format_exc())
        signal.show_log_text(str(e))

    # 更新剩余任务
    try:
        if file_path:
            file_path = convert_path(file_path)
        try:
            Flags.remain_list.remove(file_path)
            Flags.can_save_remain = True
        except Exception as e1:
            signal.show_log_text(f"remove:  {file_path}\n {str(e1)}\n {traceback.format_exc()}")
    except Exception as e:
        _check_stop(file_name_temp)
        signal.show_traceback_log(traceback.format_exc())
        signal.show_log_text(traceback.format_exc())
        signal.show_log_text(str(e))

    # 处理间歇刮削
    try:
        if config.main_mode != 4 and "rest_scrape" in config.switch_on:
            time_note = f" 🏖 已累计刮削 {count}/{count_all}，已连续刮削 {count - Flags.rest_now_begin_count}/{config.rest_count}..."
            signal.show_log_text(time_note)
            if count - Flags.rest_now_begin_count >= config.rest_count:
                if Flags.scrape_starting > count:
                    time_note = f" 🏖 当前还存在 {Flags.scrape_starting - count} 个已经在刮削的任务，等待这些任务结束将进入休息状态...\n"
                    signal.show_log_text(time_note)
                    while not Flags.rest_sleepping:
                        await asyncio.sleep(1)
                elif not Flags.rest_sleepping and count < count_all:
                    Flags.rest_sleepping = True  # 开始休眠
                    Flags.rest_next_begin_time = time.time()  # 下一轮倒计时开始时间
                    time_note = f'\n ⏸ 休息 {Flags.rest_time_convert} 秒，将在 <font color="red">{get_real_time(Flags.rest_next_begin_time + Flags.rest_time_convert)}</font> 继续刮削剩余的 {count_all - count} 个任务...\n'
                    signal.show_log_text(time_note)
                    while (
                        "rest_scrape" in config.switch_on
                        and time.time() - Flags.rest_next_begin_time < Flags.rest_time_convert
                    ):
                        if Flags.scrape_starting > count:  # 如果突然调大了文件数量，这时跳出休眠
                            break
                        await asyncio.sleep(1)
                    Flags.rest_now_begin_count = count
                    Flags.rest_sleepping = False  # 休眠结束，下一轮开始
                    Flags.next_start_time = time.time() - config.thread_time
                else:
                    while Flags.rest_sleepping:
                        await asyncio.sleep(1)

    except Exception as e:
        _check_stop(file_name_temp)
        signal.show_traceback_log(traceback.format_exc())
        signal.show_log_text(traceback.format_exc())
        signal.show_log_text(str(e))

    LogBuffer.clear_thread()


async def scrape(file_mode: FileMode, movie_list: Optional[list[str]]) -> None:
    Flags.reset()
    if movie_list is None:
        movie_list = []
    Flags.scrape_start_time = time.time()  # 开始刮削时间
    Flags.file_mode = file_mode  # 刮削模式（工具单文件或主界面/日志点开始正常刮削）

    signal.show_scrape_info("🔎 正在刮削中...")

    signal.add_label_info({})  # 清空主界面显示信息
    thread_number = config.thread_number  # 线程数量
    thread_time = config.thread_time  # 线程延时
    signal.label_result.emit(f" 刮削中：{0} 成功：{Flags.succ_count} 失败：{Flags.fail_count}")
    signal.logs_failed_settext.emit("\n\n\n")

    # 日志页面显示开始时间
    Flags.start_time = time.time()
    if file_mode == FileMode.Single:
        signal.show_log_text("🍯 🍯 🍯 NOTE: 当前是单文件刮削模式！")
    elif file_mode == FileMode.Again:
        signal.show_log_text(f"🍯 🍯 🍯 NOTE: 开始重新刮削！！！ 刮削文件数量（{len(movie_list)})")
        n = 0
        for each_f, each_i in Flags.new_again_dic.items():
            n += 1
            if each_i[0]:
                signal.show_log_text(f"{n} 🖥 File path: {each_f}\n 🚘 File number: {each_i[0]}")
            else:
                signal.show_log_text(f"{n} 🖥 File path: {each_f}\n 🌐 File url: {each_i[1]}")

    # 获取设置的媒体目录、失败目录、成功目录
    movie_path, success_folder, failed_folder, escape_folder_list, extrafanart_folder, softlink_path = (
        get_movie_path_setting()
    )

    # 获取待刮削文件列表的相关信息
    if not movie_list:
        if config.scrape_softlink_path:
            await newtdisk_creat_symlink("copy_netdisk_nfo" in config.switch_on, movie_path, softlink_path)
            movie_path = softlink_path
        signal.show_log_text("\n ⏰ Start time: " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        movie_list = await get_movie_list(file_mode, movie_path, escape_folder_list)
    else:
        signal.show_log_text("\n ⏰ Start time: " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    Flags.remain_list = movie_list
    Flags.can_save_remain = True

    count_all = len(movie_list)
    Flags.total_count = count_all

    task_list = []
    i = 0
    for each in movie_list:
        i += 1
        task_list.append((each, i, count_all))

    if count_all:
        Flags.count_claw += 1
        if config.main_mode == 4:
            signal.show_log_text(f" 🕷 当前为读取模式，并发数（{thread_number}），线程延时（0）秒...")
        else:
            if count_all < thread_number:
                thread_number = count_all
            signal.show_log_text(f" 🕷 开启异步并发，并发数（{thread_number}），线程延时（{thread_time}）秒...")
        if "rest_scrape" in config.switch_on and config.main_mode != 4:
            signal.show_log_text(
                f'<font color="brown"> 🍯 间歇刮削 已启用，连续刮削 {config.rest_count} 个文件后，将自动休息 {Flags.rest_time_convert} 秒...</font>'
            )

        Flags.next_start_time = time.time()

        # 创建信号量来限制并发数量
        semaphore = asyncio.Semaphore(thread_number)

        async def limited_scrape_exec_thread(task):
            async with semaphore:
                await _scrape_exec_thread(task)

        # 异步并发
        await asyncio.gather(*[limited_scrape_exec_thread(task) for task in task_list])
        signal.label_result.emit(f" 刮削中：0 成功：{Flags.succ_count} 失败：{Flags.fail_count}")
        await save_success_list()  # 保存成功列表
        if signal.stop:
            return

    signal.show_log_text("================================================================================")
    await _clean_empty_fodlers(movie_path, file_mode)
    end_time = time.time()
    used_time = str(round((end_time - Flags.start_time), 2))
    if count_all:
        average_time = str(round((end_time - Flags.start_time) / count_all, 2))
    else:
        average_time = used_time
    signal.exec_set_processbar.emit(0)
    signal.set_label_file_path.emit(f"🎉 恭喜！全部刮削完成！共 {count_all} 个文件！用时 {used_time} 秒")
    signal.show_traceback_log(
        f"🎉 All finished!!! Total {count_all} , Success {Flags.succ_count} , Failed {Flags.fail_count} "
    )
    signal.show_log_text(
        f" 🎉🎉🎉 All finished!!! Total {count_all} , Success {Flags.succ_count} , Failed {Flags.fail_count} "
    )
    signal.show_log_text("================================================================================")
    if Flags.failed_list:
        signal.show_log_text("    *** Failed results ****")
        for i in range(len(Flags.failed_list)):
            fail_path, fail_reson = Flags.failed_list[i]
            signal.show_log_text(f" 🔴 {i + 1} {fail_path}\n    {fail_reson}")
            signal.show_log_text("================================================================================")
    signal.show_log_text(
        " ⏰ Start time".ljust(15) + ": " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(Flags.start_time))
    )
    signal.show_log_text(" 🏁 End time".ljust(15) + ": " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)))
    signal.show_log_text(" ⏱ Used time".ljust(15) + f": {used_time}S")
    signal.show_log_text(" 📺 Movies num".ljust(15) + f": {count_all}")
    signal.show_log_text(" 🍕 Per time".ljust(15) + f": {average_time}S")
    signal.show_log_text("================================================================================")
    signal.show_scrape_info(f"🎉 刮削完成 {count_all}/{count_all}")

    # auto run after scrape
    if "actor_photo_auto" in config.emby_on:
        await update_emby_actor_photo()
    if config.actor_photo_kodi_auto:
        await creat_kodi_actors(True)

    signal.reset_buttons_status.emit()
    if len(Flags.again_dic):
        Flags.new_again_dic = Flags.again_dic.copy()
        new_movie_list = list(Flags.new_again_dic.keys())
        Flags.again_dic.clear()
        start_new_scrape(FileMode.Again, new_movie_list)
    if "auto_exit" in config.switch_on:
        signal.show_log_text("\n\n 🍔 已启用「刮削后自动退出软件」！")
        count = 5
        for i in range(count):
            signal.show_log_text(f" {count - i} 秒后将自动退出！")
            await asyncio.sleep(1)
        signal.exec_exit_app.emit()


def start_new_scrape(file_mode: FileMode, movie_list: Optional[list[str]] = None) -> None:
    signal.change_buttons_status.emit()
    signal.exec_set_processbar.emit(0)
    try:
        Flags.start_time = time.time()
        config.executor.submit(scrape(file_mode, movie_list))
    except Exception:
        signal.show_traceback_log(traceback.format_exc())
        signal.show_log_text(traceback.format_exc())


def _check_stop(file_name_temp: str) -> None:
    if signal.stop:
        Flags.now_kill += 1
        signal.show_log_text(
            f" 🕷 {get_current_time()} 已停止刮削：{Flags.now_kill}/{Flags.total_kills} {file_name_temp}"
        )
        signal.set_label_file_path.emit(
            f"⛔️ 正在停止刮削...\n   正在停止已在运行的任务线程（{Flags.now_kill}/{Flags.total_kills}）..."
        )
        # exceptions must derive from BaseException
        raise Exception("手动停止刮削")


async def _failed_file_info_show(count: str, path: str, error_info: str) -> None:
    folder = os.path.dirname(path)
    info_str = f"{'🔴 ' + count + '.':<3} {path} \n    所在目录: {folder} \n    失败原因: {error_info} \n"
    if await aiofiles.os.path.islink(path):
        real_path = await read_link_async(path)
        real_folder = os.path.dirname(path)
        info_str = (
            f"{count + '.':<3} {path} \n    指向文件: {real_path} \n    "
            f"所在目录: {real_folder} \n    失败原因: {error_info} \n"
        )
    signal.logs_failed_show.emit(info_str)


def get_remain_list() -> bool:
    """This function is intended to be sync."""
    remain_list_path = resources.userdata_path("remain.txt")
    if os.path.isfile(remain_list_path):
        with open(remain_list_path, encoding="utf-8", errors="ignore") as f:
            temp = f.read()
            Flags.remain_list = temp.split("\n") if temp.strip() else []
            if "remain_task" in config.switch_on and len(Flags.remain_list):
                box = QMessageBox(QMessageBox.Information, "继续刮削", "上次刮削未完成，是否继续刮削剩余任务？")
                box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
                box.button(QMessageBox.Yes).setText("继续刮削剩余任务")
                box.button(QMessageBox.No).setText("从头刮削")
                box.button(QMessageBox.Cancel).setText("取消")
                box.setDefaultButton(QMessageBox.No)
                reply = box.exec()
                if reply == QMessageBox.Cancel:
                    return True  # 不刮削

                if reply == QMessageBox.Yes:
                    movie_path = config.media_path
                    if movie_path == "":
                        movie_path = manager.data_folder
                    if not re.findall(r"[/\\]$", movie_path):
                        movie_path += "/"
                    movie_path = convert_path(movie_path)
                    temp_remain_path = convert_path(Flags.remain_list[0])
                    if movie_path not in temp_remain_path:
                        box = QMessageBox(
                            QMessageBox.Warning,
                            "提醒",
                            f"很重要！！请注意：\n当前待刮削目录：{movie_path}\n剩余任务文件路径：{temp_remain_path}\n剩余任务的文件路径，并不在当前待刮削目录中！\n剩余任务很可能是使用其他配置扫描的！\n请确认成功输出目录和失败目录是否正确！如果配置不正确，继续刮削可能会导致文件被移动到新配置的输出位置！\n是否继续刮削？",
                        )
                        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                        box.button(QMessageBox.Yes).setText("继续")
                        box.button(QMessageBox.No).setText("取消")
                        box.setDefaultButton(QMessageBox.No)
                        reply = box.exec()
                        if reply == QMessageBox.No:
                            return True
                    signal.show_log_text(
                        f"🍯 🍯 🍯 NOTE: 继续刮削未完成任务！！！ 剩余未刮削文件数量（{len(Flags.remain_list)})"
                    )
                    start_new_scrape(FileMode.Default, Flags.remain_list)
                    return True
    return False


def again_search() -> None:
    Flags.new_again_dic = Flags.again_dic.copy()
    new_movie_list = list(Flags.new_again_dic.keys())
    Flags.again_dic.clear()
    start_new_scrape(FileMode.Again, new_movie_list)


async def move_sub(
    folder_old_path: str,
    folder_new_path: str,
    file_name: str,
    sub_list: list[str],
    naming_rule: str,
) -> None:
    copy_flag = False

    # 更新模式 或 读取模式
    if config.main_mode > 2:
        if config.update_mode == "c" and not config.success_file_rename:
            return

    # 软硬链接开时，复制字幕（EMBY 显示字幕）
    elif config.soft_link > 0:
        copy_flag = True

    # 成功移动关、成功重命名关时，返回
    elif not config.success_file_move and not config.success_file_rename:
        return

    for sub in sub_list:
        sub_old_path = os.path.join(folder_old_path, (file_name + sub))
        sub_new_path = os.path.join(folder_new_path, (naming_rule + sub))
        sub_new_path_chs = os.path.join(folder_new_path, (naming_rule + ".chs" + sub))
        if config.subtitle_add_chs:
            if ".chs" not in sub:
                sub_new_path = sub_new_path_chs
        if await aiofiles.os.path.exists(sub_old_path) and not await aiofiles.os.path.exists(sub_new_path):
            if copy_flag:
                if not await copy_file_async(sub_old_path, sub_new_path):
                    LogBuffer.log().write("\n 🔴 Sub copy failed!")
                    return
            elif not await move_file_async(sub_old_path, sub_new_path):
                LogBuffer.log().write("\n 🔴 Sub move failed!")
                return
        LogBuffer.log().write("\n 🍀 Sub done!")
