"""
爬虫控制, 调用 models.crawlers 中各个网站爬虫
"""

import asyncio
import re
from typing import Callable, TypedDict

import langid

from mdcx.config.manager import config
from mdcx.config.manual import ManualConfig
from mdcx.crawlers import (
    airav,
    airav_cc,
    avsex,
    avsox,
    cableav,
    cnmdb,
    dahlia,
    dmm,
    faleno,
    fantastica,
    fc2,
    fc2club,
    fc2hub,
    fc2ppvdb,
    freejavbt,
    getchu,
    getchu_dmm,
    giga,
    hdouban,
    hscangku,
    iqqtv_new,
    jav321,
    javbus,
    javday,
    javdb,
    javlibrary_new,
    kin8,
    love6,
    lulubar,
    madouqu,
    mdtv,
    mgstage,
    mmtv,
    mywife,
    official,
    prestige,
    theporndb,
    xcity,
)
from mdcx.models.enums import FileMode
from mdcx.models.flags import Flags
from mdcx.models.json_data import JsonData, new_json_data
from mdcx.models.log_buffer import LogBuffer
from mdcx.number import get_number_letters, is_uncensored


class CrawlersResult(TypedDict):
    """
    爬虫结果类型，包含所有可能的元数据字段. (注释由 AI 生成, 仅供参考)
    """

    # 基本信息
    number: str  # 番号
    short_number: str  # 素人番号的短形式（不带前缀数字）
    title: str  # 标题
    originaltitle: str  # 原始标题（日文）
    originaltitle_amazon: str  # 用于 Amazon 搜索的原始标题
    outline: str  # 简介
    originalplot: str  # 原始简介（日文）
    # 演员信息
    actor: str  # 演员名称，逗号分隔
    all_actor: str  # 所有来源的演员名称
    all_actor_photo: dict  # 演员照片信息
    actor_amazon: list[str]  # 用于 Amazon 搜索的演员名称
    amazon_orginaltitle_actor: str  # 用于 Amazon 搜索的原始标题中的演员
    # 元数据信息
    tag: str  # 标签，逗号分隔
    release: str  # 发行日期
    year: str  # 发行年份
    runtime: str  # 片长（分钟）
    score: str  # 评分
    series: str  # 系列
    director: str  # 导演
    studio: str  # 制作商
    publisher: str  # 发行商
    # 图片与视频
    thumb: str  # 缩略图URL
    thumb_list: list  # 所有来源的缩略图URL列表
    poster: str  # 海报URL
    extrafanart: list[str]  # 额外剧照URL列表
    trailer: str  # 预告片URL
    image_download: bool  # 是否需要下载图片
    # 马赛克类型
    mosaic: str
    letters: str  # 番号字母部分
    # 标志信息
    has_sub: bool  # 是否有字幕
    c_word: str  # 中文字幕标识
    leak: str  # 是否是无码流出
    wuma: str  # 是否是无码
    youma: str  # 是否是有码
    cd_part: str  # CD分集信息
    destroyed: str  # 是否是无码破解
    version: int  # 版本信息
    # 文件路径与指定信息
    file_path: str  # 文件路径
    appoint_number: str  # 指定番号
    appoint_url: str  # 指定URL
    # 其他信息
    javdbid: str  # JavDB ID
    fields_info: str  # 字段来源信息
    naming_media: str  # 媒体命名规则
    naming_file: str  # 文件命名规则
    folder_name: str  # 文件夹命名规则
    # 字段来源信息
    poster_from: str
    thumb_from: str
    extrafanart_from: str
    trailer_from: str
    outline_from: str
    website_name: str  # 使用的网站名称


