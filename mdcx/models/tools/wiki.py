import random
import re
import urllib.parse
from typing import Optional

import bs4
import langid
import zhconv

from mdcx.models.config.manager import config
from mdcx.models.config.manual import ManualConfig
from mdcx.models.config.resources import resources
from mdcx.models.core.flags import Flags
from mdcx.models.core.translate import (
    deepl_translate_async,
    llm_translate_async,
    youdao_translate_async,
)
from mdcx.models.core.web import google_translate_async
from mdcx.models.data_models import EMbyActressInfo


async def search_wiki(actor_info: EMbyActressInfo) -> tuple[Optional[str], str]:
    """
    搜索维基百科演员信息

    Args:
        actor_info: 演员信息, 将填充 wiki 解析结果

    Returns:
        tuple: wiki 详情页 URL, 日志
    """
    try:
        actor_name = actor_info.name
        # 优先用日文去查找，其次繁体。wiki的搜索很烂，因为跨语言的原因，经常找不到演员
        actor_data = resources.get_actor_data(actor_name)
        actor_name_tw = ""
        if actor_data["has_name"]:
            actor_name = actor_data["jp"]
            actor_name_tw = actor_data["zh_tw"]
            if actor_name_tw == actor_name:
                actor_name_tw = ""
        else:
            actor_name = zhconv.convert(actor_name, "zh-hant")

        # 请求维基百科搜索页接口
        url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={actor_name}&language=zh&format=json"
        res, error = await config.async_client.get_json(url, headers=config.random_headers)
        if res is None:
            return None, f"维基百科搜索结果请求失败: {error}"

        search_results = res.get("search")

        # 搜索无结果
        if not search_results:
            if not actor_name_tw:
                return None, "维基百科暂未收录"
            url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={actor_name_tw}&language=zh&format=json"
            res, error = await config.async_client.get_json(url)
            if res is None:
                return None, f"维基百科搜索结果请求失败: {error}"
            search_results = res.get("search")
            # 搜索无结果
            if not search_results:
                return None, "维基百科暂未收录"

        for each_result in search_results:
            description = each_result.get("description")

            # 根据描述信息判断是否为女优
            if description:
                description_en = description
                description_t = description.lower()
                for each_des in ManualConfig.ACTRESS_WIKI_KEYWORDS:
                    if each_des.lower() in description_t:
                        break
                else:
                    continue
                actor_info.taglines = [f"{description}"]
            else:
                description_en = ""

            # 通过id请求数据，获取 wiki url
            wiki_id = each_result.get("id")
            url = f"https://m.wikidata.org/wiki/Special:EntityData/{wiki_id}.json"
            res, error = await config.async_client.get_json(url, headers=config.random_headers)
            if res is None:
                continue
            # 获取详细信息并返回URL
            url, msg = handle_search_res(res, wiki_id, actor_info, description_en)
            if url is None:
                # todo log
                continue
            return url, msg
        return None, "未找到匹配的演员信息"
    except Exception as e:
        return None, f"搜索过程发生异常: {str(e)}"


async def get_detail(url, url_log, actor_info: EMbyActressInfo) -> tuple[bool, str]:
    """异步版本的_get_wiki_detail函数"""
    try:
        ja = True if "ja." in url else False
        emby_on = config.emby_on
        res, error = await config.async_client.get_text(url, headers=config.random_headers)
        if res is None:
            return False, f"维基百科演员页请求失败: {error}"
        if "noarticletext mw-content-ltr" in res:
            return False, "维基百科演员页没有该词条"

        av_key = [
            "女优",
            "女優",
            "男优",
            "男優",
            "（AV）导演",
            "AV导演",
            "AV監督",
            "成人电影",
            "成人影片",
            "映画監督",
            "アダルトビデオ監督",
            "电影导演",
            "配音員",
            "配音员",
            "声優",
            "声优",
            "グラビアアイドル",
            "モデル",
        ]
        for key in av_key:
            if key in res:
                break
        else:
            return False, "页面内容未命中关键词，识别为非女优或导演"

        # 处理维基百科内容
        result, error = await parse_detail(res, url, url_log, actor_info, ja, emby_on)
        return result, error
    except Exception as e:
        return False, f"获取维基百科详情时发生异常: {str(e)}"


