import re
import time
import traceback
from io import StringIO
from pathlib import Path

import aiofiles
import aiofiles.os
from lxml import etree

from ..config.enums import DownloadableFile, KeepableFile, Language, NfoInclude, OutlineShow, ReadMode, Website
from ..config.manager import manager
from ..gen.field_enums import CrawlerResultFields
from ..manual import ManualConfig
from ..models.log_buffer import LogBuffer
from ..models.types import CrawlersResult, FileInfo, OtherInfo
from ..number import get_number_letters
from ..signals import signal
from ..utils import get_used_time
from ..utils.file import delete_file_async
from ..utils.language import is_japanese
from .utils import render_name_template


async def write_nfo(file_info: FileInfo, data: CrawlersResult, nfo_file: Path, output_dir: Path, update=False) -> bool:
    start_time = time.time()
    download_files = manager.config.download_files
    keep_files = manager.config.keep_files
    outline_show = manager.config.outline_format

    if not update:
        # 不写nfo
        # 不下载，不保留时
        if DownloadableFile.NFO not in download_files:
            if KeepableFile.NFO not in keep_files and await aiofiles.os.path.exists(nfo_file):
                await delete_file_async(nfo_file)
            return True

        LogBuffer.log().write(f"\n 🍀 Nfo done! (old)({get_used_time(start_time)}s)")
        return True

    if manager.config.main_mode == 3 or manager.config.main_mode == 4:
        nfo_title_template = manager.config.update_titletemplate
    else:
        nfo_title_template = manager.config.naming_media

    # 字符转义，避免emby无法解析
    rep_word = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&apos;": "'",
        "&quot;": '"',
        "&lsquo;": "「",
        "&rsquo;": "」",
        "&hellip;": "…",
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "'": "&apos;",
        '"': "&quot;",
    }

    def rep(raw: str) -> str:
        for key, value in rep_word.items():
            raw = raw.replace(key, value)
        return raw

    originalplot = rep(data.originalplot)
    originaltitle = rep(data.originaltitle)
    outline = rep(data.outline)
    publisher = rep(data.publisher)
    series = rep(data.series)
    studio = rep(data.studio)
    title = rep(data.title)

    show_4k = False
    show_cnword = False
    show_moword = False
    # 获取在媒体文件中显示的规则，不需要过滤Windows异常字符
    should_escape_result = False
    nfo_title, *_ = render_name_template(
        nfo_title_template,
        file_info,
        data,
        show_4k,
        show_cnword,
        show_moword,
        should_escape_result,
    )

    # 获取字段
    nfo_include_new = manager.config.nfo_include_new
    cd_part = file_info.cd_part
    cover = data.thumb
    directors = data.directors
    number = data.number
    poster = data.poster
    release = data.release
    runtime = data.runtime
    tags = data.tags
    trailer = data.trailer
    year = data.year

    try:
        if not await aiofiles.os.path.exists(output_dir):
            await aiofiles.os.makedirs(output_dir)
        await delete_file_async(nfo_file)  # 避免115出现重复文件

        code = StringIO()
        print('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', file=code)
        print("<movie>", file=code)

        # 输出剧情简介
        if outline:
            outline = outline.replace("\n", "<br>")
            if originalplot and originalplot != outline:
                if OutlineShow.SHOW_ZH_JP in outline_show:
                    outline += f"<br>  <br>{originalplot}"
                elif OutlineShow.SHOW_JP_ZH in outline_show:
                    outline = f"{originalplot}<br>  <br>{outline}"
                outline_from = data.outline_from.capitalize().replace("Youdao", "有道").replace("Llm", "LLM")
                if OutlineShow.SHOW_FROM in outline_show and outline_from:
                    outline += f"<br>  <br>由 {outline_from} 提供翻译"
            if NfoInclude.OUTLINE_NO_CDATA in nfo_include_new:
                temp_outline = outline.replace("<br>", "")
                if NfoInclude.PLOT_ in nfo_include_new:
                    print(f"  <plot>{temp_outline}</plot>", file=code)
                if NfoInclude.OUTLINE in nfo_include_new:
                    print(f"  <outline>{temp_outline}</outline>", file=code)
            else:
                if NfoInclude.PLOT_ in nfo_include_new:
                    print("  <plot><![CDATA[" + outline + "]]></plot>", file=code)
                if NfoInclude.OUTLINE in nfo_include_new:
                    print("  <outline><![CDATA[" + outline + "]]></outline>", file=code)

        # 输出日文剧情简介
        if originalplot and NfoInclude.ORIGINALPLOT in nfo_include_new:
            originalplot = originalplot.replace("\n", "<br>")
            if NfoInclude.OUTLINE_NO_CDATA in nfo_include_new:
                temp_originalplot = originalplot.replace("<br>", "")
                print(f"  <originalplot>{temp_originalplot}</originalplot>", file=code)
            else:
                print("  <originalplot><![CDATA[" + originalplot + "]]></originalplot>", file=code)

        # 输出发行日期
        if release:
            nfo_tagline = manager.config.nfo_tagline.replace("release", release)
            if nfo_tagline:
                print("  <tagline>" + nfo_tagline + "</tagline>", file=code)
            if NfoInclude.PREMIERED in nfo_include_new:
                print("  <premiered>" + release + "</premiered>", file=code)
            if NfoInclude.RELEASEDATE in nfo_include_new:
                print("  <releasedate>" + release + "</releasedate>", file=code)
            if NfoInclude.RELEASE_ in nfo_include_new:
                print("  <release>" + release + "</release>", file=code)

        # 输出番号
        print("  <num>" + number + "</num>", file=code)

        # 输出标题
        if cd_part and NfoInclude.TITLE_CD in nfo_include_new:
            nfo_title += " " + cd_part[1:].upper()
        print("  <title>" + nfo_title + "</title>", file=code)

        # 输出原标题
        if NfoInclude.ORIGINALTITLE in nfo_include_new:
            if number != title:
                print("  <originaltitle>" + number + " " + originaltitle + "</originaltitle>", file=code)
            else:
                print("  <originaltitle>" + originaltitle + "</originaltitle>", file=code)

        # 输出类标题
        if NfoInclude.SORTTITLE in nfo_include_new:
            if cd_part:
                originaltitle += " " + cd_part[1:].upper()
            if number != title:
                print("  <sorttitle>" + number + " " + originaltitle + "</sorttitle>", file=code)
            else:
                print("  <sorttitle>" + number + "</sorttitle>", file=code)

        # 输出国家和分级
        country = data.country

        # 输出家长分级
        if NfoInclude.MPAA in nfo_include_new:
            if country == "JP":
                print("  <mpaa>JP-18+</mpaa>", file=code)
            else:
                print("  <mpaa>NC-17</mpaa>", file=code)

        # 输出自定义分级
        if NfoInclude.CUSTOMRATING in nfo_include_new:
            if country == "JP":
                print("  <customrating>JP-18+</customrating>", file=code)
            else:
                print("  <customrating>NC-17</customrating>", file=code)

        # 输出国家
        if NfoInclude.COUNTRY in nfo_include_new:
            print(f"  <countrycode>{country}</countrycode>", file=code)

        # 输出男女演员
        if NfoInclude.ACTOR_ALL in nfo_include_new:
            actors = data.all_actors
        else:
            actors = data.actors
        # 有演员时输出演员
        if NfoInclude.ACTOR in nfo_include_new:
            if not actors:
                actors = [manager.config.actor_no_name]
            for name in actors:
                print("  <actor>", file=code)
                print("    <name>" + name + "</name>", file=code)
                print("    <type>Actor</type>", file=code)
                print("  </actor>", file=code)

        # 输出导演
        if NfoInclude.DIRECTOR in nfo_include_new:
            for name in directors:
                print("  <director>" + name + "</director>", file=code)

        # 输出公众评分、影评人评分
        try:
            if data.score:
                score = float(data.score)
                if NfoInclude.SCORE in nfo_include_new:
                    print("  <rating>" + str(score) + "</rating>", file=code)
                if NfoInclude.CRITICRATING in nfo_include_new:
                    print("  <criticrating>" + str(int(score * 10)) + "</criticrating>", file=code)
        except Exception:
            print(traceback.format_exc())

        # 输出我想看人数
        try:
            if data.wanted and NfoInclude.WANTED in nfo_include_new:
                print("  <votes>" + data.wanted + "</votes>", file=code)
        except Exception:
            pass

        # 输出年代
        if str(year) and NfoInclude.YEAR in nfo_include_new:
            print("  <year>" + str(year) + "</year>", file=code)

        # 输出时长
        if str(runtime) and NfoInclude.RUNTIME in nfo_include_new:
            print("  <runtime>" + str(runtime).replace(" ", "") + "</runtime>", file=code)

        # 输出合集(使用演员)
        if NfoInclude.ACTOR_SET in nfo_include_new:
            for name in data.actors:
                print("  <set>", file=code)
                print("    <name>" + name + "</name>", file=code)
                print("  </set>", file=code)

        # 输出合集(使用系列)
        if NfoInclude.SERIES_SET in nfo_include_new and series:
            print("  <set>", file=code)
            print("    <name>" + series + "</name>", file=code)
            print("  </set>", file=code)

        # 输出系列
        if series and NfoInclude.SERIES in nfo_include_new:
            print("  <series>" + series + "</series>", file=code)

        # 输出片商/制作商
        if studio:
            if NfoInclude.STUDIO in nfo_include_new:
                print("  <studio>" + studio + "</studio>", file=code)
            if NfoInclude.MAKER in nfo_include_new:
                print("  <maker>" + studio + "</maker>", file=code)

        # 输出发行商 label（厂牌/唱片公司） publisher（发行商）
        if publisher:
            if NfoInclude.PUBLISHER in nfo_include_new:
                print("  <publisher>" + publisher + "</publisher>", file=code)
            if NfoInclude.LABEL in nfo_include_new:
                print("  <label>" + publisher + "</label>", file=code)

        # 输出 tag
        if NfoInclude.TAG in nfo_include_new:
            for t in tags:
                if t:
                    print("  <tag>" + t + "</tag>", file=code)

        # 输出 genre
        if NfoInclude.GENRE in nfo_include_new:
            for t in tags:
                if t:
                    print("  <genre>" + t + "</genre>", file=code)

        # 输出封面地址
        if poster and NfoInclude.POSTER in nfo_include_new:
            print("  <poster>" + poster + "</poster>", file=code)

        # 输出背景地址
        if cover and NfoInclude.COVER in nfo_include_new:
            print("  <cover>" + cover + "</cover>", file=code)

        # 输出预告片
        if trailer and NfoInclude.TRAILER in nfo_include_new:
            print("  <trailer>" + trailer + "</trailer>", file=code)

        # external id
        for site, u in data.external_ids.items():
            if u:
                print(f"  <{site}id>{u}</{site}id>", file=code)
        # 没有时使用搜索关键词填充 javdbsearchid # todo 允许配置其他网站的后备字段, 允许控制是否输出该字段
        if not data.external_ids.get(Website.JAVDB):
            print(f"  <javdbsearchid>{number}</javdbsearchid>", file=code)

        print("</movie>", file=code)

        async with aiofiles.open(nfo_file, "w", encoding="UTF-8") as f:
            await f.write(code.getvalue())
            LogBuffer.log().write(f"\n 🍀 Nfo done! (new)({get_used_time(start_time)}s)")
            return True

    except Exception as e:
        LogBuffer.log().write(f"\n 🔴 Nfo failed! \n     {str(e)}")
        signal.show_traceback_log(traceback.format_exc())
        signal.show_log_text(traceback.format_exc())
        return False


