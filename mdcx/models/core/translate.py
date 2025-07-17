import asyncio
import hashlib
import random
import re
import time
import traceback
import urllib
from typing import Literal, Optional, Union, cast

import langid
import zhconv

from mdcx.config.manager import config
from mdcx.config.resources import resources
from mdcx.models.base.number import get_number_letters
from mdcx.models.core.flags import Flags
from mdcx.models.core.web import get_actorname, get_yesjav_title, google_translate_async
from mdcx.models.json_data import JsonData
from mdcx.models.log_buffer import LogBuffer
from mdcx.signals import signal
from mdcx.utils import get_used_time, remove_repeat

deepl_result = {}
REGEX_KANA = re.compile(r"[\u3040-\u30ff]")  # 平假名/片假名


async def youdao_translate_async(title: str, outline: str):
    url = "https://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule"
    msg = f"{title}\n{outline}"
    lts = str(int(time.time() * 1000))
    salt = lts + str(random.randint(0, 10))
    sign = hashlib.md5(("fanyideskweb" + msg + salt + "Ygy_4c=r#e#4EX^NUGUc5").encode("utf-8")).hexdigest()

    data = {
        "i": msg,
        "from": "AUTO",
        "to": "zh-CHS",
        "smartresult": "dict",
        "client": "fanyideskweb",
        "salt": salt,
        "sign": sign,
        "lts": lts,
        "bv": "c6b8c998b2cbaa29bd94afc223bc106c",
        "doctype": "json",
        "version": "2.1",
        "keyfrom": "fanyi.web",
        "ue": "UTF-8",
        "typoResult": "true",
        "action": "FY_BY_CLICKBUTTION",
    }
    headers = {
        "Cookie": random.choice(
            [
                "OUTFOX_SEARCH_USER_ID=833904829@10.169.0.84",
                "OUTFOX_SEARCH_USER_ID=-10218418@11.136.67.24;",
                "OUTFOX_SEARCH_USER_ID=1989505748@10.108.160.19;",
                "OUTFOX_SEARCH_USER_ID=2072418438@218.82.240.196;",
                "OUTFOX_SEARCH_USER_ID=1768574849@220.181.76.83;",
                "OUTFOX_SEARCH_USER_ID=-2153895048@10.168.8.76;",
            ]
        ),
        "Referer": "https://fanyi.youdao.com/?keyfrom=dict2.top",
    }
    headers_o = config.headers
    headers.update(headers_o)
    res, error = await config.async_client.post_json(url, data=data, headers=headers)
    if res is None:
        return title, outline, f"请求失败！可能是被封了，可尝试更换代理！错误：{error}"
    else:
        res = cast(dict, res)
        translateResult = res.get("translateResult")
        if not translateResult:
            return title, outline, f"返回数据未找到翻译结果！返回内容：{res}"
        else:
            list_count = len(translateResult)
            if list_count:
                i = 0
                if title:
                    i = 1
                    title_result_list = translateResult[0]
                    title_list = [a.get("tgt") for a in title_result_list]
                    title_temp = "".join(title_list)
                    if title_temp:
                        title = title_temp
                if outline:
                    outline_temp = ""
                    for j in range(i, list_count):
                        outline_result_list = translateResult[j]
                        outline_list = [a.get("tgt") for a in outline_result_list]
                        outline_temp += "".join(outline_list) + "\n"
                    outline_temp = outline_temp.strip("\n")
                    if outline_temp:
                        outline = outline_temp
    return title, outline.strip("\n"), ""


async def deepl_translate_async(
    title: str,
    outline: str,
    ls: Union[Literal["JA"], Literal["EN"]] = "JA",
):
    """DeepL 翻译接口"""
    r1, r2 = await asyncio.gather(_deepl_translate(title, ls), _deepl_translate(outline, ls))
    if r1 is None or r2 is None:
        return "", "", "DeepL 翻译失败! 查看网络日志以获取更多信息"
    return r1, r2, None


async def _deepl_translate(text: str, source_lang: Union[Literal["JA"], Literal["EN"]] = "JA") -> Optional[str]:
    """调用 DeepL API 翻译文本"""
    if not text:
        return ""

    deepl_key = config.deepl_key
    if not deepl_key:
        return None

    # 确定 API URL, 免费版本的 key 包含 ":fx" 后缀，付费版本的 key 不包含 ":fx" 后缀
    deepl_url = "https://api-free.deepl.com" if ":fx" in deepl_key else "https://api.deepl.com"
    url = f"{deepl_url}/v2/translate"
    # 构造请求头
    headers = {"Content-Type": "application/json", "Authorization": f"DeepL-Auth-Key {deepl_key}"}
    # 构造请求体
    data = {"text": [text], "source_lang": source_lang, "target_lang": "ZH"}
    res, error = await config.async_client.post_json(url, json_data=data, headers=headers)
    if res is None:
        signal.add_log(f"DeepL API 请求失败: {error}")
        return None
    if "translations" in res and len(res["translations"]) > 0:
        return res["translations"][0]["text"]
    else:
        signal.add_log(f"DeepL API 返回数据异常: {res}")
        return None


