import asyncio
import random
import re
import time
import traceback

import zhconv

from mdcx.config.manager import config
from mdcx.config.resources import resources
from mdcx.models.base.translate import (
    deepl_translate_async,
    google_translate_async,
    llm_translate_async,
    youdao_translate_async,
)
from mdcx.models.base.web import get_actorname, get_yesjav_title
from mdcx.models.log_buffer import LogBuffer
from mdcx.models.types import CrawlersResult
from mdcx.number import get_number_letters
from mdcx.signals import signal
from mdcx.utils import get_used_time, remove_repeat
from mdcx.utils.str import is_japanese


def translate_info(json_data: CrawlersResult, has_sub: bool):
    xml_info = resources.info_mapping_data
    if xml_info is not None and len(xml_info) == 0:
        return json_data
    tag_translate = config.tag_translate
    series_translate = config.series_translate
    studio_translate = config.studio_translate
    publisher_translate = config.publisher_translate
    director_translate = config.director_translate
    tag_language = config.tag_language
    series_language = config.series_language
    studio_language = config.studio_language
    publisher_language = config.publisher_language
    director_language = config.director_language
    fields_rule = config.fields_rule

    tag_include = config.tag_include
    tag = json_data.tag
    remove_key = [
        "HD高画质",
        "HD高畫質",
        "高画质",
        "高畫質",
        "無碼流出",
        "无码流出",
        "無碼破解",
        "无码破解",
        "無碼片",
        "无码片",
        "有碼片",
        "有码片",
        "無碼",
        "无码",
        "有碼",
        "有码",
        "流出",
        "国产",
        "國產",
    ]
    for each_key in remove_key:
        tag = tag.replace(each_key, "")

    # 映射tag并且存在xml_info时，处理tag映射
    if tag_translate:
        tag_list = re.split(r"[,，]", tag)
        tag_new = []
        for each_info in tag_list:
            if each_info:  # 为空时会多出来一个
                info_data = resources.get_info_data(each_info)
                each_info = info_data.get(tag_language)
                if each_info and each_info not in tag_new:
                    tag_new.append(each_info)
        tag = ",".join(tag_new)

    # tag去重/去空/排序
    tag = remove_repeat(tag)

    # 添加演员
    if "actor" in tag_include and json_data.actor:
        actor = json_data.actor
        actor_list: list = actor.split(",")

        for each_actor in actor_list:
            should_add = True
            if len(config.nfo_tag_actor_contains_list) > 0:
                # 按白名单筛选演员名
                should_add = each_actor in config.nfo_tag_actor_contains_list

            if should_add:
                # 按要求修改演员命名格式
                nfo_tag_actor = config.nfo_tag_actor.replace("actor", each_actor)
                if nfo_tag_actor:
                    tag = nfo_tag_actor + "," + tag

    # 添加番号前缀
    letters = json_data.letters
    if "letters" in tag_include and letters and letters != "未知车牌":
        # 去除素人番号前缀数字
        if "del_num" in fields_rule:
            temp_n = re.findall(r"\d{3,}([a-zA-Z]+-\d+)", json_data.number)
            if temp_n:
                letters = get_number_letters(temp_n[0])
                json_data.letters = letters
                json_data.number = temp_n[0]
        tag = letters + "," + tag
        tag = tag.strip(",")

    # 添加字幕、马赛克信息到tag中
    mosaic = json_data.mosaic
    if has_sub and "cnword" in tag_include:
        tag += ",中文字幕"
    if mosaic and "mosaic" in tag_include:
        tag += "," + mosaic

    # 添加系列、制作、发行信息到tag中
    series = json_data.series
    studio = json_data.studio
    publisher = json_data.publisher
    director = json_data.director
    if not studio and publisher:
        studio = publisher
    if not publisher and studio:
        publisher = studio

    # 系列
    if series:  # 为空时会匹配所有
        if series_translate:  # 映射
            info_data = resources.get_info_data(series)
            series = info_data.get(series_language, "")
        if series and "series" in tag_include:  # 写nfo
            nfo_tag_series = config.nfo_tag_series.replace("series", series)
            if nfo_tag_series:
                tag += f",{nfo_tag_series}"

    # 片商
    if studio:
        if studio_translate:
            info_data = resources.get_info_data(studio)
            studio = info_data.get(studio_language, "")
        if studio and "studio" in tag_include:
            nfo_tag_studio = config.nfo_tag_studio.replace("studio", studio)
            if nfo_tag_studio:
                tag += f",{nfo_tag_studio}"

    # 发行
    if publisher:
        if publisher_translate:
            info_data = resources.get_info_data(publisher)
            publisher = info_data.get(publisher_language, "")
        if publisher and "publisher" in tag_include:
            nfo_tag_publisher = config.nfo_tag_publisher.replace("publisher", publisher)
            if nfo_tag_publisher:
                tag += f",{nfo_tag_publisher}"

    # 导演
    if director and director_translate:
        info_data = resources.get_info_data(director)
        director = info_data.get(director_language, "")

    if tag_language == "zh_cn":
        tag = zhconv.convert(tag, "zh-cn")
    elif tag_language == "zh_tw":
        tag = zhconv.convert(tag, "zh-hant")

    # tag去重/去空/排序
    tag = remove_repeat(tag)

    json_data.tag = tag.strip(",")
    json_data.series = series
    json_data.studio = studio
    json_data.publisher = publisher
    json_data.director = director
    return json_data


