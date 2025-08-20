#!/usr/bin/env python3
import re
import time

from lxml import etree

from mdcx.config.manager import manager
from mdcx.models.log_buffer import LogBuffer

seesaawiki_request_fail_flag = False


def get_title(html):
    result = html.xpath('//p[contains(@class, "sub_title")]/text()')
    return result[0] if result else ""


def get_actor_photo(actor):
    actor = actor.split(",")
    data = {}
    for i in actor:
        actor_photo = {i: ""}
        data.update(actor_photo)
    return data


def get_cover(key):
    return (
        f"https://www.kin8tengoku.com/{key}/pht/1.jpg",
        f"https://smovie.kin8tengoku.com/sample_mobile_template/{key}/hls-1800k.mp4",
    )


def get_outline(html):
    result = html.xpath('normalize-space(string(//div[@id="comment"]))')
    return result.strip()


def get_actor(html):
    result = html.xpath('//div[@class="icon"]/a[contains(@href, "listpages/actor")]/text()')
    return ",".join(result)


def get_tag(html):
    result = html.xpath(
        '//td[@class="movie_table_td" and contains(text(), "カテゴリー")]/following-sibling::td/div/a/text()'
    )
    return ",".join(result)


def get_release(html):
    return html.xpath('string(//td[@class="movie_table_td" and contains(text(), "更新日")]/following-sibling::td)')


def get_year(release):
    result = re.search(r"\d{4}", release)
    return result[0] if result else release


def get_runtime(html):
    s = html.xpath('string(//td[@class="movie_table_td" and contains(text(), "再生時間")]/following-sibling::td)')
    runtime = ""
    if ":" in s:
        temp_list = s.split(":")
        if len(temp_list) == 3:
            runtime = int(temp_list[0]) * 60 + int(temp_list[1])
        elif len(temp_list) <= 2:
            runtime = int(temp_list[0])
    return str(runtime)


def get_extrafanart(html):
    result = html.xpath("//img[@class='white_gallery ']/@src")
    new_result = []
    for i in result:
        if i:
            if "http" not in i:
                i = f"https:{i}"
            new_result.append(
                i.replace("/2.jpg", "/2_lg.jpg").replace("/3.jpg", "/3_lg.jpg").replace("/4.jpg", "/4_lg.jpg")
            )
    return new_result


async def main(
    number,
    appoint_url="",
    **kwargs,
):
    start_time = time.time()
    website_name = "kin8"
    LogBuffer.req().write(f"-> {website_name}")
    real_url = appoint_url
    cover_url = ""
    image_cut = ""
    image_download = False
    web_info = "\n       "
    LogBuffer.info().write(" \n    🌐 kin8")
    debug_info = ""
    try:
        if real_url:
            key = re.findall(r"\d{3,}", real_url)
            key = key[0] if key else ""
            assert isinstance(key, str)
            number = f"KIN8-{key}" if key else number
        else:
            key = re.findall(r"KIN8(TENGOKU)?-?(\d{3,})", number.upper())
            key = key[0][1] if key else ""
            assert isinstance(key, str)
            if not key:
                debug_info = f"番号中未识别到 KIN8 番号: {number} "
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)
            number = f"KIN8-{key}"
            real_url = f"https://www.kin8tengoku.com/moviepages/{key}/index.html"

        debug_info = f"番号地址: {real_url} "
        LogBuffer.info().write(web_info + debug_info)
        html_content, error = await manager.computed.async_client.get_text(real_url, encoding="euc-jp")
        if html_content is None:
            debug_info = f"网络请求错误: {error} "
            LogBuffer.info().write(web_info + debug_info)
            raise Exception(debug_info)

        html_info = etree.fromstring(html_content, etree.HTMLParser())
        title = get_title(html_info)
        if not title:
            debug_info = "数据获取失败: 未获取到title！"
            LogBuffer.info().write(web_info + debug_info)
            raise Exception(debug_info)
        outline = get_outline(html_info)
        actor = get_actor(html_info)
        actor_photo = get_actor_photo(actor)
        cover_url, trailer = get_cover(key)
        poster = cover_url
        extrafanart = get_extrafanart(html_info)
        studio = "kin8tengoku"
        release = get_release(html_info)
        year = get_year(release)
        runtime = get_runtime(html_info)
        tag = get_tag(html_info)
        score = ""
        series = ""
        director = ""
        publisher = "kin8tengoku"
        mosaic = "无码"
        try:
            dic = {
                "number": number,
                "title": title,
                "originaltitle": title,
                "actor": actor,
                "outline": outline,
                "originalplot": outline,
                "tag": tag,
                "release": release,
                "year": year,
                "runtime": runtime,
                "score": score,
                "series": series,
                "director": director,
                "studio": studio,
                "publisher": publisher,
                "source": "kin8",
                "actor_photo": actor_photo,
                "thumb": cover_url,
                "poster": poster,
                "extrafanart": extrafanart,
                "trailer": trailer,
                "image_download": image_download,
                "image_cut": image_cut,
                "mosaic": mosaic,
                "website": real_url,
                "wanted": "",
            }
            debug_info = "数据获取成功！"
            LogBuffer.info().write(web_info + debug_info)

        except Exception as e:
            debug_info = f"数据生成出错: {str(e)}"
            LogBuffer.info().write(web_info + debug_info)
            raise Exception(debug_info)
    except Exception as e:
        # print(traceback.format_exc())
        LogBuffer.error().write(str(e))
        dic = {
            "title": "",
            "thumb": "",
            "website": "",
        }
    dic = {website_name: {"zh_cn": dic, "zh_tw": dic, "jp": dic}}
    LogBuffer.req().write(f"({round(time.time() - start_time)}s) ")
    return dic


if __name__ == "__main__":
    # yapf: disable
    # print(main('kin8-3681'))
    print(main(number="", appoint_url="https://www.kin8tengoku.com/moviepages/1232/index.html"))
