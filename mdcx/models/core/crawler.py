import asyncio
import re

from mdcx.config.manager import config
from mdcx.config.models import Language, Website, WebsiteSet
from mdcx.crawlers import get_crawler_compat
from mdcx.gen.field_enums import CrawlerResultFields
from mdcx.manual import ManualConfig
from mdcx.models.enums import FileMode
from mdcx.models.flags import Flags
from mdcx.models.log_buffer import LogBuffer
from mdcx.models.types import CrawlerInput, CrawlerResponse, CrawlerResult, CrawlersResult, CrawlTask
from mdcx.number import is_uncensored
from mdcx.utils.dataclass import update
from mdcx.utils.language import is_japanese

MULTI_LANGUAGE_WEBSITES = [  # 支持多语言, language 参数有意义
    Website.AIRAV_CC,
    Website.AIRAV,
    Website.IQQTV,
    Website.JAVLIBRARY,
]


def clean_list(raw: list[str]) -> list[str]:
    """清理列表，去除空值和重复值, 保持原有顺序"""
    cleaned = []
    for item in raw:
        if item.strip() and item not in cleaned:
            cleaned.append(item.strip())
    return cleaned


def _deal_some_list(field: str, website: Website, same_list: list[Website]) -> list[Website]:
    if website not in same_list:
        same_list.append(website)
    if field in ["title", "outline", "thumb", "poster", "trailer", "extrafanart"]:
        same_list.remove(website)
        same_list.insert(0, website)
    elif field in ["tag", "score", "director", "series"]:
        same_list.remove(website)
    return same_list


async def _call_crawler(task_input: CrawlerInput, website: Website, timeout: int = 30) -> CrawlerResponse:
    """
    调用指定网站的爬虫函数

    Args:
        task_input (CallCrawlerInput): 包含爬虫所需的输入数据
        website (str): 网站名称
        timeout (int): 请求超时时间，默认为30秒

    Raises:
        asyncio.TimeoutError: 如果请求超时
        Exception: 爬虫函数抛出的异常
    """
    short_number = task_input.short_number

    # 259LUXU-1111， mgstage 和 avsex 之外使用 LUXU-1111（素人番号时，short_number有值，不带前缀数字；反之，short_number为空)
    if short_number and website != "mgstage" and website != "avsex":
        task_input.number = short_number

    # 获取爬虫函数
    crawler = get_crawler_compat(website)
    c = crawler(config.async_client, config.get_website_base_url(website))

    # 对爬虫函数调用添加超时限制, 超时异常由调用者处理
    r = await asyncio.wait_for(c.run(task_input), timeout=timeout)
    return r