CRAWLER_FUNCS: dict[str, Callable] = {
    "7mmtv": mmtv.main,
    "airav_cc": airav_cc.main,  # lang
    "airav": airav.main,  # lang
    "avsex": avsex.main,
    "avsox": avsox.main,
    "cableav": cableav.main,
    "cnmdb": cnmdb.main,
    "dahlia": dahlia.main,
    "dmm": dmm.main,
    "faleno": faleno.main,
    "fantastica": fantastica.main,
    "fc2": fc2.main,
    "fc2club": fc2club.main,
    "fc2hub": fc2hub.main,
    "fc2ppvdb": fc2ppvdb.main,
    "freejavbt": freejavbt.main,
    "getchu_dmm": getchu_dmm.main,
    "getchu": getchu.main,
    "giga": giga.main,
    "hdouban": hdouban.main,
    "hscangku": hscangku.main,
    "iqqtv": iqqtv_new.main,  # lang
    "jav321": jav321.main,
    "javbus": javbus.main,
    "javday": javday.main,
    "javdb": javdb.main,
    "javlibrary": javlibrary_new.main,  # lang
    "kin8": kin8.main,
    "love6": love6.main,
    "lulubar": lulubar.main,
    "madouqu": madouqu.main,
    "mdtv": mdtv.main,
    "mgstage": mgstage.main,
    "mywife": mywife.main,
    "official": official.main,
    "prestige": prestige.main,
    "theporndb": theporndb.main,
    "xcity": xcity.main,
}

MULTI_LANGUAGE_WEBSITES = [  # 支持多语言, language 参数有意义
    "airav_cc",
    "airav",
    "iqqtv",
    "javlibrary",
]


def clean_list(raw: list[str]) -> list[str]:
    """清理列表，去除空值和重复值, 保持原有顺序"""
    cleaned = []
    for item in raw:
        if item.strip() and item not in cleaned:
            cleaned.append(item.strip())
    return cleaned


def _deal_some_list(field: str, website: str, same_list: list[str]) -> list[str]:
    if website not in same_list:
        same_list.append(website)
    if field in ["title", "outline", "thumb", "poster", "trailer", "extrafanart"]:
        same_list.remove(website)
        same_list.insert(0, website)
    elif field in ["tag", "score", "director", "series"]:
        same_list.remove(website)
    return same_list


async def _call_crawler(
    task_input: JsonData,
    website: str,
    language: str,
    org_language: str,
    timeout: int = 30,
) -> dict[str, dict[str, dict]]:
    """
    获取某个网站数据
    """
    appoint_number = task_input["appoint_number"]
    appoint_url = task_input["appoint_url"]
    file_path = task_input["file_path"]
    number = task_input["number"]
    mosaic = task_input["mosaic"]
    short_number = task_input["short_number"]

    # 259LUXU-1111， mgstage 和 avsex 之外使用 LUXU-1111（素人番号时，short_number有值，不带前缀数字；反之，short_number为空)
    if short_number and website != "mgstage" and website != "avsex":
        number = short_number

    # 获取爬虫函数
    crawler_func = CRAWLER_FUNCS.get(website, javdb.main)

    # 准备参数
    kwargs = {
        "number": number,
        "appoint_url": appoint_url,
        "language": language,
        "file_path": file_path,
        "appoint_number": appoint_number,
        "mosaic": mosaic,
        "short_number": short_number,
        "org_language": org_language,
    }

    try:
        # 对爬虫函数调用添加超时限制
        return await asyncio.wait_for(crawler_func(**kwargs), timeout=timeout)
    except asyncio.TimeoutError:
        # 返回空结果
        return {website: {language or "jp": {"title": "", "thumb": "", "website": ""}}}


