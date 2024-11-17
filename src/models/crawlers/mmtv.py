#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import time

import urllib3
from lxml import etree

from models.base.number import is_uncensored
from models.base.web import curl_html
from models.config.config import config
from models.crawlers.guochan import get_extra_info

urllib3.disable_warnings()  # yapf: disable


# import Function.config as cf


def get_actor_photo(actor):
    actor = actor.split(',')
    data = {}
    for i in actor:
        actor_photo = {i: ''}
        data.update(actor_photo)
    return data


def get_title(html, web_number):
    result = html.xpath('//h1[@class="fullvideo-title h5 mb-2"]/text()')
    return result[0].replace(web_number, '').strip() if result else ''


def get_actor(html, title, file_path):
    actor_list = html.xpath('//div[@class="fullvideo-idol"]/span/a/text()')
    actor = ''
    if actor_list:
        for each in actor_list:
            '''愛澄玲花,日高ゆりあ（青山ひより） 菜津子 32歳 デザイナー'''
            actor += re.sub(r'（.+）', '', each).split(' ')[0] + ','
    else:
        actor = get_extra_info(title, file_path, info_type="actor")
    return actor.strip(',')


def get_real_url(html, number):
    result = html.xpath('//figure[@class="video-preview"]/a')
    url = ''
    cap_number = number.upper()
    for each in result:
        temp_url = each.get('href')
        temp_title = each.xpath('img/@alt')
        if temp_title and temp_url:
            temp_title = temp_title[0]
            temp_number = temp_title.split(' ')[0]
            if cap_number.startswith('FC2'):
                temp_number_head = cap_number.replace('FC2-', 'FC2-PPV ')
                if temp_title.upper().startswith(temp_number_head):
                    return temp_url
            elif temp_number.upper().startswith(cap_number):
                return temp_url
            elif temp_number.upper().endswith(cap_number) and temp_number.upper().replace(cap_number, '').isdigit():
                return temp_url
    return url


def get_cover(html):
    result = re.findall(r'class="player-cover" ><a><img src="([^"]+)', html)
    if result:
        result = result[0]
        if 'http' not in result:
            result = 'https://7mmtv.tv' + result
    return result if result else ''


def get_outline(html):
    outline, originalplot = '', ''
    result = html.xpath('//div[@class="video-introduction-images-text"]/p/text()')
    if result:
        outline = result[-1]
        originalplot = result[0]
    return outline, originalplot


def get_year(release):
    result = re.search(r'\d{4}', release)
    return result[0] if result else release


def get_release(res):
    release = re.search(r'\d{4}-\d{2}-\d{2}', res)
    return release[0] if release else ''


def get_runtime(s):
    runtime = ''
    if ':' in s:
        temp_list = s.split(":")
        if len(temp_list) == 3:
            runtime = int(temp_list[0]) * 60 + int(temp_list[1])
        elif len(temp_list) <= 2:
            runtime = int(temp_list[0])
    elif '分' in s or 'min' in s:
        a = re.findall(r'(\d+)(分|min)', s)
        if a:
            runtime = a[0][0]
    return str(runtime)


def get_director(html):
    director = ''
    result = html.xpath('//div[@class="col-auto flex-shrink-1 flex-grow-1"]/a[contains(@href,"director")]/text()')
    if result and result[0] != 'N/A' and result[0] != '----':
        director = result[0]
    return director


def get_studio(html):
    studio = ''
    result = html.xpath('//div[@class="col-auto flex-shrink-1 flex-grow-1"]/a[contains(@href,"makersr")]/text()')
    if result and result[0] != 'N/A' and result[0] != '----':
        studio = result[0]
    return studio


def get_publisher(html):
    publisher = ''
    result = html.xpath('//div[@class="col-auto flex-shrink-1 flex-grow-1"]/a[contains(@href,"issuer")]/text()')
    if result and result[0] != 'N/A' and result[0] != '----':
        publisher = result[0]
    return publisher


def get_tag(html):
    result = html.xpath('//div[@class="d-flex flex-wrap categories"]/a/text()')
    return ','.join(result)


def get_extrafanart(html):
    # 前几张
    result1 = html.xpath('//span/img[contains(@class, "lazyload")]/@data-src')
    # 其他隐藏需点击的
    if result2 := html.xpath('//div[contains(@class, "fullvideo")]/script[@language="javascript"]/text()'):
        result2 = re.findall(r'https?://.+?\.jpe?g', str(result2))
    result = result1 + result2
    return result if result else ''


