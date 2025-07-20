"""
刮削过程的一般工具函数
依赖:
    此模块不应依赖 models.core 中除 flags 外的任何其他模块
"""

import asyncio
import os
import re
import traceback

import aiofiles.os

from mdcx.config.manager import config
from mdcx.config.resources import resources
from mdcx.consts import ManualConfig
from mdcx.models.base.number import deal_actor_more
from mdcx.models.log_buffer import LogBuffer
from mdcx.models.types import GetVideoSizeContext, JsonData, ShowData, ShowResultInput, TemplateInput
from mdcx.number import get_number_first_letter, get_number_letters
from mdcx.signals import signal
from mdcx.utils import get_new_release, get_used_time, split_path
from mdcx.utils.file import read_link_async
from mdcx.utils.video import get_video_metadata


def replace_word(json_data: JsonData):
    # 常见字段替换的字符
    for key, value in ManualConfig.ALL_REP_WORD.items():
        for each in ManualConfig.ALL_KEY_WORD:
            json_data[each] = json_data[each].replace(key, value)

    # 简体时替换的字符
    key_word = []
    if config.title_language == "zh_cn":
        key_word.append("title")
    if config.outline_language == "zh_cn":
        key_word.append("outline")

    for key, value in ManualConfig.CHINESE_REP_WORD.items():
        for each in key_word:
            json_data[each] = json_data[each].replace(key, value)

    # 替换标题的上下集信息
    fields_word = ["title", "originaltitle"]
    for field in fields_word:
        for each in ManualConfig.TITLE_REP:
            json_data[field] = json_data[field].replace(each, "").strip(":， ").strip()


def replace_special_word(json_data: JsonData):
    # 常见字段替换的字符
    all_key_word = [
        "title",
        "originaltitle",
        "outline",
        "originalplot",
        "series",
        "director",
        "studio",
        "publisher",
        "tag",
    ]
    for key, value in ManualConfig.SPECIAL_WORD.items():
        for each in all_key_word:
            json_data[each] = json_data[each].replace(key, value)


def deal_some_field(json_data: JsonData) -> JsonData:
    fields_rule = config.fields_rule
    actor = json_data["actor"]
    title = json_data["title"]
    originaltitle = json_data["originaltitle"]
    number = json_data["number"]

    # 演员处理
    if actor:
        # 去除演员名中的括号
        new_actor_list = []
        actor_list = []
        temp_actor_list = []
        for each_actor in actor.split(","):
            if each_actor and each_actor not in actor_list:
                actor_list.append(each_actor)
                new_actor = re.findall(r"[^\(\)\（\）]+", each_actor)
                if new_actor[0] not in new_actor_list:
                    new_actor_list.append(new_actor[0])
                temp_actor_list.extend(new_actor)
        if "del_char" in fields_rule:
            json_data["actor"] = ",".join(new_actor_list)
        else:
            json_data["actor"] = ",".join(actor_list)

        # 去除标题后的演员名
        if "del_actor" in fields_rule:
            new_all_actor_name_list = []
            for each_actor in json_data["actor_amazon"] + temp_actor_list:
                # 获取演员映射表的所有演员别名进行替换
                actor_keyword_list: list[str] = resources.get_actor_data(each_actor).get("keyword", [])
                new_all_actor_name_list.extend(actor_keyword_list)
            for each_actor in set(new_all_actor_name_list):
                try:
                    end_actor = re.compile(rf" {each_actor}$")
                    title = re.sub(end_actor, "", title)
                    originaltitle = re.sub(end_actor, "", originaltitle)
                except Exception:
                    signal.show_traceback_log(traceback.format_exc())
        json_data["title"] = title.strip()
        json_data["originaltitle"] = originaltitle.strip()

    # 去除标题中的番号
    if number != title and title.startswith(number):
        title = title.replace(number, "").strip()
        json_data["title"] = title
    if number != originaltitle and originaltitle.startswith(number):
        originaltitle = originaltitle.replace(number, "").strip()
        json_data["originaltitle"] = originaltitle

    # 去除标题中的/
    json_data["title"] = json_data["title"].replace("/", "#").strip(" -")
    json_data["originaltitle"] = json_data["originaltitle"].replace("/", "#").strip(" -")

    # 去除素人番号前缀数字
    if "del_num" in fields_rule:
        temp_n = re.findall(r"\d{3,}([a-zA-Z]+-\d+)", number)
        if temp_n:
            json_data["number"] = temp_n[0]
            json_data["letters"] = get_number_letters(json_data["number"])

    if number.endswith("Z"):
        json_data["number"] = json_data["number"][:-1] + "z"
    return json_data