async def _call_crawlers(
    task_input: JsonData,
    number_website_list: list[str],
) -> CrawlersResult:
    """
    获取一组网站的数据：按照设置的网站组，请求各字段数据，并返回最终的数据
    采用按需请求策略：仅请求必要的网站，失败时才请求下一优先级网站
    """
    number = task_input["number"]
    short_number = task_input["short_number"]
    scrape_like = config.scrape_like
    none_fields = config.none_fields  # 不单独刮削的字段

    def get_field_websites(field: str) -> list[str]:
        """
        获取指定字段的来源优先级列表

        field_websites = (config.{field}_website - config.{field}_website_exclude) ∩ (number_website_list)
        """
        # 指定字段网站列表
        field_no_zh = field.replace("_zh", "")  # 去除 _zh 后缀的字段名
        field_list = clean_list(getattr(config, f"{field}_website", "").split(","))
        # 与指定类型网站列表取交集
        field_list = [i for i in field_list if i in number_website_list]
        if "official" in config.website_set:  # 优先使用官方网站
            field_list.insert(0, "official")
        # 指定字段排除网站列表
        field_ex_list = clean_list(getattr(config, f"{field_no_zh}_website_exclude", "").split(","))
        # 所有设定的本字段来源失败时, 是否继续使用类型网站补全
        include_others = field == "title" or field in config.whole_fields
        if include_others and field != "trailer":  # 取剩余未相交网站， trailer 不取未相交网站
            field_list.extend([i for i in number_website_list if i not in field_list])
        # 排除指定网站
        field_list = [i for i in field_list if i not in field_ex_list]
        # 特殊处理
        # mgstage 素人番号检查
        if short_number:
            not_frist_field_list = ["title", "actor"]  # 这些字段以外，素人把 mgstage 放在第一位
            if field not in not_frist_field_list and "mgstage" in field_list:
                field_list.remove("mgstage")
                field_list.insert(0, "mgstage")
        # faleno.jp 番号检查 dldss177 dhla009
        elif re.findall(r"F[A-Z]{2}SS", number):
            field_list = _deal_some_list(field, "faleno", field_list)
        # dahlia-av.jp 番号检查
        elif number.startswith("DLDSS") or number.startswith("DHLA"):
            field_list = _deal_some_list(field, "dahlia", field_list)
        # fantastica 番号检查 FAVI、FAAP、FAPL、FAKG、FAHO、FAVA、FAKY、FAMI、FAIT、FAKA、FAMO、FASO、FAIH、FASH、FAKS、FAAN
        elif (
            re.search(r"FA[A-Z]{2}-?\d+", number.upper())
            or number.upper().startswith("CLASS")
            or number.upper().startswith("FADRV")
            or number.upper().startswith("FAPRO")
            or number.upper().startswith("FAKWM")
            or number.upper().startswith("PDS")
        ):
            field_list = _deal_some_list(field, "fantastica", field_list)
        return field_list

    # 获取使用的网站
    all_fields = [f for f in ManualConfig.CONFIG_DATA_FIELDS if f not in none_fields]  # 去除不专门刮削的字段
    if scrape_like == "speed":  # 快速模式
        all_field_websites = {field: number_website_list for field in all_fields}
    else:  # 全部模式
        # 各字段网站列表
        all_field_websites = {field: get_field_websites(field) for field in all_fields}
        if config.outline_language == "jp" and "outline_zh" in all_field_websites:
            del all_field_websites["outline_zh"]
        if config.title_language == "jp" and "title_zh" in all_field_websites:
            del all_field_websites["title_zh"]

    # 各字段语言, 未指定则默认为 "any"
    all_field_languages = {field: getattr(config, f"{field}_language", "any") for field in all_fields}
    all_field_languages["title_zh"] = config.title_language
    all_field_languages["outline_zh"] = config.outline_language

    # 处理配置项中没有的字段
    # originaltitle 的网站优先级同 title, 语言为 jp
    all_field_websites["originaltitle"] = all_field_websites.get("title", number_website_list)
    all_field_languages["originaltitle"] = "jp"
    all_field_websites["originalplot"] = all_field_websites.get("outline", number_website_list)
    all_field_languages["originalplot"] = "jp"

    # 各字段的取值优先级 (网站, 语言) 对
    all_field_website_lang_pairs: dict[str, list[tuple[str, str]]] = {}
    for field, websites in all_field_websites.items():
        language = all_field_languages[field]
        all_field_website_lang_pairs[field] = []
        for website in websites:
            pair = (website, language)
            if website not in MULTI_LANGUAGE_WEBSITES:
                pair = (website, "")  # 单语言网站, 语言参数无意义
            all_field_website_lang_pairs[field].append(pair)

    # 缓存已请求的网站结果
    all_res: dict[tuple[str, str], dict] = {}

    reduced: CrawlersResult = new_json_data()  # 验证 JsonData 和 CrawlersResult 一致, 初始化所有字段
    reduced.update(task_input)  # 复制输入数据

    # 无优先级设置的字段的默认配置
    default_website_lang_pairs = [
        (w, "") if w not in MULTI_LANGUAGE_WEBSITES else (w, "any") for w in number_website_list
    ]

    # 按字段分别处理，每个字段按优先级尝试获取
    for field in ManualConfig.CRAWLER_DATA_FIELDS:  # 与 CONFIG_DATA_FIELDS 不完全一致
        # 获取该字段的优先级列表
        sources = all_field_website_lang_pairs.get(field, default_website_lang_pairs)

        # 如果title_language不是jp，则允许从title_zh来源获取title
        if field == "title" and config.title_language != "jp":
            sources = sources + all_field_website_lang_pairs.get("title_zh", [])
        # 如果outline_language不是jp，则允许从outline_zh来源获取outline
        elif field == "outline" and config.outline_language != "jp":
            sources = sources + all_field_website_lang_pairs.get("outline_zh", [])

        LogBuffer.info().write(
            f"\n\n    🙋🏻‍ {field} \n    ====================================\n"
            f"    🌐 来源优先级：{' -> '.join(i[0] + f'({i[1]})' * bool(i[1]) for i in sources)}"
        )

        # 按优先级依次尝试获取字段值
        for website, language in sources:
            # 检查是否已经请求过该网站
            key = (website, language)

            # 如果网站不支持多语言，标准化key
            if website not in MULTI_LANGUAGE_WEBSITES:
                key = (website, "")

            # 如果已有该网站数据，直接使用
            if key in all_res:
                site_data = all_res[key]
            else:
                # 处理多语言网站的特殊情况
                if website in MULTI_LANGUAGE_WEBSITES:
                    # 对于多语言网站，检查是否需要请求jp语言
                    if language == "any" and all((website, lang) not in all_res for lang in ["jp", "zh_cn", "zh_tw"]):
                        # 添加一个jp语言的请求
                        language = "jp"
                        key = (website, language)

                    # 对于iqqtv，如果请求中文时已经有jp数据，可以跳过jp请求
                    if (
                        website == "iqqtv"
                        and language == "jp"
                        and any((website, lang) in all_res for lang in ["zh_cn", "zh_tw"])
                    ):
                        continue

                    # 跳过any语言的请求，因为会通过具体语言请求
                    if language == "any":
                        continue

                # 如果网站数据尚未请求，则进行请求
                try:
                    web_data = await _call_crawler(task_input, website, language, config.title_language)

                    # 处理并保存结果
                    if website not in MULTI_LANGUAGE_WEBSITES:
                        # 单语言网站, 只取第一个语言的数据
                        all_res[(website, "")] = next(iter(web_data[website].values()))
                    else:
                        # 多语言网站，保存所有语言的数据
                        for lang, data in web_data[website].items():
                            all_res[(website, lang)] = data
                            # 同时为any语言添加一份数据
                            if (website, "any") not in all_res:
                                all_res[(website, "any")] = data

                    # 更新key以便后续使用
                    if website not in MULTI_LANGUAGE_WEBSITES:
                        key = (website, "")
                except Exception as e:
                    LogBuffer.info().write(f"\n    🔴 {website} (异常: {str(e)})")
                    continue

            # 获取网站数据
            site_data = all_res.get(key, {})
            if not site_data or not site_data.get("title", "") or not site_data.get(field, ""):
                LogBuffer.info().write(f"\n    🔴 {website} (失败)")
                continue

            # 语言检测逻辑
            if config.scrape_like != "speed":
                if field in ["title", "outline", "originaltitle", "originalplot"]:
                    lang = all_field_languages.get(field, "jp")
                    if website in ["airav_cc", "iqqtv", "airav", "avsex", "javlibrary", "lulubar"]:  # why?
                        if langid.classify(site_data[field])[0] != "ja":
                            if lang == "jp":
                                LogBuffer.info().write(f"\n    🔴 {website} (失败，检测为非日文，跳过！)")
                                continue
                        elif lang != "jp":
                            LogBuffer.info().write(f"\n    🔴 {website} (失败，检测为日文，跳过！)")
                            continue

            # 添加来源信息
            if field in ["poster", "thumb", "extrafanart", "trailer", "outline"]:
                reduced[field + "_from"] = website

            if field == "poster":
                reduced["image_download"] = site_data["image_download"]
            elif field == "thumb":
                # 记录所有 thumb url 以便后续下载
                reduced["thumb_list"].append((website, site_data["thumb"]))
            elif field == "actor":
                if isinstance(site_data["actor"], list):
                    # 处理 actor 为列表的情况
                    site_data["actor"] = ",".join(site_data["actor"])
                reduced["all_actor"] = reduced.get("all_actor", site_data["actor"])
                reduced["all_actor_photo"] = reduced.get("all_actor_photo", site_data.get("actor_photo", ""))
                # 记录所有网站的 actor 用于 Amazon 搜图, 因为有的网站 actor 不对
                reduced["actor_amazon"].extend(site_data["actor"].split(","))
            elif field == "originaltitle" and site_data.get("actor", ""):
                reduced["amazon_orginaltitle_actor"] = site_data["actor"].split(",")[0]

            # 保存数据
            reduced[field] = site_data[field]
            reduced["fields_info"] += f"\n     {field:<13}: {website}" + f" ({language})" * bool(language)
            LogBuffer.info().write(f"\n    🟢 {website} (成功)\n     ↳ {reduced[field]}")

            # 找到有效数据，跳出循环继续处理下一个字段
            break
        else:  # 所有来源都无此字段
            reduced["fields_info"] += f"\n     {field:<13}: {'-----'} ({'not found'})"

    # 处理 year
    if reduced.get("year", "") and (r := re.search(r"\d{4}", reduced.get("release", ""))):
        reduced["year"] = r.group()

    # 处理 number：素人影片时使用有数字前缀的number
    if short_number:
        reduced["number"] = number

    # 处理 javdbid
    javdb_key = ("javdb", "")
    reduced["javdbid"] = all_res.get(javdb_key, {}).get("javdbid", "")

    # todo 由于异步, 此处日志混乱. 需移除 LogBuffer.req(), 改为返回日志信息
    reduced["fields_info"] = f"\n 🌐 [website] {LogBuffer.req().get().strip('-> ')}{reduced['fields_info']}"

    return reduced