async def _call_crawlers(task_input: CrawlerInput, number_website_list: list[Website]) -> CrawlersResult:
    """
    获取一组网站的数据：按照设置的网站组，请求各字段数据，并返回最终的数据
    采用按需请求策略：仅请求必要的网站，失败时才请求下一优先级网站
    """
    number = task_input.number
    short_number = task_input.short_number
    scrape_like = config.scrape_like
    none_fields = config.none_fields  # 不单独刮削的字段

    def get_field_websites(field: str) -> list[Website]:
        """
        获取指定字段的来源优先级列表

        field_websites = (config.{field}_website - config.{field}_website_exclude) ∩ (number_website_list)
        """
        # 指定字段网站列表
        field_no_zh = field.replace("_zh", "")  # 去除 _zh 后缀的字段名
        field_list: list[Website] = getattr(config.pydantic, f"{field}_website", [])
        # todo 移除运行时检查
        assert all(isinstance(i, Website) for i in field_list), f"{field}_website must be a list of Website"
        # 与指定类型网站列表取交集
        field_list = [i for i in field_list if i in number_website_list]
        if WebsiteSet.OFFICIAL in config.pydantic.website_set:  # 优先使用官方网站
            field_list.insert(0, Website.OFFICIAL)
        # 指定字段排除网站列表
        field_ex_list: list[Website] = getattr(config.pydantic, f"{field_no_zh}_website_exclude", [])
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
            if field not in not_frist_field_list and Website.MGSTAGE in field_list:
                field_list.remove(Website.MGSTAGE)
                field_list.insert(0, Website.MGSTAGE)
        # faleno.jp 番号检查 dldss177 dhla009
        elif re.findall(r"F[A-Z]{2}SS", number):
            field_list = _deal_some_list(field, Website.FALENO, field_list)
        # dahlia-av.jp 番号检查
        elif number.startswith("DLDSS") or number.startswith("DHLA"):
            field_list = _deal_some_list(field, Website.DAHLIA, field_list)
        # fantastica 番号检查 FAVI、FAAP、FAPL、FAKG、FAHO、FAVA、FAKY、FAMI、FAIT、FAKA、FAMO、FASO、FAIH、FASH、FAKS、FAAN
        elif (
            re.search(r"FA[A-Z]{2}-?\d+", number.upper())
            or number.upper().startswith("CLASS")
            or number.upper().startswith("FADRV")
            or number.upper().startswith("FAPRO")
            or number.upper().startswith("FAKWM")
            or number.upper().startswith("PDS")
        ):
            field_list = _deal_some_list(field, Website.FANTASTICA, field_list)
        return field_list

    # 获取使用的网站
    all_fields = [f for f in ManualConfig.CONFIG_DATA_FIELDS if f not in none_fields]  # 去除不专门刮削的字段
    if scrape_like == "speed":  # 快速模式
        all_field_websites = dict.fromkeys(all_fields, number_website_list)
    else:  # 全部模式
        # 各字段网站列表
        all_field_websites = {field: get_field_websites(field) for field in all_fields}
        if config.outline_language == "jp" and "outline_zh" in all_field_websites:
            del all_field_websites["outline_zh"]
        if config.title_language == "jp" and "title_zh" in all_field_websites:
            del all_field_websites["title_zh"]

    # 各字段语言, 未指定则默认为 "any"
    all_field_languages: dict[str, Language] = {
        field: getattr(config.pydantic, f"{field}_language", Language.UNDEFINED) for field in all_fields
    }
    all_field_languages["title_zh"] = config.pydantic.title_language
    all_field_languages["outline_zh"] = config.pydantic.outline_language

    # 处理配置项中没有的字段
    # originaltitle 的网站优先级同 title, 语言为 jp
    all_field_websites["originaltitle"] = all_field_websites.get("title", number_website_list)
    all_field_languages["originaltitle"] = Language.JP
    all_field_websites["originalplot"] = all_field_websites.get("outline", number_website_list)
    all_field_languages["originalplot"] = Language.JP

    # 各字段的取值优先级 (网站, 语言) 对
    all_field_website_lang_pairs: dict[str, list[tuple[Website, Language]]] = {}
    for field, websites in all_field_websites.items():
        language = all_field_languages[field]
        all_field_website_lang_pairs[field] = []
        for website in websites:
            pair = (website, language)
            if website not in MULTI_LANGUAGE_WEBSITES:
                pair = (website, Language.UNDEFINED)  # 单语言网站, 语言参数无意义
            all_field_website_lang_pairs[field].append(pair)

    # 缓存已请求的网站结果
    all_res: dict[tuple[Website, Language], CrawlerResult] = {}
    reduced = CrawlersResult.empty()

    # 无优先级设置的字段的默认配置
    default_website_lang_pairs: list[tuple[Website, Language]] = [(w, Language.UNDEFINED) for w in number_website_list]

    # 处理 CrawlerResult 字段重命名
    for old, new in ManualConfig.RENAME_MAP.items():
        if old in all_field_languages:
            all_field_languages[new] = all_field_languages[old]
            del all_field_languages[old]
        if old in all_field_website_lang_pairs:
            all_field_website_lang_pairs[new] = all_field_website_lang_pairs[old]
            del all_field_website_lang_pairs[old]

    all_field_website_lang_pairs["all_actors"] = all_field_website_lang_pairs["actors"]

    # 按字段分别处理，每个字段按优先级尝试获取
    for field in ManualConfig.REDUCED_FIELDS:  # 与 CONFIG_DATA_FIELDS 不完全一致
        # 获取该字段的优先级列表
        sources = all_field_website_lang_pairs.get(field, default_website_lang_pairs)

        # 如果title_language不是jp，则允许从title_zh来源获取title
        if field == CrawlerResultFields.TITLE and config.pydantic.title_language != Language.JP:
            sources = sources + all_field_website_lang_pairs.get("title_zh", [])
        # 如果outline_language不是jp，则允许从outline_zh来源获取outline
        elif field == CrawlerResultFields.OUTLINE and config.pydantic.outline_language != Language.JP:
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
                key = (website, Language.UNDEFINED)

            # 如果已有该网站数据，直接使用
            if key in all_res:
                site_data = all_res[key]
            else:
                # 如果网站数据尚未请求，则进行请求
                try:
                    task_input.language = language
                    task_input.org_language = config.title_language
                    web_data = await _call_crawler(task_input, website)
                    if web_data.data is None:
                        if e := web_data.debug_info.error:
                            raise e
                        raise ValueError(f"爬虫 {website} 返回了空数据")
                    site_data = web_data.data
                    # 处理并保存结果
                    all_res[key] = web_data.data
                    # 多语言网站, 如果 undefined 尚不存在, 也使用当前语言数据
                    if website in MULTI_LANGUAGE_WEBSITES and (website, Language.UNDEFINED) not in all_res:
                        all_res[(website, Language.UNDEFINED)] = web_data.data
                except Exception as e:
                    LogBuffer.info().write(f"\n    🔴 {website} (异常: {str(e)})")
                    continue

            # 获取网站数据
            if not site_data or not site_data.title or not getattr(site_data, field, None):
                LogBuffer.info().write(f"\n    🔴 {website} (失败)")
                continue

            # 语言检测逻辑
            if config.scrape_like != "speed" and field in [
                CrawlerResultFields.TITLE,
                CrawlerResultFields.OUTLINE,
                CrawlerResultFields.ORIGINALTITLE,
                CrawlerResultFields.ORIGINALPLOT,
            ]:
                lang = all_field_languages.get(field, Language.JP)
                if website in ["airav_cc", "iqqtv", "airav", "avsex", "javlibrary", "lulubar"]:  # why?
                    if not is_japanese(getattr(site_data, field, "")):
                        if lang == Language.JP:
                            LogBuffer.info().write(f"\n    🔴 {website} (失败，检测为非日文，跳过！)")
                            continue
                    elif lang != Language.JP:
                        LogBuffer.info().write(f"\n    🔴 {website} (失败，检测为日文，跳过！)")
                        continue

            # 添加来源信息
            if field in [
                CrawlerResultFields.POSTER,
                CrawlerResultFields.THUMB,
                CrawlerResultFields.EXTRAFANART,
                CrawlerResultFields.TRAILER,
                CrawlerResultFields.OUTLINE,
            ]:
                setattr(reduced, field + "_from", website)

            if field == CrawlerResultFields.POSTER:
                reduced.image_download = site_data.image_download
            elif field == CrawlerResultFields.ORIGINALTITLE and site_data.actor:
                reduced.amazon_orginaltitle_actor = site_data.actor.split(",")[0]

            # 保存数据
            setattr(reduced, field, getattr(site_data, field))
            reduced.fields_info += f"\n     {field:<13}: {website}" + f" ({language})" * bool(language)
            LogBuffer.info().write(f"\n    🟢 {website} (成功)\n     ↳ {getattr(reduced, field)}")

            # 找到有效数据，跳出循环继续处理下一个字段
            break
        else:  # 所有来源都无此字段
            reduced.fields_info += f"\n     {field:<13}: {'-----'} ({'not found'})"

    # 需尽力收集的字段
    for data in all_res.values():
        # 记录所有来源的 thumb url 以便后续下载
        if data.thumb:
            reduced.thumb_list.append((data.source, data.thumb))
        # 记录所有来源的 actor 用于 Amazon 搜图
        if data.actor:
            reduced.actor_amazon.extend(data.actor.split(","))
    # 去重
    reduced.thumb_list = list(dict.fromkeys(reduced.thumb_list))  # 保序
    reduced.actor_amazon = list(set(reduced.actor_amazon))

    # 处理 year
    if reduced.year and (r := re.search(r"\d{4}", reduced.release)):
        reduced.year = r.group()

    # 处理 number：素人影片时使用有数字前缀的number
    if short_number:
        reduced.number = number

    # 处理 javdbid
    if r := all_res.get((Website.JAVDB, Language.UNDEFINED)):
        reduced.javdbid = r.javdbid

    # 处理 all_actor
    if not reduced.all_actor:
        # 如果没有 all_actor 字段，则从 actor 中获取
        reduced.all_actor = reduced.actor

    # todo 由于异步, 此处日志混乱. 需移除 LogBuffer.req(), 改为返回日志信息
    reduced.fields_info = f"\n 🌐 [website] {LogBuffer.req().get().strip('-> ')}{reduced.fields_info}"

    return reduced


