"""
补全emby信息及头像
"""

import asyncio
import os
import re
import shutil
import time
import traceback

import aiofiles
import aiofiles.os
from lxml import etree

from mdcx.config.extend import get_movie_path_setting
from mdcx.config.manager import manager
from mdcx.config.resources import resources
from mdcx.models.base.web import download_file_with_filepath
from mdcx.models.tools.actress_db import ActressDB
from mdcx.models.tools.emby import EMbyActressInfo
from mdcx.models.tools.emby_actor_image import (
    _generate_server_url,
    _get_emby_actor_list,
    _get_gfriends_actor_data,
    update_emby_actor_photo,
)
from mdcx.models.tools.wiki import get_detail, search_wiki
from mdcx.signals import signal
from mdcx.utils import get_used_time
from mdcx.utils.file import copy_file_async


async def creat_kodi_actors(add: bool) -> None:
    signal.change_buttons_status.emit()
    signal.show_log_text(f"📂 待刮削目录: {get_movie_path_setting()[0]}")
    if add:
        signal.show_log_text("💡 将为待刮削目录中的每个视频创建 .actors 文件夹，并补全演员图片到 .actors 文件夹中\n")
        signal.show_log_text("👩🏻 开始补全 Kodi/Plex/Jvedio 演员头像...")
        gfriends_actor_data = await _get_gfriends_actor_data()
    else:
        signal.show_log_text("💡 将清除该目录下的所有 .actors 文件夹...\n")
        gfriends_actor_data = True

    if gfriends_actor_data:
        await _deal_kodi_actors(gfriends_actor_data, add)
    signal.reset_buttons_status.emit()
    signal.show_log_text("================================================================================")


async def update_emby_actor_info() -> None:
    signal.change_buttons_status.emit()
    start_time = time.time()
    emby_on = manager.config_v1.emby_on
    server_name = "Emby" if "emby" in manager.config_v1.server_type else "Jellyfin"
    signal.show_log_text(f"👩🏻 开始补全 {server_name} 演员信息...")

    actor_list = await _get_emby_actor_list()
    tasks = []

    for actor in actor_list:
        actor_name = actor.get("Name")
        # 名字含有空格时跳过
        if re.search(r"[ .·・-]", actor_name):
            signal.show_log_text(f"🔍 {actor_name}: 名字含有空格等分隔符，识别为非女优，跳过！")
            continue
        task = asyncio.create_task(_process_actor_async(actor, emby_on))
        tasks.append(task)

    db = 0
    wiki = 0
    updated = 0
    for task in asyncio.as_completed(tasks):
        flag, msg = await task
        updated += flag != 0
        wiki += flag & 1
        db += flag >> 1
        signal.show_log_text(msg)

    signal.show_log_text(
        f"\n🎉🎉🎉 补全完成！！！ 用时 {get_used_time(start_time)} 秒 共更新: {updated} Wiki 获取: {wiki} 数据库: {db}"
    )

    if "actor_info_photo" in emby_on:
        signal.show_log_text("5 秒后开始补全演员头像头像...")
        await asyncio.sleep(5)
        signal.show_log_text("\n")
        signal.change_buttons_status.emit()
        await update_emby_actor_photo()
        signal.reset_buttons_status.emit()
    else:
        signal.reset_buttons_status.emit()