async def get_nfo_data(file_path: Path, movie_number: str) -> tuple[CrawlersResult | None, OtherInfo | None]:
    local_nfo_path = file_path.with_suffix(".nfo")
    local_nfo_name = local_nfo_path.name
    file_folder = file_path.parent
    json_data = CrawlersResult.empty()
    json_data.field_sources = dict.fromkeys(CrawlerResultFields, "local")

    if not await aiofiles.os.path.exists(local_nfo_path):
        LogBuffer.error().write("nfo文件不存在")
        json_data.outline = file_path.name
        json_data.tag = str(file_path)
        return None, None

    async with aiofiles.open(local_nfo_path, encoding="utf-8") as f:
        content = await f.read()
        content = content.replace("<![CDATA[", "").replace("]]>", "")

    parser = etree.HTMLParser(encoding="utf-8")
    xml_nfo = etree.HTML(content.encode("utf-8"), parser)

    title = "".join(xml_nfo.xpath("//title/text()"))
    # 获取不到标题，表示xml错误，重新刮削
    if not title:
        LogBuffer.error().write("nfo文件损坏")
        json_data.outline = file_path.name
        json_data.tag = str(file_path)
        return None, None
    title = re.sub(r" (CD)?\d{1}$", "", title)

    # 获取其他数据
    originaltitle = "".join(xml_nfo.xpath("//originaltitle/text()"))
    number = "".join(xml_nfo.xpath("//num/text()"))
    if not number:
        number = movie_number
    letters = get_number_letters(number)
    title = title.replace(number + " ", "").strip()
    originaltitle = originaltitle.replace(number + " ", "").strip()
    originaltitle_amazon = originaltitle
    if originaltitle:
        for key, value in ManualConfig.SPECIAL_WORD.items():
            originaltitle_amazon = originaltitle_amazon.replace(value, key)
    actor = ",".join(xml_nfo.xpath("//actor/name/text()"))
    originalplot = "".join(xml_nfo.xpath("//originalplot/text()"))
    outline = ""
    temp_outline = re.findall(r"<plot>(.+)</plot>", content)
    if not temp_outline:
        temp_outline = re.findall(r"<outline>(.+)</outline>", content)
    if temp_outline:
        outline = temp_outline[0]
        if "<br>  <br>" in outline:
            temp_from = re.findall(r"<br>  <br>由 .+ 提供翻译", outline)
            if temp_from:
                outline = outline.replace(temp_from[0], "")
                json_data.outline_from = temp_from[0].replace("<br>  <br>由 ", "").replace(" 提供翻译", "")
            outline = outline.replace(originalplot, "").replace("<br>  <br>", "")
    tag = ",".join(xml_nfo.xpath("//tag/text()"))
    release = "".join(xml_nfo.xpath("//release/text()"))
    if not release:
        release = "".join(xml_nfo.xpath("//releasedate/text()"))
    if not release:
        release = "".join(xml_nfo.xpath("//premiered/text()"))
    if release:
        release = release.replace("/", "-").strip(". ")
        if len(release) < 10:
            release_list = re.findall(r"(\d{4})-(\d{1,2})-(\d{1,2})", release)
            if release_list:
                r_year, r_month, r_day = release_list[0]
                r_month = "0" + r_month if len(r_month) == 1 else r_month
                r_day = "0" + r_day if len(r_day) == 1 else r_day
                release = r_year + "-" + r_month + "-" + r_day
    json_data.release = release
    year = "".join(xml_nfo.xpath("//year/text()"))
    runtime = "".join(xml_nfo.xpath("//runtime/text()"))
    score = "".join(xml_nfo.xpath("//rating/text()"))
    if not score:
        score = "".join(xml_nfo.xpath("//rating/text()"))
        if score:
            score = str(int(score) / 10)
    series = "".join(xml_nfo.xpath("//series/text()"))
    director = ",".join(xml_nfo.xpath("//director/text()"))
    studio = "".join(xml_nfo.xpath("//studio/text()"))
    if not studio:
        studio = "".join(xml_nfo.xpath("//maker/text()"))
    publisher = "".join(xml_nfo.xpath("//publisher/text()"))
    if not publisher:
        publisher = "".join(xml_nfo.xpath("//label/text()"))
    cover = "".join(xml_nfo.xpath("//cover/text()")).replace("&amp;", "&")
    poster = "".join(xml_nfo.xpath("//poster/text()")).replace("&amp;", "&")
    trailer = "".join(xml_nfo.xpath("//trailer/text()")).replace("&amp;", "&")
    wanted = "".join(xml_nfo.xpath("//votes/text()"))

    # 判断马赛克
    if "国产" in tag or "國產" in tag:
        json_data.mosaic = "国产"
    elif "破解" in tag:
        json_data.mosaic = "无码破解"
    elif "有码" in tag or "有碼" in tag:
        json_data.mosaic = "有码"
    elif "流出" in tag:
        json_data.mosaic = "流出"
    elif "无码" in tag or "無碼" in tag or "無修正" in tag:
        json_data.mosaic = "无码"
    elif "里番" in tag or "裏番" in tag:
        json_data.mosaic = "里番"
    elif "动漫" in tag or "動漫" in tag:
        json_data.mosaic = "动漫"

    # 获取只有标签的标签（因为启用字段翻译后，会再次重复添加字幕、演员、发行、系列等字段）
    replace_keys = set(filter(None, ["：", ":"] + re.split(r"[,，]", actor)))
    temp_tag_list = list(filter(None, re.split(r"[,，]", tag.replace("中文字幕", ""))))
    only_tag_list = temp_tag_list.copy()
    for each_tag in temp_tag_list:
        for each_key in replace_keys:
            if each_key in each_tag:
                only_tag_list.remove(each_tag)
                break
    tag_only = ",".join(only_tag_list)

    # 获取本地图片路径
    poster_path_1 = file_path.with_name(file_path.stem + "-poster.jpg")
    poster_path_2 = file_folder / "poster.jpg"
    thumb_path_1 = file_path.with_name(file_path.stem + "-thumb.jpg")
    thumb_path_2 = file_folder / "thumb.jpg"
    fanart_path_1 = file_path.with_name(file_path.stem + "-fanart.jpg")
    fanart_path_2 = file_folder / "fanart.jpg"
    if await aiofiles.os.path.isfile(poster_path_1):
        poster_path = poster_path_1
    elif await aiofiles.os.path.isfile(poster_path_2):
        poster_path = poster_path_2
    else:
        poster_path = None
    if await aiofiles.os.path.isfile(thumb_path_1):
        thumb_path = thumb_path_1
    elif await aiofiles.os.path.isfile(thumb_path_2):
        thumb_path = thumb_path_2
    else:
        thumb_path = None
    if await aiofiles.os.path.isfile(fanart_path_1):
        fanart_path = fanart_path_1
    elif await aiofiles.os.path.isfile(fanart_path_2):
        fanart_path = fanart_path_2
    else:
        fanart_path = None

    # 返回数据
    json_data.title = title
    if (
        manager.config.get_field_config(CrawlerResultFields.TITLE).language == Language.JP
        and ReadMode.READ_UPDATE_NFO in manager.config.read_mode
        and originaltitle
    ):
        json_data.title = originaltitle
    json_data.originaltitle = originaltitle
    if is_japanese(originaltitle):
        json_data.originaltitle_amazon = originaltitle
        if actor:
            json_data.actor_amazon = actor.split(",")
    json_data.number = number
    json_data.letters = letters
    json_data.actor = actor
    json_data.all_actor = actor
    json_data.outline = outline
    if (
        manager.config.get_field_config(CrawlerResultFields.OUTLINE).language == Language.JP
        and ReadMode.READ_UPDATE_NFO in manager.config.read_mode
        and originalplot
    ):
        json_data.outline = originalplot
    json_data.originalplot = originalplot
    json_data.tag = tag
    if ReadMode.READ_UPDATE_NFO in manager.config.read_mode:
        json_data.tag = tag_only
    json_data.release = release
    json_data.year = year
    json_data.runtime = runtime
    json_data.score = score
    json_data.director = director
    json_data.series = series
    json_data.studio = studio
    json_data.publisher = publisher
    # json_data.website = website
    json_data.thumb = cover
    if cover:
        json_data.thumb_list.append(("local", cover))
    json_data.poster = poster
    json_data.trailer = trailer
    json_data.wanted = wanted
    info = OtherInfo.empty()
    info.poster_path = poster_path
    info.thumb_path = thumb_path
    info.fanart_path = fanart_path
    LogBuffer.log().write(f"\n 📄 [NFO] {local_nfo_name}")
    signal.show_traceback_log(f"{number} {json_data.mosaic}")
    return json_data, info