async def _call_specific_crawler(task_input: CrawlerInput, website: Website) -> CrawlersResult:
    file_number = task_input.number
    short_number = task_input.short_number

    title_language = config.title_language
    org_language = title_language

    if website not in ["airav_cc", "iqqtv", "airav", "avsex", "javlibrary", "mdtv", "madouqu", "lulubar"]:
        title_language = "jp"

    elif website == "mdtv":
        title_language = "zh_cn"

    task_input.language = title_language
    task_input.org_language = org_language
    web_data = await _call_crawler(task_input, website)
    web_data_json = web_data.data
    if web_data_json is None:
        return CrawlersResult.empty()

    res = update(CrawlersResult.empty(), web_data_json)
    if not res.title:
        return res
    if res.thumb:
        res.thumb_list = [(website, res.thumb)]

    # 加入来源信息
    res.outline_from = website
    res.poster_from = website
    res.thumb_from = website
    res.extrafanart_from = website
    res.trailer_from = website
    # todo
    res.fields_info = f"\n 🌐 [website] {LogBuffer.req().get().strip('-> ')}"

    if short_number:
        res.number = file_number

    res.actor_amazon = web_data_json.actors
    res.all_actors = res.all_actors or web_data_json.actors

    return res


async def _crawl(task_input: CrawlTask, website: Website | None) -> CrawlersResult | None:  # 从JSON返回元数据
    appoint_number = task_input.appoint_number
    cd_part = task_input.cd_part
    destroyed = task_input.destroyed
    file_number = task_input.number
    file_path = task_input.file_path
    leak = task_input.leak
    mosaic = task_input.mosaic
    short_number = task_input.short_number
    wuma = task_input.wuma
    youma = task_input.youma

    # ================================================网站规则添加开始================================================

    if website is None:  # 从全部网站刮削
        # =======================================================================先判断是不是国产，避免浪费时间
        if (
            mosaic == "国产"
            or mosaic == "國產"
            or (re.search(r"([^A-Z]|^)MD[A-Z-]*\d{4,}", file_number) and "MDVR" not in file_number)
            or re.search(r"MKY-[A-Z]+-\d{3,}", file_number)
        ):
            task_input.mosaic = "国产"
            res = await _call_crawlers(task_input, config.pydantic.website_guochan)

        # =======================================================================kin8
        elif file_number.startswith("KIN8"):
            website = Website.KIN8
            res = await _call_specific_crawler(task_input, website)

        # =======================================================================同人
        elif file_number.startswith("DLID"):
            website = Website.GETCHU
            res = await _call_specific_crawler(task_input, website)

        # =======================================================================里番
        elif "getchu" in file_path.lower() or "里番" in file_path or "裏番" in file_path:
            website = Website.GETCHU_DMM
            res = await _call_specific_crawler(task_input, website)

        # =======================================================================Mywife No.1111
        elif "mywife" in file_path.lower():
            website = Website.MYWIFE
            res = await _call_specific_crawler(task_input, website)

        # =======================================================================FC2-111111
        elif "FC2" in file_number.upper():
            file_number_1 = re.search(r"\d{5,}", file_number)
            if file_number_1:
                file_number_1.group()
                res = await _call_crawlers(task_input, config.pydantic.website_fc2)
            else:
                LogBuffer.error().write(f"未识别到FC2番号：{file_number}")
                res = None

        # =======================================================================sexart.15.06.14
        elif re.search(r"[^.]+\.\d{2}\.\d{2}\.\d{2}", file_number) or (
            "欧美" in file_path and "东欧美" not in file_path
        ):
            res = await _call_crawlers(task_input, config.pydantic.website_oumei)

        # =======================================================================无码抓取:111111-111,n1111,HEYZO-1111,SMD-115
        elif mosaic == "无码" or mosaic == "無碼":
            res = await _call_crawlers(task_input, config.pydantic.website_wuma)

        # =======================================================================259LUXU-1111
        elif short_number or "SIRO" in file_number.upper():
            res = await _call_crawlers(task_input, config.pydantic.website_suren)

        # =======================================================================ssni00321
        elif re.match(r"\D{2,}00\d{3,}", file_number) and "-" not in file_number and "_" not in file_number:
            res = await _call_crawlers(task_input, [Website.DMM])

        # =======================================================================剩下的（含匹配不了）的按有码来刮削
        else:
            website_list = config.pydantic.website_youma
            if WebsiteSet.OFFICIAL in config.pydantic.website_set:  # 优先使用官方网站
                website_list.insert(0, Website.OFFICIAL)
            res = await _call_crawlers(task_input, website_list)
    else:
        res = await _call_specific_crawler(task_input, website)

    # ================================================网站请求结束================================================
    # ======================================超时或未找到返回
    if res is None:
        return None

    number = file_number  # res.number 实际上并未设置, 此处取 file_number
    if appoint_number:
        number = appoint_number
    res.number = number  # 此处设置

    # 马赛克
    if leak:
        res.mosaic = "无码流出"
    elif destroyed:
        res.mosaic = "无码破解"
    elif wuma:
        res.mosaic = "无码"
    elif youma:
        res.mosaic = "有码"
    elif mosaic:
        res.mosaic = mosaic
    if not res.mosaic:
        if is_uncensored(number):
            res.mosaic = "无码"
        else:
            res.mosaic = "有码"
    print(number, cd_part, res.mosaic, LogBuffer.req().get().strip("-> "))

    # 原标题，用于amazon搜索
    res.originaltitle_amazon = res.originaltitle
    if res.actor_amazon:
        for each in res.actor_amazon:  # 去除演员名，避免搜索不到
            try:
                end_actor = re.compile(rf" {each}$")
                res.originaltitle_amazon = re.sub(end_actor, "", res.originaltitle_amazon)
            except Exception:
                pass

    # VR 时下载小封面
    if "VR" in number:
        res.image_download = True

    return res