async def translate_actor(res: CrawlersResult):
    # 网络请求真实的演员名字
    actor_realname = config.actor_realname
    mosaic = res.mosaic
    number = res.number

    # 非读取模式，勾选了使用真实名字时; 读取模式，勾选了允许更新真实名字时
    if actor_realname:
        start_time = time.time()
        if mosaic != "国产" and (
            number.startswith("FC2") or number.startswith("SIRO") or re.search(r"\d{3,}[A-Z]{3,}-", number)
        ):
            result, temp_actor = await get_actorname(res.number)
            if result:
                actor: str = res.actor
                all_actor: str = res.all_actor
                actor_list: list = all_actor.split(",")
                res.actor = temp_actor
                # 从actor_list中循环查找元素是否包含字符串temp_actor，有则替换
                for item in actor_list:
                    if item.find(actor) != -1:
                        actor_list[actor_list.index(item)] = temp_actor
                res.all_actor = ",".join(actor_list)

                LogBuffer.log().write(
                    f"\n 👩🏻 Av-wiki done! Actor's real Japanese name is '{temp_actor}' ({get_used_time(start_time)}s)"
                )
            else:
                LogBuffer.log().write(f"\n 🔴 Av-wiki failed! {temp_actor} ({get_used_time(start_time)}s)")

    # 如果不映射，返回
    if not config.actor_translate:
        return res

    # 映射表数据加载失败，返回
    xml_actor = resources.actor_mapping_data
    if xml_actor is not None and len(xml_actor) == 0:
        return res

    # 未知演员，返回
    actor = res.actor
    if "actor_all," in config.nfo_include_new:
        actor = res.all_actor
    if actor == config.actor_no_name:
        return res

    # 查询映射表
    actor_list = actor.split(",")
    actor_new_list = []
    actor_href_list = []
    actor_language = config.actor_language
    for each_actor in actor_list:
        if each_actor:
            actor_data = resources.get_actor_data(each_actor)
            new_actor = actor_data.get(actor_language)
            if new_actor not in actor_new_list:
                actor_new_list.append(new_actor)
                if actor_data.get("href"):
                    actor_href_list.append(actor_data.get("href"))
    res.actor = ",".join(actor_new_list)
    if "actor_all," in config.nfo_include_new:
        res.all_actor = ",".join(actor_new_list)

    return res