async def _call_specific_crawler(task_input: JsonData, website: str) -> CrawlersResult:
    file_number = task_input["number"]
    short_number = task_input["short_number"]

    title_language = config.title_language
    org_language = title_language
    outline_language = config.outline_language
    actor_language = config.actor_language
    tag_language = config.tag_language
    series_language = config.series_language
    studio_language = config.studio_language
    publisher_language = config.publisher_language
    director_language = config.director_language
    if website not in ["airav_cc", "iqqtv", "airav", "avsex", "javlibrary", "mdtv", "madouqu", "lulubar"]:
        title_language = "jp"
        outline_language = "jp"
        actor_language = "jp"
        tag_language = "jp"
        series_language = "jp"
        studio_language = "jp"
        publisher_language = "jp"
        director_language = "jp"
    elif website == "mdtv":
        title_language = "zh_cn"
        outline_language = "zh_cn"
        actor_language = "zh_cn"
        tag_language = "zh_cn"
        series_language = "zh_cn"
        studio_language = "zh_cn"
        publisher_language = "zh_cn"
        director_language = "zh_cn"
    web_data = await _call_crawler(task_input, website, title_language, org_language)
    web_data_json = web_data.get(website, {}).get(title_language, {})
    res = task_input.copy()
    res.update(web_data_json)
    if not res["title"]:
        return res
    if outline_language != title_language:
        web_data_json = web_data[website][outline_language]
        if web_data_json["outline"]:
            res["outline"] = web_data_json["outline"]
    if actor_language != title_language:
        web_data_json = web_data[website][actor_language]
        if web_data_json["actor"]:
            res["actor"] = web_data_json["actor"]
    if tag_language != title_language:
        web_data_json = web_data[website][tag_language]
        if web_data_json["tag"]:
            res["tag"] = web_data_json["tag"]
    if series_language != title_language:
        web_data_json = web_data[website][series_language]
        if web_data_json["series"]:
            res["series"] = web_data_json["series"]
    if studio_language != title_language:
        web_data_json = web_data[website][studio_language]
        if web_data_json["studio"]:
            res["studio"] = web_data_json["studio"]
    if publisher_language != title_language:
        web_data_json = web_data[website][publisher_language]
        if web_data_json["publisher"]:
            res["publisher"] = web_data_json["publisher"]
    if director_language != title_language:
        web_data_json = web_data[website][director_language]
        if web_data_json["director"]:
            res["director"] = web_data_json["director"]
    if res["thumb"]:
        res["thumb_list"] = [(website, res["thumb"])]

    # 加入来源信息
    res["outline_from"] = website
    res["poster_from"] = website
    res["thumb_from"] = website
    res["extrafanart_from"] = website
    res["trailer_from"] = website
    # todo
    res["fields_info"] = f"\n 🌐 [website] {LogBuffer.req().get().strip('-> ')}"

    if short_number:
        res["number"] = file_number

    temp_actor = (
        web_data[website]["jp"]["actor"]
        + ","
        + web_data[website]["zh_cn"]["actor"]
        + ","
        + web_data[website]["zh_tw"]["actor"]
    )
    res["actor_amazon"] = []
    [res["actor_amazon"].append(i) for i in temp_actor.split(",") if i and i not in res["actor_amazon"]]
    res["all_actor"] = res["all_actor"] if res.get("all_actor") else web_data_json["actor"]
    res["all_actor_photo"] = res["all_actor_photo"] if res.get("all_actor_photo") else web_data_json["actor_photo"]

    return res