async def llm_translate_async(title: str, outline: str, target_language: str = "简体中文"):
    r1, r2 = await asyncio.gather(_llm_translate(title, target_language), _llm_translate(outline, target_language))
    if r1 is None or r2 is None:
        return "", "", "LLM 翻译失败! 查看网络日志以获取更多信息"
    return r1, r2, None


async def _llm_translate(text: str, target_language: str = "简体中文") -> Optional[str]:
    """调用 LLM 翻译文本"""
    if not text:
        return ""
    return await config.llm_client.ask(
        model=config.llm_model,
        system_prompt="You are a professional translator.",
        user_prompt=config.llm_prompt.replace("{content}", text).replace("{lang}", target_language),
        temperature=config.llm_temperature,
        max_try=config.llm_max_try,
        log_fn=signal.add_log,
    )


def translate_info(json_data: JsonData):
    xml_info = resources.info_mapping_data
    if len(xml_info) == 0:
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
    tag = json_data["tag"]
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
    if "actor" in tag_include and json_data["actor"]:
        tag = json_data["actor"] + "," + tag
        tag = tag.strip(",")

    # 添加番号前缀
    letters = json_data["letters"]
    if "letters" in tag_include and letters and letters != "未知车牌":
        # 去除素人番号前缀数字
        if "del_num" in fields_rule:
            temp_n = re.findall(r"\d{3,}([a-zA-Z]+-\d+)", json_data["number"])
            if temp_n:
                letters = get_number_letters(temp_n[0])
                json_data["letters"] = letters
                json_data["number"] = temp_n[0]
        tag = letters + "," + tag
        tag = tag.strip(",")

    # 添加字幕、马赛克信息到tag中
    has_sub = json_data["has_sub"]
    mosaic = json_data["mosaic"]
    if has_sub and "cnword" in tag_include:
        tag += ",中文字幕"
    if mosaic and "mosaic" in tag_include:
        tag += "," + mosaic

    # 添加系列、制作、发行信息到tag中
    series = json_data["series"]
    studio = json_data["studio"]
    publisher = json_data["publisher"]
    director = json_data["director"]
    if not studio and publisher:
        studio = publisher
    if not publisher and studio:
        publisher = studio

    # 系列
    if series:  # 为空时会匹配所有
        if series_translate:  # 映射
            info_data = resources.get_info_data(series)
            series = info_data.get(series_language)
        if series and "series" in tag_include:  # 写nfo
            nfo_tag_series = config.nfo_tag_series.replace("series", series)
            if nfo_tag_series:
                tag += f",{nfo_tag_series}"

    # 片商
    if studio:
        if studio_translate:
            info_data = resources.get_info_data(studio)
            studio = info_data.get(studio_language)
        if studio and "studio" in tag_include:
            nfo_tag_studio = config.nfo_tag_studio.replace("studio", studio)
            if nfo_tag_studio:
                tag += f",{nfo_tag_studio}"

    # 发行
    if publisher:
        if publisher_translate:
            info_data = resources.get_info_data(publisher)
            publisher = info_data.get(publisher_language)
        if publisher and "publisher" in tag_include:
            nfo_tag_publisher = config.nfo_tag_publisher.replace("publisher", publisher)
            if nfo_tag_publisher:
                tag += f",{nfo_tag_publisher}"

    # 导演
    if director:
        if director_translate:
            info_data = resources.get_info_data(director)
            director = info_data.get(director_language)

    if tag_language == "zh_cn":
        tag = zhconv.convert(tag, "zh-cn")
    else:
        tag = zhconv.convert(tag, "zh-hant")

    # tag去重/去空/排序
    tag = remove_repeat(tag)

    json_data["tag"] = tag.strip(",")
    json_data["series"] = series
    json_data["studio"] = studio
    json_data["publisher"] = publisher
    json_data["director"] = director
    return json_data


