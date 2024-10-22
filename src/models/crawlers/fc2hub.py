#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time  # yapf: disable # NOQA: E402

import urllib3
from lxml import etree

from models.base.web import get_html
from models.config.config import config

urllib3.disable_warnings()  # yapf: disable


# import traceback


def getTitle(html):  # 获取标题
    result = html.xpath('//h1/text()')
    if result:
        result = result[1]
    else:
        result = ''
    return result


def getNum(html):  # 获取番号
    result = html.xpath('//h1/text()')
    if result:
        result = result[0]
    else:
        result = ''
    return result


def getCover(html):  # 获取封面
    result = html.xpath('//a[@data-fancybox="gallery"]/@href')
    if result:
        result = result[0]
    else:
        result = ''
    return result


def getExtraFanart(html):  # 获取剧照
    result = html.xpath('//div[@style="padding: 0"]/a/@href')
    return result


def getStudio(html):  # 使用卖家作为厂家
    result = html.xpath('//div[@class="col-8"]/text()')
    if result:
        result = result[0].strip()
    return result


def getTag(html):  # 获取标签
    result = html.xpath('//p[@class="card-text"]/a[contains(@href, "/tag/")]/text()')
    if result:
        result = str(result).strip(' [' ']').replace(", ", ',').replace("'", '').strip()
    else:
        result = ''
    return result


def getOutline(html):  # 获取简介
    result = (''.join(html.xpath('//div[@class="col des"]//text()')).strip('[' ']').replace("',", '').replace('\\n', '').replace("'", '').replace('・', '').strip())
    return result


def getMosaic(tag, title):  # 获取马赛克
    if '無修正' in tag or '無修正' in title:
        result = '无码'
    else:
        result = '有码'
    return result


def main(number, appoint_url='', log_info='', req_web='', language='jp'):
    start_time = time.time()
    website_name = 'fc2hub'
    req_web += '-> %s' % website_name
    real_url = appoint_url
    root_url = getattr(config, 'fc2hub_website', 'https://javten.com')

    number = number.upper().replace('FC2PPV', '').replace('FC2-PPV-', '').replace('FC2-', '').replace('-', '').strip()
    dic = {}
    web_info = '\n       '
    log_info += ' \n    🌐 fc2hub'

    try:  # 捕获主动抛出的异常
        if not real_url:

            # 通过搜索获取real_url
            url_search = root_url + '/search?kw=' + number
            debug_info = '搜索地址: %s ' % url_search
            log_info += web_info + debug_info

            # ========================================================================搜索番号
            result, html_search = get_html(url_search)
            if not result:
                debug_info = '网络请求错误: %s' % html_search
                log_info += web_info + debug_info
                raise Exception(debug_info)
            html = etree.fromstring(html_search, etree.HTMLParser())
            real_urls = html.xpath("//link[contains(@href, $number)]/@href", number='id' + number)

            if not real_urls:
                debug_info = '搜索结果: 未匹配到番号！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            else:
                language_not_jp = ['/tw/', '/ko/', '/en/']
                for url in real_urls:
                    if all(la not in url for la in language_not_jp):
                        real_url = url
                        break

        if real_url:
            debug_info = '番号地址: %s ' % real_url
            log_info += web_info + debug_info
            result, html_content = get_html(real_url)
            if not result:
                debug_info = '网络请求错误: %s' % html_content
                log_info += web_info + debug_info
                raise Exception(debug_info)
            html_info = etree.fromstring(html_content, etree.HTMLParser())

            title = getTitle(html_info)  # 获取标题
            if not title:
                debug_info = '数据获取失败: 未获取到title！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            cover_url = getCover(html_info)  # 获取cover
            outline = getOutline(html_info)
            tag = getTag(html_info)
            studio = getStudio(html_info)  # 获取厂商
            extrafanart = getExtraFanart(html_info)
            mosaic = getMosaic(tag, title)
            if 'fc2_seller' in config.fields_rule:
                actor = studio
            else:
                actor = ''

            try:
                dic = {
                    'number': 'FC2-' + str(number),
                    'title': title,
                    'originaltitle': title,
                    'actor': actor,
                    'outline': outline,
                    'originalplot': outline,
                    'tag': tag,
                    'release': '',
                    'year': '',
                    'runtime': '',
                    'score': '',
                    'series': 'FC2系列',
                    'director': '',
                    'studio': studio,
                    'publisher': studio,
                    'source': 'fc2hub.main',
                    'website': str(real_url).strip('[]'),
                    'actor_photo': {actor: ''},
                    'cover': str(cover_url),
                    'poster': '',
                    'extrafanart': extrafanart,
                    'trailer': '',
                    'image_download': False,
                    'image_cut': 'center',
                    'log_info': log_info,
                    'error_info': '',
                    'req_web': req_web + '(%ss) ' % (round((time.time() - start_time), )),
                    'mosaic': mosaic,
                    'wanted': '',
                }
                debug_info = '数据获取成功！'
                log_info += web_info + debug_info
                dic['log_info'] = log_info
            except Exception as e:
                debug_info = '数据生成出错: %s' % str(e)
                log_info += web_info + debug_info
                raise Exception(debug_info)

    except Exception as e:
        # print(traceback.format_exc())
        debug_info = str(e)
        dic = {
            'title': '',
            'cover': '',
            'website': '',
            'log_info': log_info,
            'error_info': debug_info,
            'req_web': req_web + '(%ss) ' % (round((time.time() - start_time), )),
        }
    dic = {website_name: {'zh_cn': dic, 'zh_tw': dic, 'jp': dic}}
    js = json.dumps(dic, ensure_ascii=False, sort_keys=False, indent=4, separators=(',', ': '), )
    return js


if __name__ == '__main__':
    # yapf: disable
    # print(main('FC2-424646'))
    print(main('1940476'))  # 无码  # print(main('1860858', ''))  #有码  # print(main('1599412', ''))  # print(main('1131214', ''))  # 未找到  # print(main('1837553', ''))  # print(main('1613618', ''))  # print(main('1837553', ''))  # print(main('1837589', ""))  # print(main('1760182', ''))  # print(main('1251689', ''))  # print(main('674239', ""))  # print(main('674239', "))  # print(main('1924003', ''))   # 无图