def show_movie_info(json_data: ShowData):
    if not config.show_data_log:  # 调试模式打开时显示详细日志
        return
    for key in ManualConfig.SHOW_KEY:
        value = json_data.get(key)
        if not value:
            continue
        if key == "outline" or key == "originalplot" and len(value) > 100:
            value = str(value)[:98] + "……（略）"
        elif key == "has_sub":
            value = "中文字幕"
        elif key == "actor" and "actor_all," in config.nfo_include_new:
            value = json_data["all_actor"]
        LogBuffer.log().write("\n     " + "%-13s" % key + ": " + str(value))


async def get_video_size(json_data: GetVideoSizeContext, file_path: str):
    # 获取本地分辨率 同时获取视频编码格式
    definition = ""
    height = 0
    hd_get = config.hd_get
    if await aiofiles.os.path.islink(file_path):
        if "symlink_definition" in config.no_escape:
            file_path = await read_link_async(file_path)
        else:
            hd_get = "path"
    codec_fourcc = ""
    if hd_get == "video":
        try:
            height, codec_fourcc = await asyncio.to_thread(get_video_metadata, file_path)
        except Exception as e:
            signal.show_log_text(f" 🔴 无法获取视频分辨率! 文件地址: {file_path}  错误信息: {e}")
    elif hd_get == "path":
        file_path_temp = file_path.upper()
        if "8K" in file_path_temp:
            height = 4000
        elif "4K" in file_path_temp or "UHD" in file_path_temp:
            height = 2000
        elif "1440P" in file_path_temp or "QHD" in file_path_temp:
            height = 1440
        elif "1080P" in file_path_temp or "FHD" in file_path_temp:
            height = 1080
        elif "960P" in file_path_temp:
            height = 960
        elif "720P" in file_path_temp or "HD" in file_path_temp:
            height = 720

    hd_name = config.hd_name
    if not height:
        pass
    elif height >= 4000:
        definition = "8K" if hd_name == "height" else "UHD8"
    elif height >= 2000:
        definition = "4K" if hd_name == "height" else "UHD"
    elif height >= 1400:
        definition = "1440P" if hd_name == "height" else "QHD"
    elif height >= 1000:
        definition = "1080P" if hd_name == "height" else "FHD"
    elif height >= 900:
        definition = "960P" if hd_name == "height" else "HD"
    elif height >= 700:
        definition = "720P" if hd_name == "height" else "HD"
    elif height >= 500:
        definition = "540P" if hd_name == "height" else "qHD"
    elif height >= 400:
        definition = "480P"
    elif height >= 300:
        definition = "360P"
    elif height >= 100:
        definition = "144P"
    json_data["definition"] = definition

    if definition in ["4K", "8K", "UHD", "UHD8"]:
        json_data["_4K"] = "-" + definition

    # 去除标签中的分辨率率，使用本地读取的实际分辨率
    remove_key = ["144P", "360P", "480P", "540P", "720P", "960P", "1080P", "1440P", "2160P", "4K", "8K"]
    tag = json_data["tag"]
    for each_key in remove_key:
        tag = tag.replace(each_key, "").replace(each_key.lower(), "")
    tag_list = re.split(r"[,，]", tag)
    new_tag_list = []
    [new_tag_list.append(i) for i in tag_list if i]
    if definition and "definition" in config.tag_include:
        new_tag_list.insert(0, definition)
        if hd_get == "video" and codec_fourcc:
            new_tag_list.insert(0, codec_fourcc.upper())  # 插入编码格式
    json_data["tag"] = "，".join(new_tag_list)
    return json_data


def show_data_result(json_data: ShowResultInput, start_time: float):
    if json_data["title"] == "":
        LogBuffer.log().write(
            f"\n 🌐 [website] {LogBuffer.req().get().strip('-> ')}"
            f"\n{LogBuffer.info().get().strip()}"
            f"\n 🔴 Data failed!({get_used_time(start_time)}s)"
        )
        return False
    else:
        if config.show_web_log:  # 字段刮削过程
            LogBuffer.log().write(f"\n 🌐 [website] {LogBuffer.req().get().strip('-> ')}")
        try:
            LogBuffer.log().write("\n" + LogBuffer.info().get().strip(" ").strip("\n"))
        except Exception:
            signal.show_log_text(traceback.format_exc())
        if config.show_from_log:  # 字段来源信息
            if json_data["fields_info"]:
                LogBuffer.log().write("\n" + json_data["fields_info"].strip(" ").strip("\n"))
        LogBuffer.log().write(f"\n 🍀 Data done!({get_used_time(start_time)}s)")
        return True