def handle_search_res(res, wiki_id, actor_info, description_en) -> tuple[Optional[str], str]:
    # 更新 descriptions
    description_zh = ""
    description_ja = ""
    try:
        descriptions = res["entities"][wiki_id]["descriptions"]
        if descriptions:
            try:
                description_zh = descriptions["zh"]["value"]
                description_ja = descriptions["ja"]["value"]
            except Exception:
                pass
            if description_en:
                if not description_zh:
                    en_zh = {
                        "Japanese AV idol": "日本AV女优",
                        "Japanese pornographic actress": "日本AV女优",
                        "Japanese idol": "日本偶像",
                        "Japanese pornographic film director": "日本AV影片导演",
                        "Japanese film director": "日本电影导演",
                        "pornographic actress": "日本AV女优",
                        "Japanese actress": "日本AV女优",
                        "gravure idol": "日本写真偶像",
                    }
                    temp_zh = en_zh.get(description_en)
                    if temp_zh:
                        description_zh = temp_zh
                if not description_ja:
                    en_ja: dict[str, str] = {
                        "Japanese AV idol": "日本のAVアイドル",
                        "Japanese pornographic actress": "日本のポルノ女優",
                        "Japanese idol": "日本のアイドル",
                        "Japanese pornographic film director": "日本のポルノ映画監督",
                        "Japanese film director": "日本の映画監督",
                        "pornographic actress": "日本のAVアイドル",
                        "Japanese actress": "日本のAVアイドル",
                        "gravure idol": "日本のグラビアアイドル",
                    }
                    temp_ja = en_ja.get(description_en)
                    if temp_ja:
                        description_ja = temp_ja
    except Exception:
        pass

    # 获取 Tmdb，Imdb，Twitter，Instagram等id
    url_log = ""
    try:
        claims = res["entities"][wiki_id]["claims"]
    except Exception:
        claims = None
    if claims:
        try:
            tmdb_id = claims["P4985"][0]["mainsnak"]["datavalue"]["value"]
            actor_info.provider_ids["Tmdb"] = tmdb_id
            url_log += f"TheMovieDb: https://www.themoviedb.org/person/{tmdb_id} \n"

            imdb_id = claims["P345"][0]["mainsnak"]["datavalue"]["value"]
            actor_info.provider_ids["Imdb"] = imdb_id
            url_log += f"IMDb: https://www.imdb.com/name/{imdb_id} \n"

            twitter_id = claims["P2002"][0]["mainsnak"]["datavalue"]["value"]
            actor_info.provider_ids["Twitter"] = twitter_id
            url_log += f"Twitter: https://twitter.com/{twitter_id} \n"

            instagram_id = claims["P2003"][0]["mainsnak"]["datavalue"]["value"]
            actor_info.provider_ids["Instagram"] = instagram_id
            url_log += f"Instagram: https://www.instagram.com/{instagram_id} \n"

            fanza_id = claims["P9781"][0]["mainsnak"]["datavalue"]["value"]
            actor_info.provider_ids["Fanza"] = fanza_id
            url_log += f"Fanza: https://actress.dmm.co.jp/-/detail/=/actress_id={fanza_id} \n"

            xhamster_id = claims["P8720"][0]["mainsnak"]["datavalue"]["value"]
            actor_info.provider_ids["xHamster"] = f"https://xhamster.com/pornstars/{xhamster_id}"
            url_log += f"xHamster: https://xhamster.com/pornstars/{xhamster_id} \n"
        except Exception:
            pass

    # 获取 wiki url 和 description
    try:
        sitelinks = res["entities"][wiki_id]["sitelinks"]
        if sitelinks:
            jawiki = sitelinks.get("jawiki")
            zhwiki = sitelinks.get("zhwiki")
            ja_url: str = jawiki.get("url") if jawiki else ""
            zh_url: str = zhwiki.get("url") if zhwiki else ""
            url_final = ""
            emby_on = config.emby_on
            if "actor_info_zh_cn" in emby_on:
                if zh_url:
                    url_final = zh_url.replace("zh.wikipedia.org/wiki/", "zh.m.wikipedia.org/zh-cn/")
                elif ja_url:
                    url_final = ja_url.replace("ja.", "ja.m.")

                if description_zh:
                    description_zh = zhconv.convert(description_zh, "zh-cn")
                    actor_info.taglines = [f"{description_zh}"]
                else:
                    if description_ja:
                        actor_info.taglines = [f"{description_ja}"]
                    elif description_en:
                        actor_info.taglines = [f"{description_en}"]
                    if "actor_info_translate" in emby_on and (description_ja or description_en):
                        actor_info.taglines_translate = True

            elif "actor_info_zh_tw" in emby_on:
                if zh_url:
                    url_final = zh_url.replace("zh.wikipedia.org/wiki/", "zh.m.wikipedia.org/zh-tw/")
                elif ja_url:
                    url_final = ja_url.replace("ja.", "ja.m.")

                if description_zh:
                    description_zh = zhconv.convert(description_zh, "zh-hant")
                    actor_info.taglines = [f"{description_zh}"]
                else:
                    if description_ja:
                        actor_info.taglines = [f"{description_ja}"]
                    elif description_en:
                        actor_info.taglines = [f"{description_en}"]

                    if "actor_info_translate" in emby_on and (description_ja or description_en):
                        actor_info.taglines_translate = True

            elif ja_url:
                url_final = ja_url.replace("ja.", "ja.m.")
                if description_ja:
                    actor_info.taglines = [f"{description_ja}"]
                elif description_zh:
                    actor_info.taglines = [f"{description_zh}"]
                elif description_en:
                    actor_info.taglines = [f"{description_en}"]

            if url_final:
                url_unquote = urllib.parse.unquote(url_final)
                url_log += f"Wikipedia: {url_unquote}"
                return url_final, url_log
            else:
                return None, "维基百科未获取到演员页 url"
        return None, "维基百科处理失败"
    except Exception:
        return None, "维基百科数据处理异常"


