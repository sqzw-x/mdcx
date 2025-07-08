"""
爬虫控制, 调用 models.crawlers 中各个网站爬虫
"""

import asyncio
import re
from typing import Callable

import langid

from ..base.number import get_number_letters, is_uncensored
from ..config.manager import config
from ..config.manual import ManualConfig
from ..crawlers import (
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
from ..entity.enums import FileMode
from .flags import Flags
from .json_data import JsonData, LogBuffer

CRAWLER_FUNCS: dict[str, Callable] = {
    "official": official.main,
    "iqqtv": iqqtv_new.main,
    "avsex": avsex.main,
    "airav_cc": airav_cc.main,
    "airav": airav.main,
    "freejavbt": freejavbt.main,
    "javbus": javbus.main,
    "javdb": javdb.main,
    "jav321": jav321.main,
    "dmm": dmm.main,
    "javlibrary": javlibrary_new.main,
    "xcity": xcity.main,
    "avsox": avsox.main,
    "mgstage": mgstage.main,
    "7mmtv": mmtv.main,
    "fc2": fc2.main,
    "fc2hub": fc2hub.main,
    "fc2club": fc2club.main,
    "fc2ppvdb": fc2ppvdb.main,
    "mdtv": mdtv.main,
    "madouqu": madouqu.main,
    "hscangku": hscangku.main,
    "cableav": cableav.main,
    "getchu": getchu.main,
    "getchu_dmm": getchu_dmm.main,
    "mywife": mywife.main,
    "giga": giga.main,
    "hdouban": hdouban.main,
    "lulubar": lulubar.main,
    "love6": love6.main,
    "cnmdb": cnmdb.main,
    "faleno": faleno.main,
    "fantastica": fantastica.main,
    "theporndb": theporndb.main,
    "dahlia": dahlia.main,
    "prestige": prestige.main,
    "kin8": kin8.main,
    "javday": javday.main,
}


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

    return await crawler_func(**kwargs)


async def _call_crawlers(
    task_input: JsonData,
    number_website_list: list[str],
) -> JsonData:
    """
    获取一组网站的数据：按照设置的网站组，请求各字段数据，并返回最终的数据
    """
    number = task_input["number"]
    short_number = task_input["short_number"]
    mosaic = task_input["mosaic"]
    scrape_like = config.scrape_like
    none_fields = config.none_fields  # 不单独刮削的字段
    use_official = "official" in config.website_set  # 优先使用官方网站

    def get_field_websites(field: str) -> list[str]:
        """获取指定字段的网站取值优先级列表"""
        # 指定字段网站列表
        field_no_zh = field.replace("_zh", "")  # 去除 _zh 后缀的字段名
        field_list = clean_list(getattr(config, f"{field}_website", "").split(","))
        # 与指定类型网站列表取交集
        field_list = [i for i in field_list if i in number_website_list]
        if use_official:
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
    # 各字段语言
    all_field_languages = {field: getattr(config, f"{field}_language", "zh") for field in all_fields}
    # 所有需要请求的 (网站, 语言) 对
    all_websites = (
        (website, all_field_languages[field]) for field, websites in all_field_websites.items() for website in websites
    )

    tasks = []
    for website, language in all_websites:
        tasks.append(_call_crawler(task_input, website, language, config.title_language))
    res: list[dict[str, dict[str, dict]]] = await asyncio.gather(*tasks)

    # 合并结果
    all_res: dict[tuple[str, str], dict] = {}
    for website_data in res:
        for website, datas in website_data.items():
            for lang, data in datas.items():
                key = (website, lang)
                if key in all_res:
                    raise ValueError(f"Duplicate data for {key} found in crawler results.")
                all_res[key] = data

    # 按优先级合并
    # 处理配置项和返回值的不匹配字段
    # 1. originaltitle 的取值优先级对应 title, 语言为 jp
    all_field_websites["originaltitle"] = all_field_websites.get("title", number_website_list)
    all_field_languages["originaltitle"] = "jp"
    # 2. originalplot 的取值优先级对应 outline
    all_field_websites["originalplot"] = all_field_websites.get("outline", number_website_list)
    all_field_languages["originalplot"] = "jp"
    # 2. 当语言非 jp 时, 最终 title 的取值优先级为 title 和 title_zh, 且需检查所有语言
    if config.title_language != "jp":
        all_field_websites["title"] += all_field_websites.get("title_zh", [])
        all_field_languages["title"] = "all"
    # 3. 当语言非 jp 时, 最终 outline 的取值优先级为 outline 和 outline_zh, 且需检查所有语言
    if config.outline_language != "jp":
        all_field_websites["outline"] += all_field_websites.get("outline_zh", [])
        all_field_languages["outline"] = "all"

    reduced: dict = {"number": number, "short_number": short_number, "mosaic": mosaic, "fields_info": ""}
    for field in ManualConfig.CRAWLER_DATA_FIELDS:  # 与 CONFIG_DATA_FIELDS 不完全一致
        if field not in all_field_websites:
            # 没有设定此字段的优先级和语言, 则任意取值
            sources = [(w, lang) for w in number_website_list for lang in ["jp", "zh_cn", "zh_tw"]]
        else:
            sources = [(w, all_field_languages[field]) for w in all_field_websites[field]]

        LogBuffer.info().write(
            f"\n\n    🙋🏻‍ {field} \n    ====================================\n"
            f"    🌐 来源优先级：{' -> '.join(i[0] for i in sources)}"
        )
        for website, language in sources:
            if language == "all":
                site_data = (
                    all_res.get((website, "jp"), {})
                    or all_res.get((website, "zh_cn"), {})
                    or all_res.get((website, "zh_tw"), {})
                )
            else:
                site_data = all_res.get((website, language), {})

            if not site_data.get("title", "") or not site_data.get(field, ""):
                LogBuffer.info().write(f"\n    🔴 {website} (失败)")
                continue

            if config.scrape_like != "speed":
                if field in ["title", "outline", "originaltitle", "originalplot"]:
                    if website in ["airav_cc", "iqqtv", "airav", "avsex", "javlibrary", "lulubar"]:  # why?
                        if langid.classify(site_data[field])[0] != "ja":
                            if language == "jp":
                                LogBuffer.info().write(f"\n    🔴 {website} (失败，检测为非日文，跳过！)")
                                continue
                        elif language != "jp":
                            LogBuffer.info().write(f"\n    🔴 {website} (失败，检测为日文，跳过！)")
                            continue
            # 添加来源信息
            if field in ["poster", "thumb", "extrafanart", "trailer", "outline"]:
                reduced[field + "_from"] = website

            if field == "poster":
                reduced["image_download"] = site_data["image_download"]
            elif field == "thumb":
                # 记录所有 thumb url 以便后续下载
                reduced["thumb_list"] = reduced.get("thumb_list", []).append((website, site_data["thumb"]))
            elif field == "actor":
                if isinstance(site_data["actor"], list):
                    # 处理 actor 为列表的情况
                    site_data["actor"] = ",".join(site_data["actor"])
                reduced["all_actor"] = reduced.get("all_actor", site_data["actor"])
                reduced["all_actor_photo"] = reduced.get("all_actor_photo", site_data.get("actor_photo", ""))
                # 记录所有网站的 actor 用于 Amazon 搜图, 因为有的网站 actor 不对
                reduced["actor_amazon"] = reduced.get("actor_amazon", []).extend(site_data["actor"].split(","))
            elif field == "originaltitle" and site_data.get("actor", ""):
                reduced["amazon_orginaltitle_actor"] = site_data["actor"].split(",")[0]

            reduced[field] = site_data[field]
            reduced["fields_info"] += f"\n     {field:<13}: {website} ({language})"
            LogBuffer.info().write(f"\n    🟢 {website} (成功)\n     ↳ {reduced[field]}")
            break
        else:  # 所有来源都无此字段
            reduced[field] = None
            reduced["fields_info"] += "\n     {field:<13}: {'-----'} ({'not found'})"

    # 处理 year
    if reduced.get("year", "") and (r := re.search(r"\d{4}", reduced.get("release", ""))):
        reduced["year"] = r.group()

    # 处理 number：素人影片时使用有数字前缀的number
    if short_number:
        reduced["number"] = number

    # 处理 javdbid
    r = all_res.get(("javdb", "jp"), {}) or all_res.get(("javdb", "zh_cn"), {}) or all_res.get(("javdb", "zh_tw"), {})
    if r and "javdbid" in r:
        reduced["javdbid"] = r["javdbid"]

    # todo 由于异步, 此处日志混乱. 需移除 LogBuffer.req(), 改为返回日志信息
    reduced["fields_info"] = f"\n 🌐 [website] {LogBuffer.req().get().strip('-> ')}{reduced['fields_info']}"

    return reduced


async def _call_specific_crawler(task_input: JsonData, website: str) -> JsonData:
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


async def _crawl(task_input: JsonData, website_name: str) -> JsonData:  # 从JSON返回元数据
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
    originaltitle = res.get("originaltitle") if res.get("originaltitle") else ""
    res["originaltitle_amazon"] = originaltitle
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


async def crawl(task_input: JsonData, file_mode: FileMode) -> JsonData:
    # 从指定网站获取json_data
    website_name = _get_website_name(task_input, file_mode)
    res = await _crawl(task_input, website_name)
    return _deal_res(res)


def _deal_res(res: JsonData) -> JsonData:
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