async def translate_title_outline(json_data: CrawlersResult, cd_part: str, movie_number: str):
    title_language = config.title_language
    title_translate = config.title_translate
    outline_language = config.outline_language
    outline_translate = config.outline_translate
    translate_by = config.translate_by
    if title_language == "jp" and outline_language == "jp":
        return
    trans_title = ""
    trans_outline = ""
    title_sehua = config.title_sehua
    title_sehua_zh = config.title_sehua_zh
    title_yesjav = config.title_yesjav
    title_is_jp = is_japanese(json_data.title)

    # 处理title
    if title_language != "jp":
        movie_title = ""

        # 匹配本地高质量标题(色花标题数据)
        if title_sehua_zh or (title_is_jp and title_sehua):
            start_time = time.time()
            try:
                movie_title = resources.sehua_title_data.get(movie_number)
            except Exception:
                signal.show_traceback_log(traceback.format_exc())
                signal.show_log_text(traceback.format_exc())
            if movie_title:
                json_data.title = movie_title
                LogBuffer.log().write(f"\n 🌸 Sehua title done!({get_used_time(start_time)}s)")

        # 匹配网络高质量标题（yesjav， 可在线更新）
        if not movie_title and title_yesjav and title_is_jp:
            start_time = time.time()
            movie_title = await get_yesjav_title(movie_number)
            if movie_title and not is_japanese(movie_title):
                json_data.title = movie_title
                LogBuffer.log().write(f"\n 🆈 Yesjav title done!({get_used_time(start_time)}s)")

        # 使用json_data数据
        if not movie_title and title_translate and title_is_jp:
            trans_title = json_data.title

    # 处理outline
    if json_data.outline and outline_language != "jp" and outline_translate and is_japanese(json_data.outline):
        trans_outline = json_data.outline

    # 翻译
    if config.translate_by_list and ((trans_title and title_translate) or (trans_outline and outline_translate)):
        start_time = time.time()
        translate_by_list = config.translate_by_list.copy()
        if not cd_part:
            random.shuffle(translate_by_list)

        async def _task(each):
            if each == "youdao":  # 使用有道翻译
                t, o, r = await youdao_translate_async(trans_title, trans_outline)
            elif each == "google":  # 使用 google 翻译
                t, o, r = await google_translate_async(trans_title, trans_outline)
            elif each == "llm":  # 使用 llm 翻译
                t, o, r = await llm_translate_async(trans_title, trans_outline)
            else:  # 使用deepl翻译
                t, o, r = await deepl_translate_async(trans_title, trans_outline, "JA")
            if r:
                LogBuffer.log().write(
                    f"\n 🔴 Translation failed!({each.capitalize()})({get_used_time(start_time)}s) Error: {r}"
                )
            else:
                if t:
                    json_data.title = t
                if o:
                    json_data.outline = o
                LogBuffer.log().write(f"\n 🍀 Translation done!({each.capitalize()})({get_used_time(start_time)}s)")
                json_data.outline_from = each
                return "break"

        res = await asyncio.gather(*[_task(each) for each in translate_by_list])
        for r in res:
            if r == "break":
                break
        else:
            translate_by = translate_by.strip(",").capitalize()
            LogBuffer.log().write(f"\n 🔴 Translation failed! {translate_by} 不可用！({get_used_time(start_time)}s)")

    # 简繁转换
    if title_language == "zh_cn":
        json_data.title = zhconv.convert(json_data.title, "zh-cn")
    elif title_language == "zh_tw":
        json_data.title = zhconv.convert(json_data.title, "zh-hant")
        json_data.mosaic = zhconv.convert(json_data.mosaic, "zh-hant")

    if outline_language == "zh_cn":
        json_data.outline = zhconv.convert(json_data.outline, "zh-cn")
    elif outline_language == "zh_tw":
        json_data.outline = zhconv.convert(json_data.outline, "zh-hant")

    return json_data