async def parse_detail(res, url, url_log, actor_info, ja, emby_on):
    """处理维基百科页面内容的辅助函数"""
    try:
        res = re.sub(r"<a href=\"#cite_note.*?</a>", "", res)  # 替换[1],[2]等注释
        soup = bs4.BeautifulSoup(res, "lxml")
        actor_output = soup.find(class_="mw-parser-output")

        if not actor_output or not isinstance(actor_output, bs4.Tag):
            return False, "无法解析维基百科页面内容"

        # 开头简介
        overview = _extract_introduction(actor_output)

        # 个人资料
        actor_info.locations = ["日本"]
        try:
            overview = _process_personal_profile(actor_output, actor_info, overview, url, ja, emby_on)
        except ValueError as e:
            return False, str(e)

        # 提取人物介绍和个人经历
        actor_introduce_0 = actor_output.find(id="mf-section-0")

        # 人物
        try:
            overview += _extract_section_content(actor_output, actor_introduce_0, "人物", "人物介绍")
        except Exception:
            pass

        # 简历
        try:
            keywords = [
                "简历",
                "簡歷",
                "个人简历",
                "個人簡歷",
                "略歴",
                "経歴",
                "来歴",
                "生平",
                "生平与职业生涯",
                "略歴・人物",
            ]
            for keyword in keywords:
                content = _extract_section_content(actor_output, actor_introduce_0, keyword, "个人经历")
                if content:
                    overview += content
                    break
        except Exception:
            pass

        # 翻译
        try:
            overview = await _process_translation(actor_info, overview, ja, emby_on)
        except Exception as e:
            return False, f"翻译处理过程中发生异常: {str(e)}"

        # 外部链接和最终处理
        overview = _finalize_overview(overview, url_log, res, actor_info, emby_on)
        actor_info.overview = overview

        return True, ""

    except Exception as e:
        return False, f"处理维基百科页面内容时发生异常: {str(e)}"


def _extract_introduction(actor_output):
    """提取开头简介"""
    actor_introduce_0 = actor_output.find(id="mf-section-0")
    overview = ""
    if not actor_introduce_0 or not isinstance(actor_introduce_0, bs4.Tag):
        return overview

    begin_intro = actor_introduce_0.find_all("p")
    for each in begin_intro:
        if isinstance(each, bs4.Tag):
            info = each.get_text("", strip=True)
            overview += info + "\n"
    return overview


