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


def get_title(html, title, number, actor_photo):
    if not title:
        result = html.xpath('//title/text()')
        if result:
            title = result[0].replace(number, '')
            for key, value in actor_photo:
                title = title.replace(key, '')
            number_123 = re.findall(r'\d+', number)
            for each in number_123:
                title = title.replace(each, '')
    return title.strip()


def get_actor(html):
    actor_list = html.xpath('//div[@class="video_description"]/a[contains(@href, "performer/")]/text()')
    actor_new_list = []
    for a in actor_list:
        if a.strip():
            actor_new_list.append(a.strip())
    return ','.join(actor_new_list)


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
        result[i] = 'https://lulubar.net' + result[i]
    return result


def get_release(html):
    result = html.xpath('//div[@class="video_description"]/span[contains(text(), "發行時間")]/text()')
    return result[0].replace('發行時間: ', '').strip() if result else ''


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
    result = html.xpath('//div[@class="kv_tag"]/a/text()')
    new_list = []
    for a in result:
        new_list.append(a.strip())
    return ','.join(new_list)


def get_cover(html_content):
    result = re.findall(r"background-image: url\('([^']+)", html_content)
    cover = result[0] if result else ''
    return cover


def get_outline(html):
    a = html.xpath('//div[@class="kv_description"]/text()')
    return a[0].strip() if a else ''


def get_real_url(html):
    title = ''
    real_url = ''
    poster_url = ''
    result = html.xpath('//div[@class="col-sm-2 search_item"]')
    for each in result:
        each_title = each.xpath('a/div[@class="album_text"]/text()')
        each_href = each.xpath('a/@href')
        each_poster = each.xpath('a/div[@class="search_img"]/img/@src')
        if each_title and each_href:
            title = each_title[0]
            real_url = 'https://love6.tv' + each_href[0]
            poster_url = each_poster[0] if each_poster else ''
        break
    return title, real_url, poster_url


def get_webnumber(html, number):
    number_list = html.xpath('//div[@class="video_description"]/span[contains(text(), "番號")]/text()')
    return number_list[0].replace('番號 : ', '').strip() if number_list else number


def main(number, appoint_url='', log_info='', req_web='', language='jp'):
    start_time = time.time()
    website_name = 'love6'
    req_web += '-> %s' % website_name
    real_url = appoint_url
    image_cut = ''
    url_search = ''
    mosaic = ''
    web_info = '\n       '
    log_info += ' \n    🌐 love6'
    debug_info = ''
    title = ''
    poster = ''

    # real_url = 'https://love6.tv/albums/view/NDI2Mw=='

    try:  # 捕获主动抛出的异常
        if not real_url:

            # 通过搜索获取real_url
            url_search = f'https://love6.tv/search/all/?search_text={number}'
            debug_info = f'搜索地址: {url_search} '
            log_info += web_info + debug_info

            # ========================================================================搜索番号
            result, html_search = get_html(url_search)
            if not result:
                debug_info = '网络请求错误: %s ' % html_search
                log_info += web_info + debug_info
                raise Exception(debug_info)

            html = etree.fromstring(html_search, etree.HTMLParser())
            title, real_url, poster = get_real_url(html)
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
            number = get_webnumber(html_info, number)
            actor = get_actor(html_info)
            actor_photo = get_actor_photo(actor)
            title = get_title(html_info, title, number, actor_photo)
            if not title:
                debug_info = '数据获取失败: 未获取到标题'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            outline = get_outline(html_info)
            cover_url = get_cover(html_content)
            tag = get_tag(html_info)
            release = get_release(html_info)
            year = get_year(release)
            runtime = ''
            score = ''
            series = ''
            director = ''
            studio = ''
            publisher = ''
            extrafanart = ''
            trailer = ''
            mosaic = ''
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
                    'source': 'love6',
                    'actor_photo': actor_photo,
                    'cover': cover_url,
                    'poster': poster,
                    'extrafanart': extrafanart,
                    'trailer': trailer,
                    'image_download': False,
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
    # print(main('ras-00'))
    # print(main('ras-0236'))
    # print(main('ras-10236'))
    print(main('MisAV005-01'))
