#!/usr/bin/env python3
import json
import re
import time

import urllib3
from lxml import etree

from models.base.web import curl_html
from models.config.config import config
from models.crawlers.guochan import get_extra_info, get_number_list

urllib3.disable_warnings()  # yapf: disable


# import traceback


def get_actor_photo(actor):
    actor = actor.split(",")
    data = {}
    for i in actor:
        actor_photo = {i: ""}
        data.update(actor_photo)
    return data


def get_detail_info(html, real_url, number, file_path):
    href = re.split(r"[/.]", real_url)[-2]
    title_h1 = html.xpath(
        '//h3[@class="title" and not(contains(normalize-space(.), "目录")) and not(contains(normalize-space(.), "为你推荐"))]/text()'
    )
    title = title_h1[0].replace(number + " ", "").strip() if title_h1 else number
    actor = get_extra_info(title, file_path, info_type="actor")
    tag = get_extra_info(title, file_path, info_type="tag")
    cover_url = html.xpath(f'//a[@data-original and contains(@href,"{href}")]/@data-original')
    cover_url = cover_url[0] if cover_url else ""

    return number, title, actor, cover_url, tag


def get_real_url(html, number_list, hscangku_url):
    item_list = html.xpath('//a[@class="stui-vodlist__thumb lazyload"]')
    for each in item_list:
        # href="/vodplay/41998-1-1.html"
        detail_url = hscangku_url + each.get("href")
        title = each.xpath("@title")[0]
        if title and detail_url:
            for n in number_list:
                temp_n = re.sub(r"[\W_]", "", n).upper()
                temp_title = re.sub(r"[\W_]", "", title).upper()
                if temp_n in temp_title:
                    return True, n, title, detail_url
    return False, "", "", ""


def get_redirected_url(url):
    result, response = curl_html(url)
    if not result:
        return None

    if redirected_url := re.search(r'"(https?://.*?)"', response).group(1):
        http = urllib3.PoolManager()
        response = http.request("GET", f"{redirected_url}{url}&p=", redirect=False)
        final_url = response.get_redirect_location()
        return final_url if final_url else None
    else:
        return None


def main(number, appoint_url="", log_info="", req_web="", language="zh_cn", file_path="", appoint_number=""):
    start_time = time.time()
    website_name = "hscangku"
    req_web += "-> %s" % website_name
    title = ""
    cover_url = ""
    web_info = "\n       "
    log_info += " \n    🌐 hscangku"
    debug_info = ""
    real_url = appoint_url
    hscangku_url = getattr(config, "hscangku_website", "http://hsck.net")

    try:
        if not real_url:
            # 处理番号
            number_list, filename_list = get_number_list(number, appoint_number, file_path)
            n_list = number_list[:1] + filename_list
            # 处理重定向
            hscangku_url = get_redirected_url(hscangku_url)
            if not hscangku_url:
                debug_info = "没有正确的 hscangku_url，无法刮削"
                log_info += web_info + debug_info
                raise Exception(debug_info)
            for each in n_list:
                real_url = f"{hscangku_url}/vodsearch/-------------.html?wd={each}&submit="
                # real_url = 'http://hsck860.cc/vodsearch/-------------.html?wd=%E6%9F%9A%E5%AD%90%E7%8C%AB&submit='
                debug_info = f"请求地址: {real_url} "
                log_info += web_info + debug_info
                result, response = curl_html(real_url)

                if not result:
                    debug_info = "网络请求错误: %s" % response
                    log_info += web_info + debug_info
                    raise Exception(debug_info)
                search_page = etree.fromstring(response, etree.HTMLParser())
                result, number, title, real_url = get_real_url(search_page, n_list, hscangku_url)
                # real_url = 'http://hsck860.cc/vodsearch/-------------.html?wd=%E6%9F%9A%E5%AD%90%E7%8C%AB&submit='
                if result:
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
        number, title, actor, cover_url, tag = get_detail_info(detail_page, real_url, number, file_path)
        actor_photo = get_actor_photo(actor)

        try:
            dic = {
                "number": number,
                "title": title,
                "originaltitle": title,
                "actor": actor,
                "outline": "",
                "originalplot": "",
                "tag": tag,
                "release": "",
                "year": "",
                "runtime": "",
                "score": "",
                "series": "",
                "country": "CN",
                "director": "",
                "studio": "",
                "publisher": "",
                "source": "hscangku",
                "website": real_url,
                "actor_photo": actor_photo,
                "cover": cover_url,
                "poster": "",
                "extrafanart": "",
                "trailer": "",
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
                "mosaic": "国产",
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
    # yapf: disable
    # print(main('大像传媒之淫蕩刺青女學徒', file_path='大像传媒之淫蕩刺青女學徒'))
    # print(main('冠希传媒GX-017强上弟弟的巨乳姐姐', file_path='冠希传媒GX-017强上弟弟的巨乳姐姐'))
    # print(main('[SWAG]XHX-0014宅男的公仔幻化成人', file_path='[SWAG]XHX-0014宅男的公仔幻化成人'))
    # print(main('IDG5401'))
    print(main('大像传媒之長腿癡女代表情慾作-米歐', file_path='大像传媒之長腿癡女代表情慾作-米歐'))
