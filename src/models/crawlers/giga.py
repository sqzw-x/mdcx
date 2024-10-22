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
    result = html.xpath('//div[@id="works_pic"]/ul/li/h5/text()')
    return result[0].strip() if result else ''


def get_actor(html):
    try:
        actor_list = html.xpath('//span[@class="yaku"]/a/text()')
        result = ','.join(actor_list)
    except:
        result = ''
    return result


def get_actor_photo(actor):
    actor = actor.split(',')
    data = {}
    for i in actor:
        actor_photo = {i: ''}
        data.update(actor_photo)
    return data


def get_director(html):
    result = html.xpath("string(//dt[contains(text(),'監督')]/following-sibling::dd)")
    return result


def get_extrafanart(html):
    result = html.xpath('//div[@class="gasatsu_images_pc"]/div/div/a/@href')
    for i in range(len(result)):
        result[i] = 'https://www.giga-web.jp' + result[i]
    return result


def get_release(html):
    result = html.xpath("//dt[contains(text(),'リリース')]/following-sibling::dd/text()")
    return result[0].replace('/', '-') if result else ''


def get_year(release):
    try:
        result = str(re.search(r'\d{4}', release).group())
        return result
    except:
        return release


def get_runtime(html):
    result = html.xpath("//dt[contains(text(),'収録時間')]/following-sibling::dd/text()")
    if result:
        result = re.findall(r'\d+', result[0])
    return result[0] if result else ''


def get_score(html):
    result = re.findall(r'5点満点中 <b>(.+)<', html)
    return result[0] if result else ''


def get_tag(html):
    result = html.xpath('//div[@id="tag_main"]/a/text()')
    return ','.join(result) if result else ''


def get_trailer(real_url):
    # https://www.giga-web.jp/product/index.php?product_id=6841
    # https://www.giga-web.jp/product/player_sample.php?id=6841&q=h
    url = real_url.replace('index.php?product_id=', 'player_sample.php?id=') + '&q=h'
    result, html = get_html(url)
    if result:
        # <source src="https://cdn-dl.webstream.ne.jp/gigadlcdn/dl/X4baSNNrcDfRdCiSN4we_s_sample/ghov28_6000.mp4" type='video/mp4'>
        result = re.findall(r'<source src="([^"]+)', html)
    return result[0] if result else ''


def get_cover(html):
    result = html.xpath('//div[@class="smh"]/li/ul/li/a/@href')
    cover = result[0].replace('http://', 'https://') if result else ''
    result = html.xpath('//div[@class="smh"]/li/ul/li/a/img/@src')
    poster = result[0] if result else cover.replace('pac_l', 'pac_s')
    if not poster:  # tre-82
        result = html.xpath('//div[@class="smh"]/li/img/@src')
        poster = result[0] if result else ''
        cover = poster.replace('pac_s', 'pac_l')
    return poster, cover


def get_outline(html):
    a = html.xpath('//div[@id="story_list2"]/ul/li[@class="story_window"]/text()')
    a = a[0].replace('[BAD END]', '').strip() if a else ''
    b = html.xpath('//div[@id="eye_list2"]/ul/li[@class="story_window"]/text()')
    b = b[0].replace('[BAD END]', '').strip() if b else ''
    return (a + '\n' + b).strip()


def get_real_url(html, number):
    result = html.xpath('//div[@class="search_sam_box"]')
    for each in result:
        href = each.xpath('a/@href')
        title = each.xpath('string()')
        if f'（{number.upper()}）' in title and href:
            return 'https://www.giga-web.jp' + href[0]
    return ''


def main(number, appoint_url='', log_info='', req_web='', language='jp'):
    start_time = time.time()
    website_name = 'giga'
    req_web += '-> %s' % website_name
    real_url = appoint_url
    image_cut = 'right'
    image_download = True
    url_search = ''
    mosaic = '有码'
    web_info = '\n       '
    log_info += ' \n    🌐 giga'
    debug_info = ''

    # real_url = 'https://www.giga-web.jp/product/index.php?product_id=6835'

    try:  # 捕获主动抛出的异常
        if not real_url:

            # 通过搜索获取real_url https://www.giga-web.jp/search/?keyword=GHOV-22
            url_search = f'https://www.giga-web.jp/search/?keyword={number}'
            debug_info = '搜索地址: %s ' % url_search
            log_info += web_info + debug_info

            # ========================================================================搜索番号
            result, html_search = get_html(url_search)
            if not result:
                debug_info = '网络请求错误: %s ' % html_search
                log_info += web_info + debug_info
                raise Exception(debug_info)

            if '/cookie_set.php' in html_search:
                url_cookies = 'https://www.giga-web.jp/cookie_set.php'
                result, html_cookies = get_html(url_cookies)
                if not result:
                    debug_info = '网络请求错误: %s ' % html_cookies
                    log_info += web_info + debug_info
                    raise Exception(debug_info)
                result, html_search = get_html(url_search)
                if not result:
                    debug_info = '网络请求错误: %s ' % html_search
                    log_info += web_info + debug_info
                    raise Exception(debug_info)

            html = etree.fromstring(html_search, etree.HTMLParser())
            real_url = get_real_url(html, number)
            if not real_url:
                debug_info = '搜索结果: 未匹配到番号！'
                log_info += web_info + debug_info
                raise Exception(debug_info)

        if real_url:
            debug_info = '番号地址: %s' % real_url
            log_info += web_info + debug_info
            result, html_content = get_html(real_url)
            if not result:
                debug_info = '网络请求错误: %s' % html_content
                log_info += web_info + debug_info
                raise Exception(debug_info)
            html_info = etree.fromstring(html_content, etree.HTMLParser())

            title = get_title(html_info)
            if not title:
                debug_info = '数据获取失败: 未获取到title！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            number = get_web_number(html_info, number)
            outline = get_outline(html_info)
            actor = get_actor(html_info)
            actor_photo = get_actor_photo(actor)
            poster, cover_url = get_cover(html_info)
            release = get_release(html_info)
            year = get_year(release)
            runtime = get_runtime(html_info)
            score = get_score(html_content)
            tag = get_tag(html_info)
            series = ''
            director = get_director(html_info)
            studio = 'GIGA'
            publisher = 'GIGA'
            extrafanart = get_extrafanart(html_info)
            trailer = get_trailer(real_url)
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
                    'source': 'giga',
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
    print(main('gsad-18'))  # 没有背景图，封面图查找路径变了  # print(main('GHOV-21'))  # print(main('GHOV-28'))  # print(main('MIAE-346'))  # print(main('STARS-1919'))    # poster图片  # print(main('abw-157'))  # print(main('abs-141'))