async def _crawl(task_input: JsonData, website_name: str) -> CrawlersResult:  # 从JSON返回元数据
    file_number = task_input["number"]
    file_path = task_input["file_path"]
    short_number = task_input["short_number"]
    appoint_number = task_input["appoint_number"]
    appoint_url = task_input["appoint_url"]
    has_sub = task_input["has_sub"]
    c_word = task_input["c_word"]
    leak = task_input["leak"]
    wuma = task_input["wuma"]
    youma = task_input["youma"]
    cd_part = task_input["cd_part"]
    destroyed = task_input["destroyed"]
    mosaic = task_input["mosaic"]
    version = task_input["version"]
    # task_input["title"] = ""
    # task_input["fields_info"] = ""
    # task_input["all_actor"] = ""
    # task_input["all_actor_photo"] = {}
    # ================================================网站规则添加开始================================================

    if website_name == "all":  # 从全部网站刮削
        # =======================================================================先判断是不是国产，避免浪费时间
        if (
            mosaic == "国产"
            or mosaic == "國產"
            or (re.search(r"([^A-Z]|^)MD[A-Z-]*\d{4,}", file_number) and "MDVR" not in file_number)
            or re.search(r"MKY-[A-Z]+-\d{3,}", file_number)
        ):
            task_input["mosaic"] = "国产"
            website_list = config.website_guochan.split(",")
            res = await _call_crawlers(task_input, website_list)

        # =======================================================================kin8
        elif file_number.startswith("KIN8"):
            website_name = "kin8"
            res = await _call_specific_crawler(task_input, website_name)

        # =======================================================================同人
        elif file_number.startswith("DLID"):
            website_name = "getchu"
            res = await _call_specific_crawler(task_input, website_name)

        # =======================================================================里番
        elif "getchu" in file_path.lower() or "里番" in file_path or "裏番" in file_path:
            website_name = "getchu_dmm"
            res = await _call_specific_crawler(task_input, website_name)

        # =======================================================================Mywife No.1111
        elif "mywife" in file_path.lower():
            website_name = "mywife"
            res = await _call_specific_crawler(task_input, website_name)

        # =======================================================================FC2-111111
        elif "FC2" in file_number.upper():
            file_number_1 = re.search(r"\d{5,}", file_number)
            if file_number_1:
                file_number_1.group()
                website_list = config.website_fc2.split(",")
                res = await _call_crawlers(task_input, website_list)
            else:
                LogBuffer.error().write(f"未识别到FC2番号：{file_number}")
                res = task_input.copy()

        # =======================================================================sexart.15.06.14
        elif re.search(r"[^.]+\.\d{2}\.\d{2}\.\d{2}", file_number) or (
            "欧美" in file_path and "东欧美" not in file_path
        ):
            website_list = config.website_oumei.split(",")
            res = await _call_crawlers(task_input, website_list)

        # =======================================================================无码抓取:111111-111,n1111,HEYZO-1111,SMD-115
        elif mosaic == "无码" or mosaic == "無碼":
            website_list = config.website_wuma.split(",")
            res = await _call_crawlers(task_input, website_list)

        # =======================================================================259LUXU-1111
        elif short_number or "SIRO" in file_number.upper():
            website_list = config.website_suren.split(",")
            res = await _call_crawlers(task_input, website_list)

        # =======================================================================ssni00321
        elif re.match(r"\D{2,}00\d{3,}", file_number) and "-" not in file_number and "_" not in file_number:
            website_list = ["dmm"]
            res = await _call_crawlers(task_input, website_list)

        # =======================================================================剩下的（含匹配不了）的按有码来刮削
        else:
            website_list = config.website_youma.split(",")
            if "official" in config.website_set:  # 优先使用官方网站
                website_list.insert(0, "official")
            res = await _call_crawlers(task_input, website_list)
    else:
        res = await _call_specific_crawler(task_input, website_name)

    # ================================================网站请求结束================================================
    # ======================================超时或未找到返回
    if res["title"] == "":
        return res

    number = res["number"]
    if appoint_number:
        number = appoint_number

    # 马赛克
    if leak:
        res["mosaic"] = "无码流出"
    elif destroyed:
        res["mosaic"] = "无码破解"
    elif wuma:
        res["mosaic"] = "无码"
    elif youma:
        res["mosaic"] = "有码"
    elif mosaic:
        res["mosaic"] = mosaic
    if not res.get("mosaic"):
        if is_uncensored(number):
            res["mosaic"] = "无码"
        else:
            res["mosaic"] = "有码"
    print(number, cd_part, res["mosaic"], LogBuffer.req().get().strip("-> "))

    # 车牌字母
    letters = get_number_letters(number)

    # 原标题，用于amazon搜索
    originaltitle = res.get("originaltitle", "")
    res["originaltitle_amazon"] = originaltitle
    if res.get("actor_amazon", []):
        for each in res["actor_amazon"]:  # 去除演员名，避免搜索不到
            try:
                end_actor = re.compile(rf" {each}$")
                res["originaltitle_amazon"] = re.sub(end_actor, "", res["originaltitle_amazon"])
            except Exception:
                pass

    # VR 时下载小封面
    if "VR" in number:
        res["image_download"] = True

    # 返回处理后的json_data
    res["number"] = number
    res["letters"] = letters
    res["has_sub"] = has_sub
    res["c_word"] = c_word
    res["leak"] = leak
    res["wuma"] = wuma
    res["youma"] = youma
    res["cd_part"] = cd_part
    res["destroyed"] = destroyed
    res["version"] = version
    res["file_path"] = file_path
    res["appoint_number"] = appoint_number
    res["appoint_url"] = appoint_url

    return res