async def _process_actor_async(actor: dict, emby_on) -> tuple[int, str]:
    """异步处理单个演员信息"""
    actor_name = actor.get("Name", "Unknown Actor")
    try:
        server_id = actor.get("ServerId", "")
        actor_id = actor.get("Id", "")
        # 已有资料时跳过
        actor_homepage, actor_person, _, _, _, update_url = _generate_server_url(actor)
        res, error = await manager.computed.async_client.get_json(actor_person, use_proxy=False)
        if res is None:
            return 0, f"🔴 {actor_name}: Emby/Jellyfin 获取演员信息错误！\n    错误信息: {error}"

        overview = res.get("Overview", "")
        if overview and "无维基百科信息" not in overview and "actor_info_miss" in emby_on:
            return 0, f"✅ {actor_name}: Emby/Jellyfin 已有演员信息！跳过！"

        actor_info = EMbyActressInfo(name=actor_name, server_id=server_id, id=actor_id)
        db_exist = 0
        wiki_found = 0
        # wiki
        logs = []
        res, msg = await search_wiki(actor_info)
        logs.append(msg)
        if res is not None:
            result, error = await get_detail(res, msg, actor_info)
            if result:  # 成功
                wiki_found = 1
        # db
        if manager.config_v1.use_database:
            if "数据库补全" in overview and "actor_info_miss" in emby_on:  # 已有数据库信息
                db_exist = 0
                logs.append(f"{actor_name}: 已有数据库信息")
            else:
                db_exist, msg = ActressDB.update_actor_info_from_db(actor_info)
                logs.append(msg)
        # summary
        summary = "\n    " + "\n".join(logs) if logs else ""
        if db_exist or wiki_found:
            res, error = await manager.computed.async_client.post_text(
                update_url, json_data=actor_info.dump(), use_proxy=False
            )
            if res is not None:
                return (
                    wiki_found + (db_exist << 1),
                    f"✅ {actor_name} 更新成功.{summary}\n主页: {actor_homepage}",
                )
            else:
                return 0, f"🔴 {actor_name} 更新失败: {error}{summary}"
        else:
            return 0, f"🔴 {actor_name}: 未检索到演员信息！跳过！"

    except Exception:
        return 0, f"🔴 {actor_name} 未知异常:\n    {traceback.format_exc()}"