def render_name_template(
    template: str,
    file_path: str,
    json_data: TemplateInput,
    show_4k: bool,
    show_cnword: bool,
    show_moword: bool,
    should_escape_result: bool,
):
    """
    将模板字符串替换成实际值

    :param template: 设置——命名——视频命名规则 下的三个模板字符串
    :param file_path: 当前文件的完整路径，用于替换filename字段
    :param should_escape_result: 作为文件名/文件夹名时需要去掉一些特殊字符，作为nfo的<title>时则不用
    """
    folder_path, file_full_name = split_path(file_path)  # 当前文件的目录和文件名
    filename = os.path.splitext(file_full_name)[0]

    # 获取文件信息
    destroyed = json_data["destroyed"]
    leak = json_data["leak"]
    wuma = json_data["wuma"]
    youma = json_data["youma"]
    m_word = destroyed + leak + wuma + youma
    c_word = json_data["c_word"]
    title = json_data["title"]
    originaltitle = json_data["originaltitle"]
    studio = json_data["studio"]
    publisher = json_data["publisher"]
    year = json_data["year"]
    outline = json_data["outline"]
    runtime = json_data["runtime"]
    director = json_data["director"]
    actor = json_data["actor"]
    release = json_data["release"]
    number = json_data["number"]
    series = json_data["series"]
    mosaic = json_data["mosaic"]
    definition = json_data["definition"]
    letters = json_data["letters"]

    # 是否勾选文件名添加4k标识
    temp_4k = ""
    if show_4k:
        definition = json_data["definition"]
        if definition == "8K" or definition == "UHD8" or definition == "4K" or definition == "UHD":
            temp_definition = definition.replace("UHD8", "UHD")
            temp_4k = f"-{temp_definition}"
    # 判断是否勾选文件名添加字幕标识
    cnword = c_word
    if not show_cnword:
        c_word = ""
    # 判断是否勾选文件名添加版本标识
    moword = m_word
    if not show_moword:
        m_word = ""
    # 判断后缀字段顺序
    suffix_sort_list = config.suffix_sort.split(",")
    for each in suffix_sort_list:
        # "mosaic" 已在ConfigSchema.init()中替换为 "moword"
        if each == "moword":
            number += m_word
        elif each == "cnword":
            number += c_word
        elif each == "definition":
            number += temp_4k
    # 生成number
    first_letter = get_number_first_letter(number)
    # 处理异常情况
    score = str(json_data["score"])
    if not series:
        series = "未知系列"
    if not actor:
        actor = config.actor_no_name
    if not year:
        year = "0000"
    if not score:
        score = "0.0"
    release = get_new_release(release, config.release_rule)
    # 获取演员
    first_actor = actor.split(",").pop(0)
    all_actor = deal_actor_more(json_data["all_actor"])
    actor = deal_actor_more(actor)

    # 替换字段里的文件夹分隔符
    if should_escape_result:
        fields = [originaltitle, title, number, director, actor, release, series, studio, publisher, cnword, outline]
        for i in range(len(fields)):
            fields[i] = fields[i].replace("/", "-").replace("\\", "-").strip(". ")
        originaltitle, title, number, director, actor, release, series, studio, publisher, cnword, outline = fields

    # 更新4k
    if definition == "8K" or definition == "UHD8" or definition == "4K" or definition == "UHD":
        temp_4k = definition.replace("UHD8", "UHD")
    # 替换文件名
    repl_list = [
        ["4K", temp_4k.strip("-")],
        ["originaltitle", originaltitle],
        ["title", title],
        ["outline", outline],
        ["number", number],
        ["first_actor", first_actor],
        ["all_actor", all_actor],
        ["actor", actor],
        ["release", release],
        ["year", str(year)],
        ["runtime", str(runtime)],
        ["director", director],
        ["series", series],
        ["studio", studio],
        ["publisher", publisher],
        ["mosaic", mosaic],
        ["definition", definition.replace("UHD8", "UHD")],
        ["cnword", cnword],
        ["moword", moword],
        ["first_letter", first_letter],
        ["letters", letters],
        ["filename", filename],
        ["wanted", str(json_data["wanted"])],
        ["score", str(score)],
    ]

    # 国产使用title作为number会出现重复，此处去除title，避免重复(需要注意titile繁体情况)
    if not number:
        number = title
    # 默认emby视频标题配置为 [number title]，国产重复时需去掉一个，去重需注意空格也应一起去掉，否则国产的nfo标题中会多一个空格
    # 读取nfo title信息会去掉前面的number和空格以保留title展示出来，同时number和标题一致时，去掉number的逻辑变成去掉整个标题导致读取失败
    if number == title and "number" in template and "title" in template:
        template = template.replace("originaltitle", "").replace("title", "").strip()

    rendered_name = template
    for each_key in repl_list:
        rendered_name = rendered_name.replace(each_key[0], each_key[1])
    return rendered_name, template, number, originaltitle, outline, title