def get_mosaic(html, number):
    try:
        mosaic = ''
        result = html.xpath('//ol[@class="breadcrumb"]')[0].xpath('string(.)')
        if '無碼AV' in result or '國產影片' in result:
            mosaic = '无码'
        elif '有碼AV' in result or '素人AV' in result:
            mosaic = '有码'
    except:
        pass
    if not mosaic:
        if number.upper().startswith('FC2'):
            mosaic = '无码'
        elif is_uncensored(number):
            mosaic = '无码'
        else:
            mosaic = '有码'
    return mosaic


def get_number(html, number):
    result = html.xpath('//div[@class="d-flex mb-4"]/span/text()')
    number = result[0] if result else number
    release = get_release(result[1]) if len(result) >= 2 else ''
    runtime = get_runtime(result[2]) if len(result) >= 3 else ''
    return number.replace('FC2-PPV ', 'FC2-'), release, runtime, number


def main(number, appoint_url='', log_info='', req_web='', language='zh_cn', file_path=''):
    start_time = time.time()
    website_name = '7mmtv'
    req_web += '-> %s' % website_name
    title = ''
    cover_url = ''
    web_info = '\n       '
    log_info += ' \n    🌐 7mmtv'
    debug_info = ''
    mmtv_url = getattr(config, '7mmtv_website', 'https://www.7mmtv.sx')
    real_url = appoint_url
    # search_url = "https://bb9711.com/zh/searchform_search/all/index.html"
    # search_url = "https://7mmtv.sx/zh/searchform_search/all/index.html"
    search_url = f"{mmtv_url}/zh/searchform_search/all/index.html"
    mosaic = ''

    try:
        if not real_url:
            search_keyword = number
            if number.upper().startswith('FC2'):
                search_keyword = re.findall(r'\d{3,}', number)[0]

            search_url = f'{search_url}?search_keyword={search_keyword}&search_type=searchall&op=search'
            debug_info = f'搜索地址: {search_url} '
            log_info += web_info + debug_info
            result, response = curl_html(search_url)

            if not result:
                debug_info = '网络请求错误: %s' % response
                log_info += web_info + debug_info
                raise Exception(debug_info)

            detail_page = etree.fromstring(response, etree.HTMLParser())
            real_url = get_real_url(detail_page, number)
            if real_url:
                debug_info = '番号地址: %s ' % real_url
                log_info += web_info + debug_info
            else:
                debug_info = '搜索结果: 未匹配到番号！'
                log_info += web_info + debug_info
                raise Exception(debug_info)

        if real_url:
            result, html_content = curl_html(real_url)
            if not result:
                debug_info = '网络请求错误: %s' % html_content
                log_info += web_info + debug_info
                raise Exception(debug_info)

            html_info = etree.fromstring(html_content, etree.HTMLParser())
            number, release, runtime, web_number = get_number(html_info, number)
            title = get_title(html_info, web_number)
            if not title:
                debug_info = '数据获取失败: 未获取到title！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            actor = get_actor(html_info, title, file_path)
            actor_photo = get_actor_photo(actor)
            cover_url = get_cover(html_content)
            outline, originalplot = get_outline(html_info)
            year = get_year(release)
            director = get_director(html_info)
            studio = get_studio(html_info)
            publisher = get_publisher(html_info)
            tag = get_tag(html_info)
            extrafanart = get_extrafanart(html_info)
            mosaic = get_mosaic(html_info, number)
            try:
                dic = {
                    'number': number,
                    'title': title,
                    'originaltitle': title,
                    'actor': actor,
                    'outline': outline,
                    'originalplot': originalplot,
                    'tag': tag,
                    'release': release,
                    'year': year,
                    'runtime': runtime,
                    'score': '',
                    'series': '',
                    'country': 'CN',
                    'director': director,
                    'studio': studio,
                    'publisher': publisher,
                    'source': '7mmtv',
                    'website': real_url,
                    'actor_photo': actor_photo,
                    'cover': cover_url,
                    'poster': '',
                    'extrafanart': extrafanart,
                    'trailer': '',
                    'image_download': False,
                    'image_cut': '',
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

        # import traceback
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
    # print(main('Fc2-1344765'))  # 26分
    # print(main('FC2-424646'))
    # print(main('极品淫娃学妹Cos凌波丽'))  # 不支持标题中间命中
    # print(main('JUC-694'))
    # print(main('DIY-061'))  # 多人
    # print(main('H4610-ki230225'))
    # print(main('c0930-ki221218'))
    # print(main('c0930-hitozuma1407'))
    # print(main('h0930-ori1665'))
    print(main('h0930-ori1665',
               appoint_url='https://7mm002.com/zh/amateur_content/107108/content.html'))  # print(main('RBD-293'))  # print(main('LUXU-728')) # 无结果  # print(main('fc2-1050737'))  # 标题中有/  # print(main('fc2-2724807'))  # print(main('luxu-1257'))  # print(main('heyzo-1031'))  # print(main('ABP-905'))  # print(main('heyzo-1031', ''))