async def translate_actor(json_data: JsonData):
    # 网络请求真实的演员名字
    actor_realname = config.actor_realname
    mosaic = json_data["mosaic"]
    number = json_data["number"]

    # 非读取模式，勾选了使用真实名字时; 读取模式，勾选了允许更新真实名字时
    if actor_realname:
        start_time = time.time()
        if mosaic != "国产" and (
            number.startswith("FC2") or number.startswith("SIRO") or re.search(r"\d{3,}[A-Z]{3,}-", number)
        ):
            result, temp_actor = await get_actorname(json_data["number"])
            if result:
                actor: str = json_data["actor"]
                all_actor: str = json_data["all_actor"]
                actor_list: list = all_actor.split(",")
                json_data["actor"] = temp_actor
                # 从actor_list中循环查找元素是否包含字符串temp_actor，有则替换
                for item in actor_list:
                    if item.find(actor) != -1:
                        actor_list[actor_list.index(item)] = temp_actor
                json_data["all_actor"] = ",".join(actor_list)

                LogBuffer.log().write(
                    f"\n 👩🏻 Av-wiki done! Actor's real Japanese name is '{temp_actor}' ({get_used_time(start_time)}s)"
                )
            else:
                LogBuffer.log().write(f"\n 🔴 Av-wiki failed! {temp_actor} ({get_used_time(start_time)}s)")

    # 如果不映射，返回
    if not config.actor_translate:
        return json_data

    # 映射表数据加载失败，返回
    xml_actor = resources.actor_mapping_data
    if len(xml_actor) == 0:
        return json_data

    # 未知演员，返回
    actor = json_data["actor"]
    if "actor_all," in config.nfo_include_new:
        actor = json_data["all_actor"]
    if actor == config.actor_no_name:
        return json_data

    # 查询映射表
    actor_list = actor.split(",")
    actor_new_list = []
    actor_href_list = []
    actor_language = config.actor_language
    for each_actor in actor_list:
        if each_actor:
            actor_data = resources.get_actor_data(each_actor)
            new_actor = actor_data.get(actor_language)
            if new_actor and not REGEX_KANA.search(new_actor):
                if actor_language == "zh_cn":
                    new_actor = zhconv.convert(new_actor, "zh-cn")
                elif actor_language == "zh_tw":
                    new_actor = zhconv.convert(new_actor, "zh-hant")
            if new_actor not in actor_new_list:
                actor_new_list.append(new_actor)
                if actor_data.get("href"):
                    actor_href_list.append(actor_data.get("href"))
    json_data["actor"] = ",".join(actor_new_list)
    if "actor_all," in config.nfo_include_new:
        json_data["all_actor"] = ",".join(actor_new_list)

    # 演员主页
    if actor_href_list:
        json_data["actor_href"] = actor_href_list[0]
    elif json_data["actor"]:
        json_data["actor_href"] = "https://javdb.com/search?f=actor&q=" + urllib.parse.quote(
            json_data["actor"].split(",")[0]
        )  # url转码，避免乱码

    return json_data


async def translate_title_outline(json_data: JsonData, movie_number: str):
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
    json_data_title_language = langid.classify(json_data["title"])[0]

    # 处理title
    if title_language != "jp":
        movie_title = ""

        # 匹配本地高质量标题(色花标题数据)
        if title_sehua_zh or (json_data_title_language == "ja" and title_sehua):
            start_time = time.time()
            try:
                movie_title = resources.sehua_title_data.get(movie_number)
            except Exception:
                signal.show_traceback_log(traceback.format_exc())
                signal.show_log_text(traceback.format_exc())
            if movie_title:
                json_data["title"] = movie_title
                LogBuffer.log().write(f"\n 🌸 Sehua title done!({get_used_time(start_time)}s)")

        # 匹配网络高质量标题（yesjav， 可在线更新）
        if not movie_title and title_yesjav and json_data_title_language == "ja":
            start_time = time.time()
            movie_title = await get_yesjav_title(movie_number)
            if movie_title and langid.classify(movie_title)[0] != "ja":
                json_data["title"] = movie_title
                LogBuffer.log().write(f"\n 🆈 Yesjav title done!({get_used_time(start_time)}s)")

        # 使用json_data数据
        if not movie_title and title_translate and json_data_title_language == "ja":
            trans_title = json_data["title"]

    # 处理outline
    if json_data["outline"] and outline_language != "jp":
        if outline_translate and langid.classify(json_data["outline"])[0] == "ja":
            trans_outline = json_data["outline"]

    # 翻译
    if Flags.translate_by_list:
        if (trans_title and title_translate) or (trans_outline and outline_translate):
            start_time = time.time()
            translate_by_list = Flags.translate_by_list.copy()
            if not json_data["cd_part"]:
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
                        json_data["title"] = t
                    if o:
                        json_data["outline"] = o
                    LogBuffer.log().write(f"\n 🍀 Translation done!({each.capitalize()})({get_used_time(start_time)}s)")
                    json_data["outline_from"] = each
                    return "break"

            res = await asyncio.gather(*[_task(each) for each in translate_by_list])
            for r in res:
                if r == "break":
                    break
            else:
                translate_by = translate_by.strip(",").capitalize()
                LogBuffer.log().write(
                    f"\n 🔴 Translation failed! {translate_by} 不可用！({get_used_time(start_time)}s)"
                )

    # 简繁转换
    if title_language == "zh_cn":
        json_data["title"] = zhconv.convert(json_data["title"], "zh-cn")
    elif title_language == "zh_tw":
        json_data["title"] = zhconv.convert(json_data["title"], "zh-hant")
        json_data["mosaic"] = zhconv.convert(json_data["mosaic"], "zh-hant")

    if outline_language == "zh_cn":
        json_data["outline"] = zhconv.convert(json_data["outline"], "zh-cn")
    elif outline_language == "zh_tw":
        json_data["outline"] = zhconv.convert(json_data["outline"], "zh-hant")

    return json_data
