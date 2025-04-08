#!/usr/bin/env python3
import json
import re
import time
from datetime import datetime

import requests
import urllib3
from lxml import etree

from models.base.web import curl_html
from models.config.config import config

urllib3.disable_warnings()  # yapf: disable


def get_actor_photo(actor):
    """
    获取演员照片信息的字典
    :param actor: 演员名字符串，以逗号分隔
    :return: 包含演员名和照片URL的字典
    """
    actor = actor.split(",")
    data = {}
    for i in actor:
        actor_photo = {i: ""}
        data.update(actor_photo)
    return data


def get_detail_info(html, number, file_path):
    """
    从详情页HTML中提取影片信息
    :param html: HTML解析后的元素树
    :param number: 影片番号
    :param file_path: 文件路径
    :return: 提取的各种元数据
    """
    # 解析标题
    title_h1 = html.xpath('//meta[@property="og:title"]/@content')
    title = title_h1[0] if title_h1 else number

    # 解析发行日期
    release_date = ""
    release_nodes = html.xpath(
        '//div[contains(@class, "field--name-field-video-date")]//time/@datetime'
    )
    if release_nodes:
        try:
            date_text = release_nodes[0]
            date_obj = datetime.strptime(date_text.split("T")[0], "%Y-%m-%d")
            release = date_obj.strftime("%Y-%m-%d")
            year = str(date_obj.year)
        except:
            release = ""
            year = ""
    else:
        release = ""
        year = ""

    # 解析演员信息
    actors = html.xpath(
        '//div[contains(@class, "field--name-field-video-actor")]//div[@class="field--item"]/a/text()'
    )
    actor = ",".join([a.strip().lstrip("#") for a in actors]) if actors else ""

    # 解析标签
    tags = html.xpath(
        '//div[contains(@class, "field--name-field-video-tags")]//div[@class="field--item"]/a/text()'
    )
    tag = ",".join([t.strip().lstrip("#") for t in tags]) if tags else ""

    # 解析封面图片
    cover_url = html.xpath('//meta[@property="og:image"]/@content')
    cover_url = cover_url[0] if cover_url else ""

    # 解析频道/类别
    studio = html.xpath(
        '//div[contains(@class, "field--name-field-video-channel")]//div[@class="field--item"]/a/text()'
    )
    studio = studio[0].strip() if studio else ""

    # 解析影片类型（无码、有码等）
    video_type = html.xpath(
        '//div[contains(@class, "field--name-field-video-type")]//div[@class="field--item"]/a/text()'
    )
    video_type = video_type[0].strip() if video_type else ""

    # 解析描述
    description = html.xpath('//meta[@name="description"]/@content')
    outline = description[0] if description else ""

    # 解析视频链接
    video_url = ""
    video_scripts = html.xpath('//script[contains(text(), "m3u8")]/text()')
    for script in video_scripts:
        m3u8_match = re.search(r'source\s*=\s*[\'"]([^"\']+\.m3u8)[\'"]', script)
        if m3u8_match:
            video_url = m3u8_match.group(1)
            break

    return (
        number,
        title,
        actor,
        cover_url,
        studio,
        release,
        year,
        tag,
        outline,
        video_url,
        video_type,
    )


def get_real_url(html, number_list):
    """
    从搜索结果页面中获取最匹配的详情页URL
    :param html: HTML解析后的元素树
    :param number_list: 要匹配的番号列表
    :return: 匹配结果状态、匹配的番号、标题和URL
    """
    item_list = html.xpath('//div[contains(@class, "imgcover")]')

    for item in item_list:
        detail_url = item.xpath(".//a/@href")
        if not detail_url:
            continue

        detail_url = detail_url[0]
        title = item.xpath("../h3/text()")
        if not title:
            continue

        title = title[0].strip()

        # 比较标题与番号是否匹配
        for n in number_list:
            temp_n = re.sub(r"[\W_]", "", n).upper()
            temp_title = re.sub(r"[\W_]", "", title).upper()
            if temp_n in temp_title:
                return True, n, title, detail_url

    return False, "", "", ""


def search(keyword, page=1):
    """
    搜索功能实现
    :param keyword: 搜索关键词
    :param page: 页码
    :return: 搜索结果列表
    """
    av911_url = "https://av911.tv"
    search_url = f"{av911_url}/serach?fulltext={keyword}&page={page-1}"
    result, response = curl_html(search_url)

    if not result:
        return []

    html = etree.fromstring(response, etree.HTMLParser())
    results = []

    item_list = html.xpath('//div[contains(@class, "imgcover")]')

    for item in item_list:
        result = {}

        link = item.xpath(".//a/@href")
        if link:
            result["url"] = av911_url + link[0]

        title = item.xpath("../h3/text()")
        if title:
            result["title"] = title[0].strip()

        cover = item.xpath(".//img/@src")
        if cover:
            result["cover"] = av911_url + cover[0]

        if result:
            results.append(result)

    return results


