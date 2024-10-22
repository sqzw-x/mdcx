#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import time  # yapf: disable # NOQA: E402

import urllib3
from lxml import etree

from models.base.web import get_html
from models.config.config import config

urllib3.disable_warnings()  # yapf: disable


def getTitle(html):  # 获取标题
    result = html.xpath('//div[@data-section="userInfo"]//h3/span/../text()')
    if result:
        result = ' '.join(result)
    else:
        result = ''
    return result


def getCover(html):  # 获取封面
    extrafanart = html.xpath('//ul[@class="items_article_SampleImagesArea"]/li/a/@href')
    if extrafanart:
        result = extrafanart[0]
    else:
        result = ''
    return result, extrafanart


def getCoverSmall(html):  # 获取小图
    result = html.xpath('//div[@class="items_article_MainitemThumb"]/span/img/@src')
    if result:
        result = 'https:' + result[0]
    else:
        result = ''
    return result


def getRelease(html):
    result = html.xpath('//div[@class="items_article_Releasedate"]/p/text()')
    result = re.findall(r'\d+/\d+/\d+', str(result))
    if result:
        result = result[0].replace('/', '-')
    else:
        result = ''
    return result


def getStudio(html):  # 使用卖家作为厂家
    result = html.xpath('//div[@class="items_article_headerInfo"]/ul/li[last()]/a/text()')
    if result:
        result = result[0].strip()
    else:
        result = ''
    return result


def getTag(html):  # 获取标签
    result = html.xpath('//a[@class="tag tagTag"]/text()')
    result = str(result).strip(" ['']").replace("', '", ",")
    return result


def getOutline(html):  # 获取简介
    result = html.xpath('//meta[@name="description"]/@content')
    if result:
        result = result[0]
    else:
        result = ''
    return result


def getMosaic(tag, title):  # 获取马赛克
    if '無修正' in tag or '無修正' in title:
        result = '无码'
    else:
        result = '有码'
    return result


def main(number, appoint_url='', log_info='', req_web='', language='jp'):
    start_time = time.time()
    website_name = 'fc2'
    req_web += '-> %s' % website_name
    real_url = appoint_url
    title = ''
    cover_url = ''
    poster_url = ''
    image_download = False
    image_cut = 'center'
    number = number.upper().replace('FC2PPV', '').replace('FC2-PPV-', '').replace('FC2-', '').replace('-', '').strip()
    dic = {}
    web_info = '\n       '
    log_info += ' \n    🌐 fc2'
    debug_info = ''

    try:  # 捕获主动抛出的异常
        if not real_url:
            real_url = 'https://adult.contents.fc2.com/article/%s/' % number

        debug_info = '番号地址: %s' % real_url
        log_info += web_info + debug_info

        # ========================================================================番号详情页
        result, html_content = get_html(real_url)
        if not result:
            debug_info = '网络请求错误: %s' % html_content
            log_info += web_info + debug_info
            raise Exception(debug_info)
        html_info = etree.fromstring(html_content, etree.HTMLParser())

        title = getTitle(html_info)  # 获取标题
        if 'お探しの商品が見つかりません' in title:
            debug_info = '搜索结果: 未匹配到番号！'
            log_info += web_info + debug_info
            raise Exception(debug_info)

        cover_url, extrafanart = getCover(html_info)  # 获取cover,extrafanart
        if 'http' not in cover_url:
            debug_info = '数据获取失败: 未获取到cover！'
            log_info += web_info + debug_info
            raise Exception(debug_info)

        poster_url = getCoverSmall(html_info)
        outline = getOutline(html_info)
        tag = getTag(html_info)
        release = getRelease(html_info)
        studio = getStudio(html_info)  # 使用卖家作为厂商
        mosaic = getMosaic(tag, title)
        tag = tag.replace('無修正,', '').replace('無修正', '').strip(',')
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
                'release': release,
                'year': release[:4],
                'runtime': '',
                'score': '',
                'series': 'FC2系列',
                'director': '',
                'studio': studio,
                'publisher': studio,
                'source': 'fc2',
                'website': real_url,
                'actor_photo': {actor: ''},
                'cover': cover_url,
                'poster': poster_url,
                'extrafanart': extrafanart,
                'trailer': '',
                'image_download': image_download,
                'image_cut': image_cut,
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
    print(main('1723984',
               ''))  # 有码  # print(main('1924776', ''))  # print(main('1860858', ''))  # print(main('1599412', ''))    # fc2hub有，fc2/fc2club没有  # print(main('1131214', ''))    # fc2club有，fc2/fc2hub没有  # print(main('1837553', ''))  # 无码  # print(main('1613618', ''))  # print(main('1837553', ''))  # print(main('1837589', ""))  # print(main('1760182', ''))  # print(main('1251689', ''))  # print(main('674239', ""))  # print(main('674239', "))
