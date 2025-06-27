#!/usr/bin/env python3
import json
import re
import time  # yapf: disable # NOQA: E402

import urllib3
from lxml import etree

from models.base.web import get_avsox_domain
from models.base.web_compat import get_text
from models.core.json_data import LogBuffer

urllib3.disable_warnings()  # yapf: disable


# import traceback
# import Function.config as cf


def get_actor_photo(actor):
    actor = actor.split(",")
    data = {}
    for i in actor:
        actor_photo = {i: ""}
        data.update(actor_photo)
    return data


def get_actor(html):
    result = ",".join(html.xpath("//div[@id='avatar-waterfall']/a/span/text()"))
    return result


def get_web_number(html):
    result = html.xpath('//div[@class="col-md-3 info"]/p/span[@style="color:#CC0000;"]/text()')
    return result[0] if result else ""


def get_title(html):
    result = html.xpath('//div[@class="container"]/h3/text()')
    return result[0] if result else ""


def get_cover(html):
    result = html.xpath('//a[@class="bigImage"]/@href')
    return result[0] if result else ""


def get_poster(html, count):
    poster_url = html.xpath("//div[@id='waterfall']/div[" + str(count) + "]/a/div[@class='photo-frame']/img/@src")[0]
    return poster_url


def get_tag(html):
    result = html.xpath('//span[@class="genre"]/a/text()')
    return ",".join(result)


def get_release(html):
    result = html.xpath(
        '//span[contains(text(),"发行时间:") or contains(text(),"發行日期:") or contains(text(),"発売日:")]/../text()'
    )
    return result[0].strip() if result else ""


def get_year(release):
    return release[:4] if release else release


def get_runtime(html):
    result = html.xpath(
        '//span[contains(text(),"长度:") or contains(text(),"長度:") or contains(text(),"収録時間:")]/../text()'
    )
    return re.findall(r"(\d+)", result[0])[0] if result else ""


def get_series(html):
    result = html.xpath('//p/a[contains(@href,"/series/")]/text()')
    return result[0].strip() if result else ""


def get_studio(html):
    result = html.xpath('//p/a[contains(@href,"/studio/")]/text()')
    return result[0].strip() if result else ""


def get_real_url(number, html):
    page_url = ""
    url_list = html.xpath('//*[@id="waterfall"]/div/a/@href')
    i = 0
    if url_list:
        for i in range(1, len(url_list) + 1):
            number_get = str(
                html.xpath('//*[@id="waterfall"]/div[' + str(i) + ']/a/div[@class="photo-info"]/span/date[1]/text()')
            ).strip(" ['']")
            if number.upper().replace("-PPV", "") == number_get.upper().replace("-PPV", ""):
                page_url = "https:" + url_list[i - 1]
                break
    return page_url, i


def main(
    number,
    appoint_url="",
    language="jp",
):
    start_time = time.time()
    website_name = "avsox"
    LogBuffer.req().write(f"-> {website_name}")
    real_url = appoint_url
    title = ""
    cover_url = ""
    poster_url = ""
    image_download = False
    image_cut = "center"
    dic = {}
    web_info = "\n       "
    LogBuffer.info().write(" \n    🌐 avsox")
    debug_info = ""

    try:
        if not real_url:
            avsox_url = get_avsox_domain()
            url_search = f"{avsox_url}/cn/search/{number}"
            debug_info = f"搜索地址: {url_search} "
            LogBuffer.info().write(web_info + debug_info)
            response, error = get_text(url_search)
            if response is None:
                debug_info = f"网络请求错误: {error}"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)
            html_search = etree.fromstring(response, etree.HTMLParser())
            real_url, count = get_real_url(number, html_search)
            if not real_url:
                debug_info = "搜索结果: 未匹配到番号！"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)
            poster_url = get_poster(html_search, count)
            if poster_url:
                image_download = True

        debug_info = f"番号地址: {real_url} "
        LogBuffer.info().write(web_info + debug_info)
        htmlcode, error = get_text(real_url)
        if htmlcode is None:
            debug_info = f"网络请求错误: {error}"
            LogBuffer.info().write(web_info + debug_info)
            raise Exception(debug_info)
        html = etree.fromstring(htmlcode, etree.HTMLParser())
        actor = get_actor(html)
        actor_photo = get_actor_photo(actor)
        web_number = get_web_number(html)
        title = get_title(html).replace(web_number + " ", "").strip()
        if not title:
            debug_info = "数据获取失败: 未获取到title！"
            LogBuffer.info().write(web_info + debug_info)
            raise Exception(debug_info)
        cover_url = get_cover(html)
        tag = get_tag(html)
        release = get_release(html)
        year = get_year(release)
        runtime = get_runtime(html)
        series = get_series(html)
        studio = get_studio(html)
        try:
            dic = {
                "number": number,
                "title": title,
                "originaltitle": title,
                "actor": actor,
                "actor_photo": actor_photo,
                "outline": "",
                "originalplot": "",
                "tag": tag,
                "release": release,
                "year": year,
                "runtime": runtime,
                "score": "",
                "series": series,
                "director": "",
                "studio": studio,
                "publisher": studio,
                "source": "avsox",
                "website": real_url,
                "cover": cover_url,
                "poster": poster_url,
                "extrafanart": "",
                "trailer": "",
                "image_download": image_download,
                "image_cut": image_cut,
                "mosaic": "无码",
                "wanted": "",
            }
            debug_info = "数据获取成功！"
            LogBuffer.info().write(web_info + debug_info)

        except Exception as e:
            debug_info = f"数据生成出错: {str(e)}"
            LogBuffer.info().write(web_info + debug_info)
            raise Exception(debug_info)

    except Exception as e:
        # cf.add_log(traceback.format_exc())
        LogBuffer.error().write(str(e))
        dic = {
            "title": "",
            "cover": "",
            "website": "",
        }
    dic = {website_name: {"zh_cn": dic, "zh_tw": dic, "jp": dic}}
    js = json.dumps(
        dic,
        ensure_ascii=False,
        sort_keys=False,
        indent=4,
        separators=(",", ": "),
    )  # .encode('UTF-8')
    LogBuffer.req().write(f"({round((time.time() - start_time))}s) ")
    return js


if __name__ == "__main__":
    # print(main('051119-917'))
    # print(main('EDVR-063 '))
    # print(main('032620_001'))
    print(
        main("FC2-2101993")
    )  # print(main('032620_001', 'https://avsox.click/cn/movie/cb8d28437cff4e90'))  # print(main('', 'https://avsox.click/cn/movie/0b4e42a270b9871b'))
