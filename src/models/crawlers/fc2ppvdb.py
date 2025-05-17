#!/usr/bin/env python3
import json
import time
import requests
import urllib3
from lxml import etree
from src.models.base.web import get_html
from src.models.config.config import config

# 禁用SSL警告
urllib3.disable_warnings()


def get_title(html):  # 获取标题
    title_nodes = html.xpath("//h2/a/text()")
    return title_nodes[0] if title_nodes else ""


def get_cover(html,number):  # 获取封面
    cover_url_nodes = html.xpath(f"//img[contains(@alt, '{number.replace('FC2-', '')}')]/@src")
    return cover_url_nodes[0] if cover_url_nodes else ""


def get_release_date(html):  #获取发行日期
    release_date_nodes = html.xpath("//div[starts-with(text(),'販売日：')]/span/text()")
    return release_date_nodes[0] if release_date_nodes else ""


def get_actors(html):  #获取演员
    actors_nodes = html.xpath("//div[starts-with(text(),'女優：')]/span/a/text()")
    return ",".join([a.strip() for a in actors_nodes]) if actors_nodes else ""


def get_tags(html):  #获取标签
    tags_nodes = html.xpath("//div[starts-with(text(),'タグ：')]/span/a/text()")
    return ",".join([t.strip() for t in tags_nodes]) if tags_nodes else ""


def get_studio(html):  #获取厂家
    studio_nodes = html.xpath("//div[starts-with(text(),'販売者：')]/span/a/text()")
    return studio_nodes[0].strip() if studio_nodes else ""


def get_video_type(html):  #获取视频类型
    uncensored_str_nodes = html.xpath("//div[starts-with(text(),'モザイク：')]/span/text()")
    uncensored_str = uncensored_str_nodes[0] if uncensored_str_nodes else ""
    return "無碼" if uncensored_str == "無" else "有碼" if uncensored_str == "有" else ""


def get_video_url(html):  #获取视频URL
    video_url_nodes = html.xpath("//a[starts-with(text(),'サンプル動画')]/@href")
    return video_url_nodes[0] if video_url_nodes else ""


def get_video_time(html):  #获取视频时长
    video_size_nodes = html.xpath("//div[starts-with(text(),'収録時間：')]/span/text()")
    return video_size_nodes[0] if video_size_nodes else ""


def main(number, appoint_url="", log_info="", req_web="", language="zh_cn", file_path="", appoint_number=""):
    """
    主函数，获取FC2视频信息
    :param number: 番号
    :param appoint_url: 指定的URL
    :param log_info: 日志信息
    :param req_web: 请求网站信息
    :param language: 语言
    :param file_path: 文件路径
    :param appoint_number: 指定番号
    :return: JSON格式的影片信息
    """
    start_time = time.time()
    website_name = "fc2ppvdb"
    req_web += "-> %s" % website_name
    real_url = appoint_url
    number = number.upper().replace("FC2PPV", "").replace("FC2-PPV-", "").replace("FC2-", "").replace("-", "").strip()
    dic = {}
    web_info = "\n       "
    log_info += " \n     🌐fc2ppvdb"
    debug_info = ""

    try:
        if not real_url:
            real_url = f"https://fc2ppvdb.com/articles/{number}"

        debug_info = "番号地址: %s" % real_url
        log_info += web_info + debug_info
        # ========================================================================番号详情页
        result, html_content = get_html(real_url)
        if not result:
            debug_info = "网络请求错误: %s" % html_content
            log_info += web_info + debug_info
            raise Exception(debug_info)
        html_info = etree.fromstring(html_content, etree.HTMLParser())

        title = get_title(html_info)
        cover_url = get_cover(html_info,number)
        if "http" not in cover_url:
            debug_info = "数据获取失败: 未获取到cover！"
            log_info += web_info + debug_info
            raise Exception(debug_info)
        release_date = get_release_date(html_info)
        year = release_date[:4] if release_date else ""
        actor = get_actors(html_info)
        tag = get_tags(html_info)
        studio = get_studio(html_info) # 使用卖家作为厂商
        video_type = get_video_type(html_info)
        video_url = get_video_url(html_info)
        video_time = get_video_time(html_info)
        tag = tag.replace("無修正,", "").replace("無修正", "").strip(",")
        if "fc2_seller" in config.fields_rule:
            actor = studio
        else:
            actor = ""

        try:
            dic = {
                "number": "FC2-" + str(number),
                "title": title,
                "originaltitle": title,
                "outline": "",
                "actor": actor,
                "originalplot": "",
                "tag": tag,
                "release": release_date,
                "year": year,
                "runtime": "",
                "score": "",
                "series": "FC2系列",
                "director": "",
                "studio": studio,
                "publisher": studio,
                "source": "fc2",
                "website": real_url,
                "actor_photo": {actor: ""},
                "cover": cover_url,
                "poster": cover_url,
                "extrafanart": "",
                "trailer": video_url,
                "log_info": log_info,
                "error_info": "",
                "req_web": req_web
                           + "(%ss) "
                           % (
                               round(
                                   (time.time() - start_time),
                               )
                           ),
                "mosaic": "无码" if video_type == "無碼" else "有码",
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
    print(main("FC2-3259498", file_path=""))