def download_image(url, save_path):
    """
    下载图片
    :param url: 图片URL
    :param save_path: 保存路径
    :return: 是否下载成功
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }
        response = requests.get(url, headers=headers, timeout=10, stream=True)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            return True
        return False
    except Exception as e:
        print(f"下载图片失败: {e}")
        return False


def main(
    number,
    appoint_url="",
    log_info="",
    req_web="",
    language="zh_cn",
    file_path="",
    appoint_number="",
):
    """
    主函数，获取影片信息
    :param number: 番号
    :param appoint_url: 指定的URL
    :param log_info: 日志信息
    :param req_web: 请求网站信息
    :param language: 语言
    :param file_path: 文件路径
    :param appoint_number: 指定的番号
    :return: JSON格式的影片信息
    """
    start_time = time.time()
    website_name = "av911"
    req_web += "-> %s" % website_name
    title = ""
    cover_url = ""
    web_info = "\n       "
    log_info += " \n    🌐 av911"
    debug_info = ""
    real_url = appoint_url
    av911_url = "https://av911.tv"

    try:
        if not real_url:
            # 处理番号
            number_list = [number]
            if appoint_number:
                number_list.append(appoint_number)

            # 尝试搜索番号
            for each in number_list:
                real_url = f"{av911_url}/serach?fulltext={each}"
                debug_info = f"请求地址: {real_url} "
                log_info += web_info + debug_info
                result, response = curl_html(real_url)

                if not result:
                    debug_info = "网络请求错误: %s" % response
                    log_info += web_info + debug_info
                    raise Exception(debug_info)

                search_page = etree.fromstring(response, etree.HTMLParser())
                result, number, title, real_url = get_real_url(search_page, number_list)
                if result:
                    real_url = (
                        av911_url + real_url
                        if not real_url.startswith("http")
                        else real_url
                    )
                    break
            else:
                debug_info = "没有匹配的搜索结果"
                log_info += web_info + debug_info
                raise Exception(debug_info)

        debug_info = f"番号地址: {real_url} "
        log_info += web_info + debug_info
        result, response = curl_html(real_url)

        if not result:
            debug_info = "没有找到数据 %s " % response
            log_info += web_info + debug_info
            raise Exception(debug_info)

        detail_page = etree.fromstring(response, etree.HTMLParser())
        (
            number,
            title,
            actor,
            cover_url,
            studio,
            release,
            year,
            tag,
            outline,
            video_url,
            video_type,
        ) = get_detail_info(detail_page, number, file_path)
        actor_photo = get_actor_photo(actor)

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
                "runtime": "",
                "score": "",
                "series": "",
                "country": (
                    "CN" if video_type == "無碼" or video_type == "无码" else "JP"
                ),
                "director": "",
                "studio": studio,
                "publisher": studio,
                "source": "av911",
                "website": real_url,
                "actor_photo": actor_photo,
                "cover": cover_url,
                "poster": cover_url,
                "extrafanart": "",
                "trailer": video_url,
                "image_download": False,
                "image_cut": "no",
                "log_info": log_info,
                "error_info": "",
                "req_web": req_web
                + "(%ss) "
                % (
                    round(
                        (time.time() - start_time),
                    )
                ),
                "mosaic": (
                    "无码" if video_type == "無碼" or video_type == "无码" else "有码"
                ),
                "wanted": "",
            }
            debug_info = "数据获取成功！"
            log_info += web_info + debug_info
            dic["log_info"] = log_info
        except Exception as e:
            debug_info = "数据生成出错: %s" % str(e)
            log_info += web_info + debug_info
            raise Exception(debug_info)

    except Exception as e:
        # print(traceback.format_exc())
        debug_info = str(e)
        dic = {
            "title": "",
            "cover": "",
            "website": "",
            "log_info": log_info,
            "error_info": debug_info,
            "req_web": req_web
            + "(%ss) "
            % (
                round(
                    (time.time() - start_time),
                )
            ),
        }
    dic = {website_name: {"zh_cn": dic, "zh_tw": dic, "jp": dic}}
    js = json.dumps(
        dic,
        ensure_ascii=False,
        sort_keys=False,
        indent=4,
        separators=(",", ": "),
    )
    return js


if __name__ == "__main__":
    # 测试代码
    print(main("巨乳", file_path=""))
    # 测试搜索功能
    # results = search("巨乳", 1)
    # print(f"搜索结果数量: {len(results)}")
    # if results:
    #     print(f"第一个结果: {results[0]}")
