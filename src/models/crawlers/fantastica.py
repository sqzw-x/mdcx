#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import time

import urllib3
from lxml import etree

from models.base.web import get_html, get_imgsize

urllib3.disable_warnings()  # yapf: disable


# import traceback


def get_web_number(html, number):
    result = html.xpath("//dt[contains(text(),'作品番号')]/following-sibling::dd/text()")
    return result[0].strip() if result else number


def get_title(html):
    result = html.xpath('//div[@class="title-area"]/h2/text()')
    return result[0] if result else ''


def get_actor(html):
    result = html.xpath("//th[contains(text(),'出演者')]/following-sibling::td//text()")
    actor_new_list = []
    for a in result:
        if a.strip():
            actor_new_list.append(a.strip())
    return ','.join(actor_new_list) if actor_new_list else ''


def get_actor_photo(actor):
    actor = actor.split(',')
    data = {}
    for i in actor:
        actor_photo = {i: ''}
        data.update(actor_photo)
    return data


def get_extrafanart(html):
    return html.xpath('//div[@class="vr_images clearfix"]/div[@class="vr_image"]/a/@href')


def get_release(html):
    result = html.xpath("//th[contains(text(),'発売日')]/following-sibling::td//text()")
    return result[0].replace('年', '-').replace('月', '-').replace('日', '').strip() if result else ''


def get_year(release):
    try:
        result = str(re.search(r'\d{4}', release).group())
        return result
    except:
        return release


def get_runtime(html):
    result = html.xpath("//th[contains(text(),'収録時間')]/following-sibling::td//text()")
    return result[0].replace('分', '').strip() if result else ''


def get_tag(html):
    result = html.xpath("//th[contains(text(),'ジャンル')]/following-sibling::td/a/text()")
    new_list = []
    for a in result:
        new_list.append(a.strip())
    return ','.join(new_list)


def get_series(html):
    result = html.xpath("//th[contains(text(),'シリーズ')]/following-sibling::td//text()")
    return result[0].strip() if result else ''


def get_cover(html):
    result = html.xpath('//div[@class="vr_wrapper clearfix"]/div[@class="img"]/img/@src')
    cover = result[0] if result else ''
    if cover == 'https://assets.fantastica-vr.com/assets/common/img/dummy_large_white.jpg':
        cover = ''
    return cover


def get_outline(html):
    return html.xpath('string(//p[@class="explain"])')


def get_real_url(html, number):
    result = html.xpath('//section[@class="item_search item_list clearfix"]/div/ul/li/a')
    for each in result:
        href = each.get('href')
        poster = each.xpath('img/@src')
        if number.lower().replace('-', '') in href.lower().replace('-', ''):
            poster = poster[0] if poster else ''
            if poster == 'https://assets.fantastica-vr.com/assets/common/img/dummy_white.jpg':
                poster = ''
            real_url = 'http://fantastica-vr.com' + href if 'http' not in href else href
            return real_url, poster
    return '', ''


def main(number, appoint_url='', log_info='', req_web='', language='jp'):
    start_time = time.time()
    website_name = 'fantastica'
    req_web += '-> %s' % website_name
    real_url = appoint_url
    image_cut = 'right'
    image_download = False
    search_url = ''
    mosaic = ''
    web_info = '\n       '
    log_info += ' \n    🌐 fantastica'
    debug_info = ''
    poster = ''

    # search_url = 'http://fantastica-vr.com/items/search?q=FAKWM001'
    # real_url = 'http://fantastica-vr.com/items/detail/FAKWM-001'

    try:  # 捕获主动抛出的异常
        if not real_url:

            # 通过搜索获取real_url
            search_url = f'http://fantastica-vr.com/items/search?q={number}'
            debug_info = '搜索地址: %s ' % search_url
            log_info += web_info + debug_info

            # ========================================================================搜索番号
            result, html_search = get_html(search_url)
            if not result:
                debug_info = '网络请求错误: %s ' % html_search
                log_info += web_info + debug_info
                raise Exception(debug_info)

            html = etree.fromstring(html_search, etree.HTMLParser())
            real_url, poster = get_real_url(html, number)
            image_download = True
            if not real_url:
                debug_info = '搜索结果: 未匹配到番号！'
                log_info += web_info + debug_info
                raise Exception(debug_info)

        if real_url:
            debug_info = '番号地址: %s ' % real_url
            log_info += web_info + debug_info
            result, html_content = get_html(real_url)
            if not result:
                debug_info = '网络请求错误: %s ' % html_content
                log_info += web_info + debug_info
                raise Exception(debug_info)

            html_info = etree.fromstring(html_content, etree.HTMLParser())
            title = get_title(html_info)
            if not title:
                debug_info = '数据获取失败: 未获取到 title！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            outline = get_outline(html_info)
            actor = get_actor(html_info)
            actor_photo = get_actor_photo(actor)
            cover_url = get_cover(html_info)
            release = get_release(html_info)
            year = get_year(release)
            runtime = get_runtime(html_info)
            score = ''
            series = get_series(html_info)
            tag = get_tag(html_info)
            director = ''
            studio = 'ファンタスティカ'
            publisher = 'ファンタスティカ'
            extrafanart = get_extrafanart(html_info)
            trailer = ''
            mosaic = '有码'
            if not poster and extrafanart:
                w, h = get_imgsize(extrafanart[0])
                if w > h:
                    poster = extrafanart[0]
                    image_download = True
            try:
                dic = {
                    'number': number,
                    'title': title,
                    'originaltitle': title,
                    'actor': actor,
                    'outline': outline,
                    'originalplot': outline,
                    'tag': tag,
                    'release': release,
                    'year': year,
                    'runtime': runtime,
                    'score': score,
                    'series': series,
                    'director': director,
                    'studio': studio,
                    'publisher': publisher,
                    'source': 'fantastica',
                    'actor_photo': actor_photo,
                    'cover': cover_url,
                    'poster': poster,
                    'extrafanart': extrafanart,
                    'trailer': trailer,
                    'image_download': image_download,
                    'image_cut': image_cut,
                    'log_info': log_info,
                    'error_info': '',
                    'req_web': req_web + '(%ss) ' % (round((time.time() - start_time), )),
                    'mosaic': mosaic,
                    'website': real_url,
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
    js = json.dumps(dic, ensure_ascii=False, sort_keys=False, indent=4, separators=(',', ': '), )  # .encode('UTF-8')
    return js


if __name__ == '__main__':
    # yapf: disable
    print(main('FAAP525'))  # 无图  # print(main('fakwm-001'))  # print(main('fakwm-064'))  # print(main('fapro-123'))
