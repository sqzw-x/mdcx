#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import time  # yapf: disable # NOQA: E402

import urllib3
from lxml import etree

from models.base.web import get_html

urllib3.disable_warnings()  # yapf: disable


# import traceback
# import Function.config as cf


def get_title(html):
    result = html.xpath('//h1/text()')
    return result[0] if result else ''


def get_actor(html):
    actor_result = html.xpath('//div[@class="box_works01_list clearfix"]//span[text()="出演女優"]/following-sibling::p[1]/text()')
    return ','.join(actor_result)


def get_actor_photo(actor):
    actor = actor.split(',')
    data = {}
    for i in actor:
        actor_photo = {i: ''}
        data.update(actor_photo)
    return data


def get_outline(html):
    return html.xpath("string(//div[@class='box_works01_text']/p)")


def get_runtime(html):
    result = html.xpath('//span[contains(text(), "収録時間")]/following-sibling::*//text()')
    if result:
        result = re.findall(r'\d+', result[0])
    return result[0] if result else ''


def get_series(html):
    result = html.xpath('//span[contains(text(), "系列")]/following-sibling::*//text()')
    return ''.join(result).strip() if result else ''


def get_director(html):
    result = html.xpath('//span[contains(text(), "导演") or contains(text(), "導演") or contains(text(), "監督")]/following-sibling::*//text()')
    return result[0] if result else ''


def get_publisher(html):
    result = html.xpath('//span[contains(text(), "メーカー")]/following-sibling::*//text()')
    return result[0] if result else 'FALENO'


def get_release(html):
    result = html.xpath('//div[@class="view_timer"]//span[text()="配信開始日"]/following-sibling::p[1]/text()')
    return result[0].replace('/', '-') if result else ''


def get_year(release):
    result = re.findall(r'\d{4}', release)
    return result[0] if result else ''


def get_tag(html):
    result = html.xpath('//a[@class="genre"]//text()')
    tag = ''
    for each in result:
        tag += each.strip().replace('，', '') + ','
    return tag.strip(',')


def get_cover(html):
    result = html.xpath("//a[@class='pop_sample']/img/@src")
    return result[0].replace('?output-quality=60', '') if result else ''


def get_extrafanart(html):  # 获取封面链接
    extrafanart_list = html.xpath("//a[@class='pop_img']/@href")
    return extrafanart_list


def get_trailer(html):  # 获取预览片
    result = html.xpath("//a[@class='pop_sample']/@href")
    return result[0] if result else ''


def get_real_url(html):
    href_result = html.xpath('//div[@class="text_name"]/a/@href')
    poster_result = html.xpath('//div[@class="text_name"]/../a/img/@src')
    if href_result and poster_result:
        return href_result[0], poster_result[0]
    return '', ''


def main(number, appoint_url='', log_info='', req_web='', language='jp'):
    # https://faleno.jp/top/works/fsdss564/
    # https://falenogroup.com/works/votan-034/
    start_time = time.time()
    website_name = 'faleno'
    req_web += '-> %s' % website_name
    real_url = appoint_url
    title = ''
    cover_url = ''
    poster_url = ''
    image_download = True
    image_cut = 'right'
    web_info = '\n       '
    debug_info = ''
    number_lo = number.lower()
    number_lo_noline = number_lo.replace('-', '')
    number_lo_space = number_lo.replace('-', ' ')
    search_url_list = [f'https://faleno.jp/top/?s={number_lo_space}', f'https://falenogroup.com/top/?s={number_lo_space}']
    real_url_list = []
    if real_url:
        real_url_list = [real_url]
    elif number.upper().startswith('FLN'):
        real_url_list = [f"https://faleno.jp/top/works/{number_lo_noline}/", f"https://faleno.jp/top/works/{number_lo}/", f"https://falenogroup.com/works/{number_lo}/",
                         f"https://falenogroup.com/works/{number_lo_noline}/"]
    log_info += '\n    🌐 faleno'
    mosaic = '有码'
    try:  # 捕获主动抛出的异常
        if not real_url_list:
            for search_url in search_url_list:
                debug_info = '请求地址: %s ' % search_url
                log_info += web_info + debug_info

                result, html_info = get_html(search_url)
                if not result:
                    debug_info = '请求错误: %s ' % html_info
                    log_info += web_info + debug_info
                    continue

                html_detail = etree.fromstring(html_info, etree.HTMLParser())
                real_url, poster_url = get_real_url(html_detail)
                if real_url:
                    real_url_list = [real_url]
                    break
                else:
                    debug_info = '未找到搜索结果'
                    log_info += web_info + debug_info
            else:
                raise Exception(debug_info)

        for real_url in real_url_list:
            debug_info = '番号地址: %s ' % real_url
            log_info += web_info + debug_info

            result, html_info = get_html(real_url)
            if not result:
                debug_info = '请求错误: %s ' % html_info
                log_info += web_info + debug_info
                continue

            html_detail = etree.fromstring(html_info, etree.HTMLParser())
            title = get_title(html_detail)
            if not title:
                debug_info = '数据获取失败: 番号标题不存在！'
                log_info += web_info + debug_info
                raise Exception(debug_info)

            actor = get_actor(html_detail)  # 获取actor
            actor_photo = get_actor_photo(actor)
            for each in actor_photo.keys():
                title = title.replace(' ' + each, '')
            cover_url = get_cover(html_detail)  # 获取cover
            if not poster_url:
                poster_url = cover_url.replace('_1200.jpg', '_2125.jpg').replace('_tsp.jpg', '_actor.jpg').replace('1200_re', '2125').replace('_1200-1', '_2125-1')
            outline = get_outline(html_detail)
            tag = ''
            release = get_release(html_detail)
            year = get_year(release)
            runtime = get_runtime(html_detail)
            score = ''
            series = get_series(html_detail)
            director = get_director(html_detail)
            studio = get_publisher(html_detail)
            publisher = studio
            extrafanart = get_extrafanart(html_detail)
            trailer = get_trailer(html_detail)
            website = real_url
            break
        else:
            raise Exception(debug_info)
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
                'source': 'faleno',
                'actor_photo': actor_photo,
                'cover': cover_url,
                'poster': poster_url,
                'extrafanart': extrafanart,
                'trailer': trailer,
                'image_download': image_download,
                'image_cut': image_cut,
                'log_info': log_info,
                'error_info': '',
                'req_web': req_web + '(%ss) ' % (round((time.time() - start_time), )),
                'mosaic': mosaic,
                'website': website,
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
            'req_web': req_web + '(%ss) ' % (round((time.time() - start_time), ))
        }
    dic = {website_name: {'zh_cn': dic, 'zh_tw': dic, 'jp': dic}}
    js = json.dumps(dic, ensure_ascii=False, sort_keys=False, indent=4, separators=(',', ': '), )  # .encode('UTF-8')
    return js


if __name__ == '__main__':
    # yapf: disable
    print(main('fsdss-564'))  # print(main('mgold-017'))    # 地址带 -  # print(main('votan-034'))    # falenogroup.com 番号和数字加空格才能搜到  # print(main('fcdss-001'))    # 页面地址 flnc001  # print(main('FSDSS-037'))    # poster .replace('_1200-1', '_2125-1')  # print(main('flns-072'))       # outline 换行