def _process_personal_profile(actor_output, actor_info, overview, url, ja, emby_on):
    """处理个人资料表格"""
    actor_profile = actor_output.find("table", class_=["infobox", "infobox vcard plainlist"])
    if not actor_profile or not isinstance(actor_profile, bs4.Tag):
        return overview

    att_keys = actor_profile.find_all(attrs={"scope": "row"})
    att_values = actor_profile.find_all("td", style="", colspan=False)

    if len(att_keys) != len(att_values):
        raise ValueError(
            f"个人资料表格列数不匹配，可能是页面格式变更或数据不完整，列数: {len(att_keys)} - {len(att_values)}, 页面地址: {url}"
        )

    if not att_keys or not att_values:
        return overview

    bday_element = actor_output.find(class_="bday")
    bday = f"({bday_element.get_text('', strip=True)})" if bday_element and isinstance(bday_element, bs4.Tag) else ""

    overview += "\n===== 个人资料 =====\n"
    for i, each in enumerate(att_keys):
        if not isinstance(each, bs4.Tag):
            continue

        info_left = each.get_text().strip()
        info_right_element = att_values[i]

        if not isinstance(info_right_element, bs4.Tag):
            continue

        info_right = info_right_element.get_text("", strip=True).replace(bday, "")
        info = info_left + ": " + info_right
        overview += info + "\n"

        _process_birth_info(info_left, info_right, actor_info)
        _process_location_info(info_left, info_right, actor_info, ja, emby_on)

    return overview


def _process_birth_info(info_left, info_right, actor_info):
    """处理出生信息"""
    if "出生" not in info_left and "生年" not in info_left:
        return

    result = re.findall(r"(\d+)年(\d+)月(\d+)日", info_right)
    if not result:
        return

    result = result[0]
    year = str(result[0]) if len(result[0]) == 4 else "19" + str(result[0]) if len(result[0]) == 2 else "1970"
    month = str(result[1]) if len(result[1]) == 2 else "0" + str(result[1])
    day = str(result[2]) if len(result[2]) == 2 else "0" + str(result[2])
    birthday = f"{year}-{month}-{day}"
    actor_info.birthday = birthday
    actor_info.year = year


def _process_location_info(info_left, info_right, actor_info, ja, emby_on):
    """处理出身地信息"""
    if "出身地" not in info_left and "出道地点" not in info_left:
        return

    location = re.findall(r"[^ →]+", info_right)
    if not location:
        return

    location = location[0]
    if location == "日本":
        return

    if ja and "actor_info_translate" in emby_on and "actor_info_ja" not in emby_on:
        location = location.replace("県", "县")
        if "actor_info_zh_cn" in emby_on:
            location = zhconv.convert(location, "zh-cn")
        elif "actor_info_zh_tw" in emby_on:
            location = zhconv.convert(location, "zh-hant")

    location = "日本·" + location.replace("日本・", "").replace("日本·", "").replace("日本", "")
    actor_info.locations = [f"{location}"]


def _extract_section_content(actor_output, actor_introduce_0, section_name, section_title):
    """提取指定章节内容的通用函数"""
    if not actor_introduce_0 or not isinstance(actor_introduce_0, bs4.Tag):
        return ""

    toctext_element = actor_introduce_0.find(class_="toctext", string=section_name)
    if not toctext_element or not isinstance(toctext_element, bs4.Tag):
        return ""

    sibling = toctext_element.find_previous_sibling()
    if not sibling or not isinstance(sibling, bs4.Tag) or not hasattr(sibling, "string") or not sibling.string:
        return ""

    s = sibling.string
    if not s:
        return ""

    ff = actor_output.find(id=f"mf-section-{s}")
    if not ff or not isinstance(ff, bs4.Tag):
        return ""

    content = f"\n===== {section_title} =====\n"
    actor_1 = ff.find_all(["p", "li"])
    for each in actor_1:
        if isinstance(each, bs4.Tag):
            info = each.get_text("", strip=True)
            content += info + "\n"

    return content


async def _process_translation(actor_info, overview, ja, emby_on):
    """处理翻译逻辑"""
    tag_trans = actor_info.taglines_translate
    if not (ja or tag_trans) or "actor_info_translate" not in emby_on or "actor_info_ja" in emby_on:
        return overview

    translate_by_list = Flags.translate_by_list.copy()
    random.shuffle(translate_by_list)

    if not translate_by_list:
        return overview

    overview_req = overview if ja and overview else ""
    tag_req = actor_info.taglines[0] if tag_trans else ""

    # 英文标签单独翻译
    if tag_req and langid.classify(tag_req)[0] == "en":
        tag_req = await _translate_english_tag(tag_req, translate_by_list, actor_info)

    # 翻译内容
    if overview_req or tag_req:
        overview = await _translate_content(tag_req, overview_req, translate_by_list, actor_info, overview)

    return overview