async def show_emby_actor_list(mode: int) -> None:
    signal.change_buttons_status.emit()
    start_time = time.time()

    mode += 1
    if mode == 1:
        signal.show_log_text("🚀 开始查询所有演员列表...")
    elif mode == 2:
        signal.show_log_text("🚀 开始查询 有头像，有信息 的演员列表...")
    elif mode == 3:
        signal.show_log_text("🚀 开始查询 没头像，有信息 的演员列表...")
    elif mode == 4:
        signal.show_log_text("🚀 开始查询 有头像，没信息 的演员列表...")
    elif mode == 5:
        signal.show_log_text("🚀 开始查询 没信息，没头像 的演员列表...")
    elif mode == 6:
        signal.show_log_text("🚀 开始查询 有信息 的演员列表...")
    elif mode == 7:
        signal.show_log_text("🚀 开始查询 没信息 的演员列表...")
    elif mode == 8:
        signal.show_log_text("🚀 开始查询 有头像 的演员列表...")
    elif mode == 9:
        signal.show_log_text("🚀 开始查询 没头像 的演员列表...")

    actor_list = await _get_emby_actor_list()
    if actor_list:
        count = 1
        succ_pic = 0
        fail_pic = 0
        succ_info = 0
        fail_info = 0
        succ = 0
        fail_noinfo = 0
        fail_nopic = 0
        fail = 0
        total = len(actor_list)
        actor_list_temp = ""
        logs = ""
        for actor_js in actor_list:
            actor_name = actor_js["Name"]
            actor_imagetages = actor_js["ImageTags"]
            actor_homepage, actor_person, pic_url, backdrop_url, backdrop_url_0, update_url = _generate_server_url(
                actor_js
            )
            # http://192.168.5.191:8096/web/index.html#!/item?id=2146&serverId=57cdfb2560294a359d7778e7587cdc98

            if actor_imagetages:
                succ_pic += 1
                actor_list_temp = f"\n✅ {count}/{total} 已有头像！ 👩🏻 {actor_name} \n{actor_homepage}"
            else:
                fail_pic += 1
                actor_list_temp = f"\n🔴 {count}/{total} 没有头像！ 👩🏻 {actor_name} \n{actor_homepage}"

            if mode > 7:
                if mode == 8 and actor_imagetages:
                    actor_list_temp = f"\n✅ {succ_pic}/{total} 已有头像！ 👩🏻 {actor_name} \n{actor_homepage}"
                    logs += actor_list_temp + "\n"
                elif mode == 9 and not actor_imagetages:
                    actor_list_temp = f"\n🔴 {fail_pic}/{total} 没有头像！ 👩🏻 {actor_name} \n{actor_homepage}"
                    logs += actor_list_temp + "\n"
                if count % 100 == 0 or (succ_pic + fail_pic) == total:
                    signal.show_log_text(logs)
                    logs = ""
                count += 1
            else:
                # http://192.168.5.191:8096/emby/Persons/梦乃爱华?api_key=ee9a2f2419704257b1dd60b975f2d64e
                res, error = await manager.computed.async_client.get_json(actor_person, use_proxy=False)
                if res is None:
                    signal.show_log_text(
                        f"\n🔴 {count}/{total} Emby 获取演员信息错误！👩🏻 {actor_name} \n    错误信息: {error}"
                    )
                    continue
                overview = res.get("Overview")

                if overview:
                    succ_info += 1
                else:
                    fail_info += 1

                if mode == 1:
                    if actor_imagetages and overview:
                        signal.show_log_text(
                            f"\n✅ {count}/{total} 已有信息！已有头像！ 👩🏻 {actor_name} \n{actor_homepage}"
                        )
                        succ += 1
                    elif actor_imagetages:
                        signal.show_log_text(
                            f"\n🔴 {count}/{total} 没有信息！已有头像！ 👩🏻 {actor_name} \n{actor_homepage}"
                        )
                        fail_noinfo += 1
                    elif overview:
                        signal.show_log_text(
                            f"\n🔴 {count}/{total} 已有信息！没有头像！ 👩🏻 {actor_name} \n{actor_homepage}"
                        )
                        fail_nopic += 1
                    else:
                        signal.show_log_text(
                            f"\n🔴 {count}/{total} 没有信息！没有头像！ 👩🏻 {actor_name} \n{actor_homepage}"
                        )
                        fail += 1
                    count += 1
                elif mode == 2 and actor_imagetages and overview:
                    signal.show_log_text(
                        f"\n✅ {count}/{total} 已有信息！已有头像！ 👩🏻 {actor_name} \n{actor_homepage}"
                    )
                    count += 1
                    succ += 1
                elif mode == 3 and not actor_imagetages and overview:
                    signal.show_log_text(
                        f"\n🔴 {count}/{total} 已有信息！没有头像！ 👩🏻 {actor_name} \n{actor_homepage}"
                    )
                    count += 1
                    fail_nopic += 1
                elif mode == 4 and actor_imagetages and not overview:
                    signal.show_log_text(
                        f"\n🔴 {count}/{total} 没有信息！已有头像！ 👩🏻 {actor_name} \n{actor_homepage}"
                    )
                    count += 1
                    fail_noinfo += 1
                elif mode == 5 and not actor_imagetages and not overview:
                    signal.show_log_text(
                        f"\n🔴 {count}/{total} 没有信息！没有头像！ 👩🏻 {actor_name} \n{actor_homepage}"
                    )
                    count += 1
                    fail += 1
                elif mode == 6 and overview:
                    signal.show_log_text(f"\n✅ {count}/{total} 已有信息！ 👩🏻 {actor_name} \n{actor_homepage}")
                    count += 1
                elif mode == 7 and not overview:
                    signal.show_log_text(f"\n🔴 {count}/{total} 没有信息！ 👩🏻 {actor_name} \n{actor_homepage}")
                    count += 1

        signal.show_log_text(f"\n\n🎉🎉🎉 查询完成！ 用时: {get_used_time(start_time)}秒")
        if mode == 1:
            signal.show_log_text(
                f"👩🏻 演员数量: {total} ✅ 有头像有信息: {succ} 🔴 有头像没信息: {fail_noinfo} 🔴 没头像有信息: {fail_nopic} 🔴 没头像没信息: {fail}\n"
            )
        elif mode == 2:
            other = total - succ
            signal.show_log_text(f"👩🏻 演员数量: {total} ✅ 有头像有信息: {succ} 🔴 其他: {other}\n")
        elif mode == 3:
            signal.show_log_text(f"👩🏻 演员数量: {total} 🔴 有信息没头像: {fail_nopic}\n")
        elif mode == 4:
            signal.show_log_text(f"👩🏻 演员数量: {total} 🔴 有头像没信息: {fail_noinfo}\n")
        elif mode == 5:
            signal.show_log_text(f"👩🏻 演员数量: {total} 🔴 没信息没头像: {fail}\n")
        elif mode == 6 or mode == 7:
            signal.show_log_text(f"👩🏻 演员数量: {total} ✅ 已有信息: {succ_info} 🔴 没有信息: {fail_info}\n")
        else:
            signal.show_log_text(f"👩🏻 演员数量: {total} ✅ 已有头像: {succ_pic} 🔴 没有头像: {fail_pic}\n")
        signal.show_log_text("================================================================================")
        signal.reset_buttons_status.emit()


