#!/usr/bin/python
import re
import time

from lxml import etree

from mdcx.config.manager import config
from mdcx.models.log_buffer import LogBuffer


def getTitle(html):
    result = html.xpath('//span[@id="program_detail_title"]/text()')
    if result:
        result = result[0]
    else:
        result = ""
    return result


def getWebNumber(html, number):
    result = html.xpath('//span[@id="hinban"]/text()')
    return result[0] if result else number


def getActor(html):
    try:
        result = str(html.xpath('//li[@class="credit-links"]/a/text()')).strip("['']").replace("'", "")
    except Exception:
        result = ""
    return result


def getActorPhoto(actor):
    actor = actor.split(",")
    d = {}
    for i in actor:
        if "," not in i:
            p = {i: ""}
            d.update(p)
    return d


def getCover(html):
    result = html.xpath('//div[@class="photo"]/p/a/@href')
    if result:
        result = "https:" + result[0]
    else:
        result = ""
    return result


def getOutline(html):
    result = html.xpath('//p[@class="lead"]/text()')
    if result:
        result = result[0].strip().replace('"', "")
    else:
        result = ""
    return result


def getRelease(html):
    result = html.xpath('//li/span[@class="koumoku" and (contains(text(), "発売日"))]/../text()')
    result = re.findall(r"[\d]+/[\d]+/[\d]+", str(result))
    if result:
        result = result[0].replace("/", "-")
    else:
        result = ""
    return result


def getYear(release):
    try:
        result = str(re.search(r"\d{4}", release).group())
        return result
    except Exception:
        return release[:4]


def getTag(html):
    result = html.xpath('//a[@class="genre"]/text()')
    if result:
        result = str(result).strip(" ['']").replace("'", "").replace(", ", ",").replace("\\n", "").replace("\\t", "")
    else:
        result = ""
    return result


def getStudio(html):
    result = html.xpath('//span[@id="program_detail_maker_name"]/text()')
    if result:
        result = result[0].strip()
    else:
        result = ""
    return result


def getPublisher(html):
    result = html.xpath('//span[@id="program_detail_label_name"]/text()')
    if result:
        result = result[0].strip()
    else:
        result = ""
    return result


def getRuntime(html):
    result = str(html.xpath('//span[@class="koumoku"][contains(text(), "収録時間")]/../text()'))
    result = re.findall(r"[\d]+", result)
    if result:
        result = result[0].strip()
    else:
        result = ""
    return result


def getDirector(html):
    result = html.xpath('//span[@id="program_detail_director"]/text()')
    if result:
        result = result[0].replace("\\n", "").replace("\\t", "").strip()
    else:
        result = ""
    return result


def getExtrafanart(html):
    result = html.xpath('//a[contains(@class, "thumb")]/@href')
    if result:
        result = (
            str(result)
            .replace("//faws.xcity.jp/scene/small/", "https://faws.xcity.jp/")
            .strip(" []")
            .replace("'", "")
            .replace(", ", ",")
        )
        result = result.split(",")
    else:
        result = ""
    return result


def getCoverSmall(html):
    result = html.xpath('//img[@class="packageThumb"]/@src')
    if result:
        result = "https:" + result[0]
    else:
        result = ""
    return result.replace("package/medium/", "")


def getSeries(html):
    result = html.xpath('//a[contains(@href, "series")]/span/text()')
    if result:
        result = result[0]
    else:
        result = ""
    return result


async def main(
    number,
    appoint_url="",
    **kwargs,
):
    start_time = time.time()
    website_name = "xcity"
    LogBuffer.req().write(f"-> {website_name}")

    headers_o = config.headers
    real_url = appoint_url
    cover_url = ""
    poster_url = ""
    image_download = False
    image_cut = "right"
    dic = {}
    web_info = "\n       "
    LogBuffer.info().write(" \n    🌐 xcity")
    debug_info = ""

    try:
        if not real_url:
            url_search = "https://xcity.jp/result_published/?q=" + number.replace("-", "")
            debug_info = f"搜索地址: {url_search} "
            LogBuffer.info().write(web_info + debug_info)

            html_search, error = await config.async_client.get_text(url_search)
            if html_search is None:
                debug_info = f"网络请求错误: {error} "
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)
            if "該当する作品はみつかりませんでした" in html_search:
                debug_info = "搜索结果: 未匹配到番号！"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)
            html = etree.fromstring(html_search, etree.HTMLParser())
            real_url = html.xpath("//table[@class='resultList']/tr/td/a/@href")
            if not real_url:
                debug_info = "搜索结果: 未匹配到番号！"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)
            else:
                real_url = "https://xcity.jp" + real_url[0]

        if real_url:
            debug_info = f"番号地址: {real_url} "
            LogBuffer.info().write(web_info + debug_info)
            html_content, error = await config.async_client.get_text(real_url)
            if html_content is None:
                debug_info = f"网络请求错误: {error} "
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)
            html_info = etree.fromstring(html_content, etree.HTMLParser())

            title = getTitle(html_info)  # 获取标题
            if not title:
                debug_info = "数据获取失败: 未获取到title！"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)
            web_number = getWebNumber(html_info, number)  # 获取番号，用来替换标题里的番号
            title = title.replace(f" {web_number}", "").strip()
            actor = getActor(html_info)  # 获取actor
            actor_photo = getActorPhoto(actor)
            cover_url = getCover(html_info)  # 获取cover
            outline = getOutline(html_info)
            release = getRelease(html_info)
            year = getYear(release)
            tag = getTag(html_info)
            studio = getStudio(html_info)
            publisher = getPublisher(html_info)
            runtime = getRuntime(html_info)
            director = getDirector(html_info)
            extrafanart = getExtrafanart(html_info)
            poster_url = getCoverSmall(html_info)
            score = ""
            series = getSeries(html_info)
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
                    "source": "xcity",
                    "website": real_url,
                    "actor_photo": actor_photo,
                    "thumb": cover_url,
                    "poster": poster_url,
                    "extrafanart": extrafanart,
                    "trailer": "",
                    "image_download": image_download,
                    "image_cut": image_cut,
                    "mosaic": "有码",
                    "wanted": "",
                }

                debug_info = "数据获取成功！"
                LogBuffer.info().write(web_info + debug_info)

            except Exception as e:
                debug_info = f"数据生成出错: {str(e)}"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)

    except Exception as e:
        LogBuffer.error().write(str(e))
        dic = {
            "title": "",
            "thumb": "",
            "website": "",
        }
    dic = {website_name: {"zh_cn": dic, "zh_tw": dic, "jp": dic}}
    LogBuffer.req().write(f"({round((time.time() - start_time))}s) ")
    return dic


if __name__ == "__main__":
    print(
        main("STVF010")
    )  # print(main('MXGS563'))  # print(main('xc-1280'))  # print(main('xv-163'))  # print(main('sea-081'))  # print(main('IA-28'))  # print(main('xc-1298'))  # print(main('DMOW185'))  # print(main('EMOT007'))  # print(main('EMOT007', "https://xcity.jp/avod/detail/?id=147036"))