def _get_website_name(task_input: JsonData, file_mode: FileMode) -> str:
    # 获取刮削网站
    website_name = "all"
    if file_mode == FileMode.Single:  # 刮削单文件（工具页面）
        website_name = Flags.website_name
    elif file_mode == FileMode.Again:  # 重新刮削
        website_temp = task_input["website_name"]
        if website_temp:
            website_name = website_temp
    elif config.scrape_like == "single":
        website_name = config.website_single

    return website_name


async def crawl(task_input: JsonData, file_mode: FileMode) -> CrawlersResult:
    # 从指定网站获取json_data
    website_name = _get_website_name(task_input, file_mode)
    res = await _crawl(task_input, website_name)
    return _deal_res(res)


def _deal_res(res: CrawlersResult) -> CrawlersResult:
    # 标题为空返回
    title = res["title"]
    if not title:
        return res

    # 演员
    res["actor"] = (
        str(res["actor"])
        .strip(" [ ]")
        .replace("'", "")
        .replace(", ", ",")
        .replace("<", "(")
        .replace(">", ")")
        .strip(",")
    )  # 列表转字符串（避免个别网站刮削返回的是列表）

    # 标签
    tag = (
        str(res["tag"]).strip(" [ ]").replace("'", "").replace(", ", ",")
    )  # 列表转字符串（避免个别网站刮削返回的是列表）
    tag = re.sub(r",\d+[kKpP],", ",", tag)
    tag_rep_word = [",HD高画质", ",HD高畫質", ",高画质", ",高畫質"]
    for each in tag_rep_word:
        if tag.endswith(each):
            tag = tag.replace(each, "")
        tag = tag.replace(each + ",", ",")
    res["tag"] = tag

    # poster图
    if not res.get("poster"):
        res["poster"] = ""

    # 发行日期
    release = res["release"]
    if release:
        release = release.replace("/", "-").strip(". ")
        if len(release) < 10:
            release_list = re.findall(r"(\d{4})-(\d{1,2})-(\d{1,2})", release)
            if release_list:
                r_year, r_month, r_day = release_list[0]
                r_month = "0" + r_month if len(r_month) == 1 else r_month
                r_day = "0" + r_day if len(r_day) == 1 else r_day
                release = r_year + "-" + r_month + "-" + r_day
    res["release"] = release

    # 评分
    if res.get("score", ""):
        res["score"] = "%.1f" % float(res.get("score", 0))

    # publisher
    if not res.get("publisher", ""):
        res["publisher"] = res["studio"]

    # 字符转义，避免显示问题
    key_word = [
        "title",
        "originaltitle",
        "number",
        "outline",
        "originalplot",
        "actor",
        "tag",
        "series",
        "director",
        "studio",
        "publisher",
    ]
    rep_word = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&apos;": "'",
        "&quot;": '"',
        "&lsquo;": "「",
        "&rsquo;": "」",
        "&hellip;": "…",
        "<br/>": "",
        "・": "·",
        "“": "「",
        "”": "」",
        "...": "…",
        "\xa0": "",
        "\u3000": "",
        "\u2800": "",
    }
    for each in key_word:
        for key, value in rep_word.items():
            res[each] = res[each].replace(key, value)

    # 命名规则
    naming_media = config.naming_media
    naming_file = config.naming_file
    folder_name = config.folder_name
    res["naming_media"] = naming_media
    res["naming_file"] = naming_file
    res["folder_name"] = folder_name
    return res