def _get_website_name(task_input: CrawlTask, file_mode: FileMode) -> str:
    # 获取刮削网站
    website_name = "all"
    if file_mode == FileMode.Single:  # 刮削单文件（工具页面）
        website_name = Flags.website_name
    elif file_mode == FileMode.Again:  # 重新刮削
        website_temp = task_input.website_name
        if website_temp:
            website_name = website_temp
    elif config.scrape_like == "single":
        website_name = config.website_single

    return website_name


async def crawl(task_input: CrawlTask, file_mode: FileMode) -> CrawlersResult | None:
    # 从指定网站获取json_data
    website_name = _get_website_name(task_input, file_mode)
    if website_name == "all":
        website = None
    else:
        website = Website(website_name)
    res = await _crawl(task_input, website)
    return _deal_res(res)


def _deal_res(res: CrawlersResult | None) -> CrawlersResult | None:
    # 标题为空返回
    if res is None or not res.title:
        return None

    # 演员
    res.actor = (
        str(res.actor).strip(" [ ]").replace("'", "").replace(", ", ",").replace("<", "(").replace(">", ")").strip(",")
    )  # 列表转字符串（避免个别网站刮削返回的是列表）

    # 标签
    tag = str(res.tag).strip(" [ ]").replace("'", "").replace("，", ",").replace(", ", ",")  # 列表转字符串
    tag = re.sub(r",\d+[kKpP],", ",", tag)
    tag_rep_word = [",HD高画质", ",HD高畫質", ",高画质", ",高畫質"]
    for each in tag_rep_word:
        if tag.endswith(each):
            tag = tag.replace(each, "")
        tag = tag.replace(each + ",", ",")
    res.tag = tag

    # 发行日期
    release = res.release
    if release:
        release = release.replace("/", "-").strip(". ")
        if len(release) < 10:
            release_list = re.findall(r"(\d{4})-(\d{1,2})-(\d{1,2})", release)
            if release_list:
                r_year, r_month, r_day = release_list[0]
                r_month = "0" + r_month if len(r_month) == 1 else r_month
                r_day = "0" + r_day if len(r_day) == 1 else r_day
                release = r_year + "-" + r_month + "-" + r_day
    res.release = release

    # 评分
    if res.score:
        res.score = f"{float(res.score):.1f}"

    # publisher
    if not res.publisher:
        res.publisher = res.studio

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
            # res[each] = res[each].replace(key, value)
            setattr(res, each, getattr(res, each).replace(key, value))

    # 命名规则
    # naming_media = config.naming_media
    # naming_file = config.naming_file
    # folder_name = config.folder_name
    # res.naming_media = naming_media
    # res.naming_file = naming_file
    # res.folder_name = folder_name
    return res
