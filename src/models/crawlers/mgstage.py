#!/usr/bin/env python3
import re
import time  # yapf: disable # NOQA: E402

import urllib3
from lxml import etree

from models.config.manager import config
from models.core.json_data import LogBuffer

urllib3.disable_warnings()  # yapf: disable


# import Function.config as cf
# import traceback


def getTitle(html):
    try:
        result = str(html.xpath('//*[@id="center_column"]/div[1]/h1/text()')).strip(" ['']")
        return result.replace("/", ",")
    except Exception:
        return ""


def getActor(html):
    result = (
        str(html.xpath('//th[contains(text(),"出演")]/../td/a/text()'))
        .replace("\\n", "")
        .strip(" ['']")
        .replace("/", ",")
        .replace("'", "")
        .replace(" ", "")
    )
    if not result:
        result = (
            str(html.xpath('//th[contains(text(),"出演")]/../td/text()'))
            .replace("\\n", "")
            .strip(" ['']")
            .replace("/", ",")
            .replace("'", "")
            .replace(" ", "")
        )
    return result


def getActorPhoto(actor):
    d = {}
    for i in actor:
        if "," not in i or ")" in i:
            p = {i: ""}
            d.update(p)
    return d


def getStudio(html):
    result1 = str(html.xpath('//th[contains(text(),"メーカー：")]/../td/a/text()')).strip(" ['']")
    result2 = str(html.xpath('//th[contains(text(),"メーカー：")]/../td/text()')).strip(" ['']")
    return str(result1 + result2).replace("'", "").replace(" ", "").replace("\\n", "")


def getPublisher(html):
    result1 = str(html.xpath('//th[contains(text(),"レーベル：")]/../td/a/text()')).strip(" ['']")
    result2 = str(html.xpath('//th[contains(text(),"レーベル：")]/../td/text()')).strip(" ['']")
    return str(result1 + result2).replace("'", "").replace(" ", "").replace("\\n", "")


def getRuntime(html):
    result1 = str(html.xpath('//th[contains(text(),"収録時間：")]/../td/a/text()')).strip(" ['']")
    result2 = str(html.xpath('//th[contains(text(),"収録時間：")]/../td/text()')).strip(" ['']")
    return str(result1 + result2).rstrip("min").replace("'", "").replace(" ", "").replace("\\n", "")


def getSeries(html):
    result1 = str(html.xpath('//th[contains(text(),"シリーズ：")]/../td/a/text()')).strip(" ['']")
    result2 = str(html.xpath('//th[contains(text(),"シリーズ：")]/../td/text()')).strip(" ['']")
    return str(result1 + result2).replace("'", "").replace(" ", "").replace("\\n", "")


def getNum(html):
    result1 = str(html.xpath('//th[contains(text(),"品番：")]/../td/a/text()')).strip(" ['']")
    result2 = str(html.xpath('//th[contains(text(),"品番：")]/../td/text()')).strip(" ['']")
    return str(result1 + result2).replace("'", "").replace(" ", "").replace("\\n", "")


def getYear(getRelease):
    try:
        result = str(re.search(r"\d{4}", getRelease).group())
        return result
    except Exception:
        return getRelease


def getRelease(html):
    result1 = str(html.xpath('//th[contains(text(),"配信開始日：")]/../td/a/text()')).strip(" ['']")
    result2 = str(html.xpath('//th[contains(text(),"配信開始日：")]/../td/text()')).strip(" ['']")
    return str(result1 + result2).replace("'", "").replace(" ", "").replace("\\n", "")


def getTag(html):
    result1 = str(html.xpath('//th[contains(text(),"ジャンル：")]/../td/a/text()')).strip(" ['']")
    result2 = str(html.xpath('//th[contains(text(),"ジャンル：")]/../td/text()')).strip(" ['']")
    return str(result1 + result2).replace("'", "").replace(" ", "").replace("\\n", "")


def getCoverSmall(cover_url):
    result = cover_url.replace("/pb_", "/pf_")
    return result


def getCover(html):
    result = str(html.xpath('//a[@id="EnlargeImage"]/@href')).strip(" ['']")
    return result


def getExtraFanart(html):
    extrafanart_list = html.xpath("//dl[@id='sample-photo']/dd/ul/li/a[@class='sample_image']/@href")
    return extrafanart_list