async def _deal_kodi_actors(gfriends_actor_data, add):
    vedio_path = get_movie_path_setting()[0]
    if vedio_path == "" or not await aiofiles.os.path.isdir(vedio_path):
        signal.show_log_text("🔴 待刮削目录不存在！任务已停止！")
        return False
    else:
        actor_folder = resources.userdata_path("actor")
        emby_on = manager.config_v1.emby_on
        all_files = await asyncio.to_thread(os.walk, vedio_path)
        all_actor = set()
        success = set()
        failed = set()
        download_failed = set()
        no_pic = set()
        actor_clear = set()
        for root, dirs, files in all_files:
            if not add:
                for each_dir in dirs:
                    if each_dir == ".actors":
                        kodi_actor_folder = os.path.join(root, each_dir)
                        await asyncio.to_thread(shutil.rmtree, kodi_actor_folder, ignore_errors=True)
                        signal.show_log_text(f"✅ 头像文件夹已清理！{kodi_actor_folder}")
                        actor_clear.add(kodi_actor_folder)
                continue
            for file in files:
                if file.lower().endswith(".nfo"):
                    nfo_path = os.path.join(root, file)
                    vedio_actor_folder = os.path.join(root, ".actors")
                    try:
                        async with aiofiles.open(nfo_path, encoding="utf-8") as f:
                            content = await f.read()
                        parser = etree.HTMLParser(encoding="utf-8")
                        xml_nfo = etree.HTML(content.encode("utf-8"), parser)
                        actor_list = xml_nfo.xpath("//actor/name/text()")
                        for each in actor_list:
                            all_actor.add(each)
                            actor_name_list = resources.get_actor_data(each)["keyword"]
                            for actor_name in actor_name_list:
                                if actor_name:
                                    net_pic_path = gfriends_actor_data.get(f"{actor_name}.jpg")
                                    if net_pic_path:
                                        vedio_actor_path = os.path.join(vedio_actor_folder, each + ".jpg")
                                        if await aiofiles.os.path.isfile(vedio_actor_path):
                                            if "actor_replace" not in emby_on:
                                                success.add(each)
                                                continue
                                        if "https://" in net_pic_path:
                                            net_file_name = net_pic_path.split("/")[-1]
                                            net_file_name = re.findall(r"^[^?]+", net_file_name)[0]
                                            local_file_path = os.path.join(actor_folder, net_file_name)
                                            if not await aiofiles.os.path.isfile(local_file_path):
                                                if not await download_file_with_filepath(
                                                    net_pic_path, local_file_path, actor_folder
                                                ):
                                                    signal.show_log_text(
                                                        f"🔴 {actor_name} 头像下载失败！{net_pic_path}"
                                                    )
                                                    failed.add(each)
                                                    download_failed.add(each)
                                                    continue
                                        else:
                                            local_file_path = net_pic_path
                                        if not await aiofiles.os.path.isdir(vedio_actor_folder):
                                            await aiofiles.os.mkdir(vedio_actor_folder)
                                        await copy_file_async(local_file_path, vedio_actor_path)
                                        signal.show_log_text(f"✅ {actor_name} 头像已创建！ {vedio_actor_path}")
                                        success.add(each)
                                        break
                            else:
                                signal.show_log_text(f"🔴 {each} 没有头像资源！")
                                failed.add(each)
                                no_pic.add(each)
                    except Exception:
                        signal.show_traceback_log(traceback.format_exc())
        if add:
            signal.show_log_text(
                f"\n🎉 操作已完成! 共有演员: {len(all_actor)}, 已有头像: {len(success)}, 没有头像: {len(failed)}, 下载失败: {len(download_failed)}, 没有资源: {len(no_pic)}"
            )
        else:
            signal.show_log_text(f"\n🎉 操作已完成! 共清理了 {len(actor_clear)} 个 .actors 文件夹!")
        return
