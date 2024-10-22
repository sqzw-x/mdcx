#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import time  # yapf: disable # NOQA: E402

import urllib3
from lxml import etree

from models.base.web import curl_html
from models.config.config import config

urllib3.disable_warnings()  # yapf: disable


# import traceback


def get_real_url(html, number, domain_2):
    real_url = ''
    new_number = number.strip().replace('-', '').upper() + ' '
    result = html.xpath('//div[@id="video_title"]/h3/a/text()')

    for each in result:
        if new_number in each.replace('-', '').upper():
            real_url = html.xpath('//div[@id="video_title"]/h3/a[contains(text(), $title)]/@href', title=each)[0]
            real_url = domain_2[:-3] + real_url
            return real_url
    result = html.xpath('//a[contains(@href, "/?v=jav")]/@title')

    for each in result:
        if new_number in each.replace('-', '').upper():
            real_url = html.xpath('//a[@title=$title]/@href', title=each)[0]
            real_url = domain_2 + real_url[1:]
            if 'ブルーレイディスク' not in each:
                return real_url
    if real_url:
        return real_url


def get_title(html):
    result = html.xpath('//div[@id="video_title"]/h3/a/text()')
    if result:
        result = result[0].strip()
    else:
        result = ''
    return result


def get_number(html, number):
    result = html.xpath('//div[@id="video_id"]/table/tr/td[@class="text"]/text()')
    return result[0] if result else number


def get_actor(html):
    result = html.xpath('//div[@id="video_cast"]/table/tr/td[@class="text"]/span/span[@class="star"]/a/text()')
    if result:
        result = str(result).strip(' []').replace("'", '').replace(', ', ',')
    else:
        result = ''
    return result


def get_actor_photo(actor):
    actor_photo = {}
    if actor:
        actor_list = actor.split(',')
        for each in actor_list:
            actor_photo[each] = ''
    return actor_photo


def get_cover(html):
    result = html.xpath("//img[@id='video_jacket_img']/@src")
    if result:
        if 'http' not in result[0]:
            result = 'https:' + result[0]
        else:
            result = result[0]
    else:
        result = ''
    return result


def get_tag(html):
    result = html.xpath('//div[@id="video_genres"]/table/tr/td[@class="text"]/span/a/text()')
    if result:
        result = str(result).strip(' []').replace("'", '').replace(', ', ',')
    else:
        result = ''
    return result


def get_release(html):
    result = html.xpath('//div[@id="video_date"]/table/tr/td[@class="text"]/text()')
    if result:
        result = str(result).strip(' []').replace("'", '').replace(', ', ',')
    else:
        result = ''
    return result


def get_year(release):
    try:
        result = str(re.search(r'\d{4}', release).group())
        return result
    except:
        return release[:4]


def get_studio(html):
    result = html.xpath('//div[@id="video_maker"]/table/tr/td[@class="text"]/span/a/text()')
    if result:
        result = result[0]
    else:
        result = ''
    return result


def get_publisher(html):
    result = html.xpath('//div[@id="video_label"]/table/tr/td[@class="text"]/span/a/text()')
    if result:
        result = result[0]
    else:
        result = ''
    return result


def get_runtime(html):
    result = html.xpath('//div[@id="video_length"]/table/tr/td/span[@class="text"]/text()')
    if result:
        result = result[0]
    else:
        result = ''
    return result


def get_score(html):
    result = html.xpath('//div[@id="video_review"]/table/tr/td/span[@class="score"]/text()')
    if result:
        result = result[0].strip('()')
    else:
        result = ''
    return result


def get_director(html):
    result = html.xpath('//div[@id="video_director"]/table/tr/td[@class="text"]/span/a/text()')
    if result:
        result = result[0]
    else:
        result = ''
    return result


def get_wanted(html):
    result = html.xpath('//a[contains(@href, "userswanted.php?")]/text()')
    return str(result[0]) if result else ''