async def get_trailer(html):
    trailer = ""
    play_url = html.xpath("//a[@class='review-btn']/@href")
    if play_url:
        play_url = play_url[0].replace("/mypage/review.php", "/sampleplayer/sampleRespons.php")
        htmlcode, error = await config.async_client.get_json(play_url, cookies={"adc": "1"})
        if htmlcode is not None:
            url_str = htmlcode.get("url")
            if url_str:
                url_temp = re.search(r"(https.+)ism/request", str(url_str))
                if url_temp:
                    trailer = url_temp.group(1) + "mp4"
    return trailer


def getOutline(html):
    result = str(html.xpath('//*[@id="introduction"]/dd/p[1]/text()')).strip(" ['']")
    if not result:
        temp = html.xpath('//*[@id="introduction"]/dd')
        result = temp[0].xpath("string(.)").replace(" ", "").strip() if temp else ""
    return result


def getScore(html):
    result = html.xpath('//td[@class="review"]/span/@class')
    if result:
        result = f"{int(result[0].replace('star_', '')[:2]) / 10:.1f}"
    return str(result)


async def main(
    number,
    appoint_url="",
    short_number="",
    **kwargs,
):
    start_time = time.time()
    website_name = "mgstage"
    LogBuffer.req().write(f"-> {website_name}")
    real_url = appoint_url
    title = ""
    cover_url = ""
    poster_url = ""
    image_download = True
    image_cut = "right"
    dic = {}
    web_info = "\n       "
    LogBuffer.info().write(" \n    🌐 mgstage")
    debug_info = ""

    try:
        if not real_url:
            number = number.upper()
            short_number = short_number.upper()
            real_url_list = [f"https://www.mgstage.com/product/product_detail/{number}/"]
            if short_number and short_number != number:
                real_url_list.append(f"https://www.mgstage.com/product/product_detail/{short_number}/")
        else:
            real_url_list = [real_url]
        for real_url in real_url_list:
            debug_info = f"番号地址: {real_url} "
            LogBuffer.info().write(web_info + debug_info)
            htmlcode, error = await config.async_client.get_text(real_url, cookies={"adc": "1"})
            if htmlcode is None:
                debug_info = f"网络请求错误: {error} "
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)
            if not htmlcode.strip():
                debug_info = "返回为空，请更换代理"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)
            htmlcode = etree.fromstring(htmlcode, etree.HTMLParser())
            actor = getActor(htmlcode).replace(" ", "").strip(",")
            title = getTitle(htmlcode).replace("\\n", "").replace("        ", "").strip(",").strip()  # 获取标题
            if title:
                break
            else:
                debug_info = "数据获取失败: 未获取到title！"
                LogBuffer.info().write(web_info + debug_info)
        else:
            raise Exception(debug_info)
        cover_url = getCover(htmlcode)  # 获取cover
        poster_url = getCoverSmall(cover_url)  # 获取cover
        outline = getOutline(htmlcode).replace("\n", "").strip(",")
        release = getRelease(htmlcode).strip(",").replace("/", "-")
        tag = getTag(htmlcode).strip(",")
        year = getYear(release).strip(",")
        runtime = getRuntime(htmlcode).strip(",")
        score = getScore(htmlcode).strip(",")
        series = getSeries(htmlcode).strip(",")
        studio = getStudio(htmlcode).strip(",")
        publisher = getPublisher(htmlcode).strip(",")
        actor_photo = getActorPhoto(actor.split(","))
        extrafanart = getExtraFanart(htmlcode)
        trailer = await get_trailer(htmlcode)
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
                "director": "",
                "studio": studio,
                "publisher": publisher,
                "source": "mgstage",
                "website": real_url,
                "actor_photo": actor_photo,
                "thumb": cover_url,
                "poster": poster_url,
                "extrafanart": extrafanart,
                "trailer": trailer,
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
        # print(traceback.format_exc())
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
    # print(main('300MIUM-696', ''))
    # print(main('200GANA-2506'))
    # print(main('406FSDSS-534'))
    # print(main('428SUKE-144', short_number='SUKE-144'))
    # print(main('abp-419', ''))
    # print(main('300MIUM-382', ''))
    # print(main('345SIMM-653'))
    # print(main('SIRO-4605'))
    # print(main('200GANA-2240'))
    # print(main('200GANA-2240'))
    # print(main('SIRO-4042'))
    # print(main('300MIUM-382'))
    # print(main('383reiw-043', ''))
    print(main("300MIUM-382", "https://www.mgstage.com/product/product_detail/300MIUM-382/"))