async def _translate_english_tag(tag_req, translate_by_list, actor_info):
    """翻译英文标签"""
    for each in translate_by_list:
        if each == "youdao":
            t, o, r = await youdao_translate_async(tag_req, "")
        elif each == "google":
            t, o, r = await google_translate_async(tag_req, "")
        elif each == "llm":
            t, o, r = await llm_translate_async(tag_req, "")
        else:  # deepl
            t, o, r = await deepl_translate_async(tag_req, "", ls="EN")

        if not r:
            actor_info.taglines = [t]
            return ""  # 清空tag_req表示已翻译
    return tag_req


async def _translate_content(tag_req, overview_req, translate_by_list, actor_info, overview):
    """翻译主要内容"""
    for each in translate_by_list:
        if each == "youdao":
            t, o, r = await youdao_translate_async(tag_req, overview_req)
        elif each == "google":
            t, o, r = await google_translate_async(tag_req, overview_req)
        elif each == "llm":
            t, o, r = await llm_translate_async(tag_req, overview_req)
        else:  # deepl
            t, o, r = await deepl_translate_async(tag_req, overview_req)

        if not r:
            if tag_req:
                actor_info.taglines = [t]
            if overview_req:
                overview = _clean_translated_overview(o)
            break
    return overview


def _clean_translated_overview(overview):
    """清理翻译后的概述文本"""
    replacements = [
        ("\n= = = = = = = = = =个人资料\n", "\n===== 个人资料 =====\n"),
        ("\n=====人物介绍\n", "\n===== 人物介绍 =====\n"),
        ("\n= = = = =个人鉴定= = = = =\n", "\n===== 个人经历 =====\n"),
        ("\n=====个人日历=====\n", "\n===== 个人经历 =====\n"),
        ("\n=====个人费用=====\n", "\n===== 个人资料 =====\n"),
        ("\n===== 个人协助 =====\n", "\n===== 人物介绍 =====\n"),
        ("\n===== 个人经济学 =====\n", "\n===== 个人经历 =====\n"),
        ("\n===== 个人信息 =====\n", "\n===== 个人资料 =====\n"),
        ("\n===== 简介 =====\n", "\n===== 人物介绍 =====\n"),
        (":", ": "),
    ]

    for old, new in replacements:
        overview = overview.replace(old, new)

    overview += "\n"

    if "=====\n" not in overview:
        overview = overview.replace(" ===== 个人资料 ===== ", "\n===== 个人资料 =====\n")
        overview = overview.replace(" ===== 人物介绍 ===== ", "\n===== 人物介绍 =====\n")
        overview = overview.replace(" ===== 个人经历 ===== ", "\n===== 个人经历 =====\n")

    return overview


def _finalize_overview(overview, url_log, res, actor_info, emby_on):
    """最终处理概述信息"""
    # 外部链接
    overview += f"\n===== 外部链接 =====\n{url_log}"
    overview = overview.replace("\n", "<br>").replace("这篇报道有多个问题。请协助改善和在笔记页上的讨论。", "").strip()

    # 设置默认标签
    if not actor_info.taglines:
        if "AV監督" in res:
            if "actor_info_zh_cn" in emby_on:
                actor_info.taglines = ["日本成人影片导演"]
            elif "actor_info_zh_tw" in emby_on:
                actor_info.taglines = ["日本成人影片導演"]
            elif "actor_info_ja" in emby_on:
                actor_info.taglines = ["日本のAV監督"]
        elif "女優" in res or "女优" in res:
            if "actor_info_zh_cn" in emby_on:
                actor_info.taglines = ["日本AV女优"]
            elif "actor_info_zh_tw" in emby_on:
                actor_info.taglines = ["日本AV女優"]
            elif "actor_info_ja" in emby_on:
                actor_info.taglines = ["日本のAV女優"]

    # 语言特定处理
    if "actor_info_zh_tw" in emby_on and overview:
        overview = zhconv.convert(overview, "zh-hant")
    elif "actor_info_ja" in emby_on:
        overview = overview.replace("== 个人资料 ==", "== 個人情報 ==")
        overview = overview.replace("== 人物介绍 ==", "== 人物紹介 ==")
        overview = overview.replace("== 个人经历 ==", "== 個人略歴 ==")
        overview = overview.replace("== 外部链接 ==", "== 外部リンク ==")

    return overview
