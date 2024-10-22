#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import time

import urllib3
from lxml import etree

from models.base.web import get_html

urllib3.disable_warnings()  # yapf: disable


# import traceback


def get_web_number(html, number):
    result = html.xpath("//dt[contains(text(),'作品番号')]/following-sibling::dd/text()")
    return result[0].strip() if result else number


def get_title(html):
    try:
        result = html.xpath('//title/text()')[0].split('|')
        number = result[0].strip()
        title = result[1].replace(number, '').strip()
        if not title or '撸撸吧' in title:
            title = number
        return title, number
    except:
        return '', ''


def get_actor(html):
    actor_list = html.xpath('//a[@title="女优"]/text()')
    actor_new_list = []
    for a in actor_list:
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


def get_studio(html):
    result = html.xpath("string(//div[@class='tag_box d-flex flex-wrap p-1 col-12 mb-1']/a[@title='片商'])")
    return result.strip()


def get_extrafanart(html):
    result = html.xpath('//div[@id="stills"]/div/img/@src')
    for i in range(len(result)):
        result[i] = 'https://lulubar.co' + result[i]
    return result


def get_release(html):
    result = html.xpath("//a[contains(@title,'上架日')]/@title")
    return result[0].replace('上架日', '').strip() if result else ''


def get_year(release):
    try:
        result = str(re.search(r'\d{4}', release).group())
        return result
    except:
        return release


def get_mosaic(html):
    result = html.xpath('//div[@class="tag_box d-flex flex-wrap p-1 col-12 mb-1"]/a[@class="tag"]/text()')
    total = ','.join(result)
    mosaic = ''
    if '有码' in total:
        mosaic = '有码'
    elif '国产' in total:
        mosaic = '国产'
    elif '无码' in total:
        mosaic = '无码'
    return mosaic


def get_tag(html):
    result = html.xpath('//div[@class="tag_box d-flex flex-wrap p-1 col-12 mb-1"]/a[@class="tag" and contains(@href,"bytagdetail")]/text()')
    new_list = []
    for a in result:
        new_list.append(a.strip())
    return ','.join(new_list)


def get_cover(html):
    result = html.xpath('//a[@class="notVipAd imgBoxW position-relative d-block"]/img/@src')
    cover = result[0] if result else ''
    return f'https://lulubar.co{cover}' if cover and 'http' not in cover else cover


def get_outline(html):
    a = html.xpath('//p[@class="video_container_info"]/text()')
    return a[0] if a else ''


def get_real_url(html, number):
    result = html.xpath('//a[@class="imgBoxW"]')
    for each in result:
        href = each.get('href')
        title = each.xpath('img/@alt')
        poster = each.xpath('img/@src')
        if title and title[0].startswith(number.lower()) and href:
            poster = f'https://lulubar.co{poster[0]}' if poster else ''
            return 'https://lulubar.co' + href, f'https://lulubar.co{poster}' if poster and 'http' not in poster else poster
    return '', ''


def main(number, appoint_url='', log_info='', req_web='', language='jp'):
    start_time = time.time()
    website_name = 'lulubar'
    req_web += '-> %s' % website_name
    real_url = appoint_url
    image_cut = 'right'
    image_download = False
    url_search = ''
    mosaic = ''
    web_info = '\n       '
    log_info += ' \n    🌐 lulubar'
    debug_info = ''
    poster = ''

    # real_url = 'https://lulubar.co/video/detail?id=340460'

    try:  # 捕获主动抛出的异常
        if not real_url:

            # 通过搜索获取real_url
            url_search = f'https://lulubar.co/video/bysearch?search={number}&page=1'
            debug_info = '搜索地址: %s ' % url_search
            log_info += web_info + debug_info

            # ========================================================================搜索番号
            result, html_search = get_html(url_search)
            if not result:
                debug_info = '网络请求错误: %s ' % html_search
                log_info += web_info + debug_info
                raise Exception(debug_info)

            html = etree.fromstring(html_search, etree.HTMLParser())
            real_url, poster = get_real_url(html, number)
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

            title, number = get_title(html_info)
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
            runtime = ''
            score = ''
            tag = get_tag(html_info)
            series = ''
            director = ''
            studio = get_studio(html_info)
            publisher = ''
            extrafanart = get_extrafanart(html_info)
            trailer = ''
            mosaic = get_mosaic(html_info)
            try:
                dic = {
                    'number': number,
                    'title': title,
                    'originaltitle': title,
                    'actor': actor,
                    'outline': outline,
                    'originalplot': '',
                    'tag': tag,
                    'release': release,
                    'year': year,
                    'runtime': runtime,
                    'score': score,
                    'series': series,
                    'director': director,
                    'studio': studio,
                    'publisher': publisher,
                    'source': 'lulubar',
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
    # print(main('TRE-82'))   # 没有背景图，封面图查找路径变了
    # print(main('gsad-18'))   # 没有结果
    print(main('SSIS-463'))  # print(main('ebod-900'))         # 双人  # print(main('MDHT-0009'))    # 国产  # print(main('GHOV-21'))  # print(main('GHOV-28'))  # print(main('MIAE-346'))  # print(main('STARS-1919'))    # poster图片  # print(main('abw-157'))  # print(main('abs-141'))