def main(number, appoint_url='', log_info='', req_web='', language='zh_cn'):
    start_time = time.time()
    website_name = 'javlibrary'
    req_web += '-> %s[%s]' % (website_name, language)
    proxies = True

    domain = 'https://www.javlibrary.com'
    if hasattr(config, 'javlibrary_website'):
        domain = config.javlibrary_website
        proxies = False
    real_url = appoint_url
    title = ''
    cover_url = ''
    url_search = ''
    if language == 'zh_cn':
        javlibrary_url = domain + '/cn/vl_searchbyid.php?keyword='
        domain_2 = f'{domain}/cn'
    elif language == 'zh_tw':
        javlibrary_url = domain + '/tw/vl_searchbyid.php?keyword='
        domain_2 = f'{domain}/tw'
    else:
        javlibrary_url = domain + '/ja/vl_searchbyid.php?keyword='
        domain_2 = f'{domain}/ja'
    web_info = '\n       '
    log_info += ' \n    🌐 javlibrary[%s]' % language.replace('zh_', '')
    debug_info = ''

    try:  # 捕获主动抛出的异常
        if not real_url:

            # 生成搜索地址
            url_search = javlibrary_url + number
            debug_info = '搜索地址: %s ' % url_search
            log_info += web_info + debug_info

            result, html_search = curl_html(url_search, proxies=proxies)
            if not result:
                debug_info = '请求错误: %s ' % html_search
                log_info += web_info + debug_info
                raise Exception(debug_info)

            # 判断返回内容是否有问题
            if 'Cloudflare' in html_search:
                real_url = ''
                debug_info = '搜索结果: 被 Cloudflare 5 秒盾拦截！'
                log_info += web_info + debug_info
                raise Exception(debug_info)

            # 获取链接
            html = etree.fromstring(html_search, etree.HTMLParser())
            real_url = get_real_url(html, number, domain_2)
            if not real_url:
                debug_info = '搜索结果: 未匹配到番号！'
                log_info += web_info + debug_info
                raise Exception(debug_info)

        if real_url:
            debug_info = '番号地址: %s ' % real_url
            log_info += web_info + debug_info

            result, html_info = curl_html(real_url, proxies=proxies)
            if not result:
                debug_info = '请求错误: %s ' % html_info
                log_info += web_info + debug_info
                raise Exception(debug_info)

            # 判断返回内容是否有问题
            if 'Cloudflare' in html_info:
                real_url = ''
                debug_info = '搜索结果: 被 Cloudflare 5 秒盾拦截！'
                log_info += web_info + debug_info
                raise Exception(debug_info)

            html_detail = etree.fromstring(html_info, etree.HTMLParser())
            title = get_title(html_detail)
            if not title:
                debug_info = '数据获取失败: 未获取到标题！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            web_number = get_number(html_detail, number)
            title = title.replace(web_number + ' ', '')  # 去掉标题里的番号
            actor = get_actor(html_detail)  # 获取actor
            actor_photo = get_actor_photo(actor)
            cover_url = get_cover(html_detail)  # 获取cover
            tag = get_tag(html_detail)
            release = get_release(html_detail)
            year = get_year(release)
            studio = get_studio(html_detail)
            publisher = get_publisher(html_detail)
            runtime = get_runtime(html_detail)
            score = get_score(html_detail)
            director = get_director(html_detail)
            wanted = get_wanted(html_detail)

            try:
                dic = {
                    'number': web_number,
                    'title': title,
                    'originaltitle': title,
                    'actor': actor,
                    'outline': '',
                    'originalplot': '',
                    'tag': tag,
                    'release': release,
                    'year': year,
                    'runtime': runtime,
                    'score': score,
                    'series': '',
                    'director': director,
                    'studio': studio,
                    'publisher': publisher,
                    'source': 'javlibrary',
                    'website': real_url,
                    'actor_photo': actor_photo,
                    'cover': cover_url,
                    'poster': '',
                    'extrafanart': '',
                    'trailer': '',
                    'image_download': False,
                    'image_cut': 'right',
                    'log_info': log_info,
                    'error_info': '',
                    'req_web': req_web + '(%ss) ' % (round((time.time() - start_time), )),
                    'mosaic': '有码',
                    'wanted': wanted,
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
    dic = {website_name: {language: dic}}
    js = json.dumps(dic, ensure_ascii=False, sort_keys=False, indent=4, separators=(',', ': '), )  # .encode('UTF-8')
    return js


if __name__ == '__main__':
    # print(main('ABW-203'))
    # print(main('SSNI-99'))
    # print(main('SSNI-990'))
    # print(main('SSNI-994'))
    # print(main('SSNI-795'))
    # print(main(' IPX-071'))
    print(main('SNIS-003'))  # print(main('SSIS-118'))  # print(main('AA-007'))  # print(main('abs-141'))  # print(main('HYSD-00083'))  # print(main('IESP-660'))  # print(main('n1403'))  # print(main('GANA-1910'))  # print(main('heyzo-1031'))  # print(main_us('x-art.19.11.03'))  # print(main('032020-001'))  # print(main('S2M-055'))  # print(main('LUXU-1217'))  # print(main('SSIS-001', ''))  # print(main('SSIS-090', ''))  # print(main('SNIS-016', ''))  # print(main('HYSD-00083', ''))  # print(main('IESP-660', ''))  # print(main('n1403', ''))  # print(main('GANA-1910', ''))  # print(main('heyzo-1031', ''))  # print(main_us('x-art.19.11.03'))  # print(main('032020-001', ''))  # print(main('S2M-055', ''))  # print(main('LUXU-1217', ''))  # print(main_us('x-art.19.11.03', ''))
