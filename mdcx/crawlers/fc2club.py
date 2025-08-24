#!/usr/bin/env python3
import re
import time

from lxml import etree

from ..config.manager import manager
from ..models.log_buffer import LogBuffer


def getTitle(html, number):  # 获取标题
    result = html.xpath("//h3/text()")
    result = result[0].replace(f"FC2-{number} ", "") if result else ""
    return result


def getNum(html):  # 获取番号
    result = html.xpath("//h1/text()")
    result = result[0] if result else ""
    return result


def getCover(html):  # 获取封面
    extrafanart = []
    result = html.xpath('//img[@class="responsive"]/@src')
    if result:
        for res in result:
            extrafanart.append(res.replace("../uploadfile", "https://fc2club.top/uploadfile"))
        result = result[0].replace("../uploadfile", "https://fc2club.top/uploadfile")
    else:
        result = ""
    return result, extrafanart


def getStudio(html):  # 使用卖家作为厂家
    result = html.xpath('//strong[contains(text(), "卖家信息")]/../a/text()')
    result = result[0].strip() if result else ""
    return result.replace("本资源官网地址", "")


def getScore(html):  # 获取评分
    try:
        result = html.xpath('//strong[contains(text(), "影片评分")]/../text()')
        result = re.findall(r"\d+", result[0])[0]
    except Exception:
        result = ""
    return result


def getActor(html, studio):  # 获取演员
    result = html.xpath('//strong[contains(text(), "女优名字")]/../a/text()')
    if result:
        result = str(result).strip(" []").replace('"', "").replace("'", "").replace(", ", ",")
    else:
        result = studio if "fc2_seller" in manager.config.fields_rule else ""
    return result


def getActorPhoto(actor):  # 获取演员头像
    actor_photo = {}
    actor_list = actor.split(",")
    for act in actor_list:
        actor_photo[act] = ""
    return actor_photo


def getTag(html):  # 获取标签
    result = html.xpath('//strong[contains(text(), "影片标签")]/../a/text()')
    result = str(result).strip(" []").replace('"', "").replace("'", "").replace(", ", ",")
    return result


def getOutline(html):  # 获取简介
    result = (
        str(html.xpath('//div[@class="col des"]/text()'))
        .strip("[]")
        .replace("',", "")
        .replace("\\n", "")
        .replace("'", "")
        .replace("・", "")
        .strip()
    )
    return result


def getMosaic(html):  # 获取马赛克
    result = str(html.xpath('//h5/strong[contains(text(), "资源参数")]/../text()'))
    mosaic = "无码" if "无码" in result else "有码"
    return mosaic


async def main(
    number,
    appoint_url="",
    **kwargs,
):
    start_time = time.time()
    website_name = "fc2club"
    LogBuffer.req().write(f"-> {website_name}")
    real_url = appoint_url
    title = ""
    cover_url = ""
    number = number.upper().replace("FC2PPV", "").replace("FC2-PPV-", "").replace("FC2-", "").replace("-", "").strip()
    dic = {}
    web_info = "\n       "
    LogBuffer.info().write(" \n    🌐 fc2club")
    debug_info = ""

    try:  # 捕获主动抛出的异常
        if not real_url:
            real_url = f"https://fc2club.top/html/FC2-{number}.html"

        debug_info = f"番号地址: {real_url} "
        LogBuffer.info().write(web_info + debug_info)

        # ========================================================================搜索番号
        html_content, error = await manager.computed.async_client.get_text(real_url)
        if html_content is None:
            debug_info = f"网络请求错误: {error}"
            LogBuffer.info().write(web_info + debug_info)
            raise Exception(debug_info)
        html_info = etree.fromstring(html_content, etree.HTMLParser())

        title = getTitle(html_info, number)  # 获取标题
        if not title:
            debug_info = "数据获取失败: 未获取到title！"
            LogBuffer.info().write(web_info + debug_info)
            raise Exception(debug_info)

        cover_url, extrafanart = getCover(html_info)  # 获取cover
        # outline = getOutline(html_info)
        tag = getTag(html_info)
        studio = getStudio(html_info)  # 获取厂商
        score = getScore(html_info)  # 获取厂商
        actor = getActor(html_info, studio)  # 获取演员
        actor_photo = getActorPhoto(actor)  # 获取演员列表
        mosaic = getMosaic(html_info)
        try:
            dic = {
                "number": "FC2-" + str(number),
                "title": title,
                "originaltitle": title,
                "actor": actor,
                "outline": "",
                "originalplot": "",
                "tag": tag,
                "release": "",
                "year": "",
                "runtime": "",
                "score": score,
                "series": "FC2系列",
                "director": "",
                "studio": studio,
                "publisher": studio,
                "source": "fc2club",
                "website": str(real_url).strip("[]"),
                "actor_photo": actor_photo,
                "thumb": cover_url,
                "poster": "",
                "extrafanart": extrafanart,
                "trailer": "",
                "image_download": False,
                "image_cut": "center",
                "mosaic": mosaic,
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
    LogBuffer.req().write(f"({round(time.time() - start_time)}s) ")
    return dic


if __name__ == "__main__":
    # print(main('1470588', ''))
    print(
        main("743423", "")
    )  # print(main('674261', ''))  # print(main('406570', ''))  # print(main('1474843', ''))  # print(main('1860858', ''))  # print(main('1599412', ''))  # print(main('1131214', ''))  # print(main('1837553', ''))  # print(main('1613618', ''))  # print(main('1837553', ''))  # print(main('1837589', ""))  # print(main('1760182', ''))  # print(main('1251689', ''))  # print(main('674239', ""))  # print(main('674239', "))
