#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import time

import urllib3
from lxml import etree

from models.base.web import curl_html
from models.config import config
from models.signals import signal

urllib3.disable_warnings()  # yapf: disable


# import traceback


def get_web_number(html):
    result = html.xpath(
        '//p/span[contains(text(), "番號") or contains(text(), "番号")]/../span[@id="ContentPlaceHolder1_Label_barcode"]/text()')
    return result[0].strip() if result else ''


def get_number(html, number):
    result = html.xpath('string(//span[@id="ContentPlaceHolder1_Label_barcode"])')
    return number if number else result


def get_title(html):
    result = html.xpath('//li[@class="vediotitle"]/h1/span/text()')
    return result[0].strip() if result else ''


def get_actor(html):
    try:
        actor_list = html.xpath('//li[@class="allavgirls"]/span/span/span/a/@title')
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


def get_studio(html):
    result = html.xpath('//li[@class="series"]/span/span/span/a/text()')
    return result[0] if result else ''


def get_release(html):
    result = html.xpath('//li[@class="date"]/font/span/text()')
    return result[0].replace('/', '-') if result else ''


def get_year(release):
    try:
        result = str(re.search(r'\d{4}', release).group())
        return result
    except:
        return release


def get_tag(html):
    result = html.xpath('//li[@class="keyword"]/span/span/a/text()')
    return ','.join(result) if result else ''


def get_cover(html):
    result = html.xpath('//img[@id="ContentPlaceHolder1_Image_itemscope"]/@src')
    return result[0] if result else ''


def get_outline(html):
    result = html.xpath('//li[@class="introduction"]/span/text()')
    return result[0] if result else ''


def retry_request(real_url, log_info, web_info):
    result, html_content = curl_html(real_url)
    if not result:
        debug_info = '网络请求错误: %s ' % html_content
        log_info += web_info + debug_info
        raise Exception(debug_info)
    html_info = etree.fromstring(html_content, etree.HTMLParser())
    title = get_title(html_info)  # 获取标题
    if not title:
        debug_info = '数据获取失败: 未获取到title！'
        log_info += web_info + debug_info
        raise Exception(debug_info)
    web_number = get_web_number(html_info)  # 获取番号，用来替换标题里的番号
    web_number1 = '[%s]' % web_number
    title = title.replace(web_number1, '').strip()
    outline = get_outline(html_info)
    actor = get_actor(html_info)  # 获取actor
    cover_url = get_cover(html_info)  # 获取cover
    tag = get_tag(html_info)
    studio = get_studio(html_info)
    return html_info, title, outline, actor, cover_url, tag, studio, log_info


def main(number, appoint_url='', log_info='', req_web='', language='zh_cn'):
    start_time = time.time()
    website_name = 'airav_cc'
    req_web += '-> %s[%s]' % (website_name, language)
    number = number.upper()
    if re.match(r'N\d{4}', number):  # n1403
        number = number.lower()
    real_url = appoint_url
    cover_url = ''
    image_cut = 'right'
    image_download = False
    url_search = ''
    mosaic = '有码'
    airav_url = 'https://airav5.fun'
    if hasattr(config, 'airav_cc_website'):
        airav_url = config.airav_cc_website
    if language == 'zh_cn':
        airav_url += '/cn'
    web_info = '\n       '
    log_info += ' \n    🌐 airav[%s]' % language.replace('zh_', '')
    debug_info = ''

    # real_url = 'https://airav5.fun/jp/playon.aspx?hid=44733'

    try:  # 捕获主动抛出的异常
        if not real_url:

            # 通过搜索获取real_url https://airav5.fun/cn/searchresults.aspx?Search=ssis-200&Type=0
            url_search = airav_url + f'/searchresults.aspx?Search={number}&Type=0'
            debug_info = '搜索地址: %s ' % url_search
            log_info += web_info + debug_info

            # ========================================================================搜索番号
            result, html_search = curl_html(url_search)
            if not result:
                debug_info = '网络请求错误: %s ' % html_search
                log_info += web_info + debug_info
                raise Exception(debug_info)
            html = etree.fromstring(html_search, etree.HTMLParser())
            number2 = ' ' + number.upper()
            real_url = html.xpath(
                "//h3[@class='one_name ga_name' and contains(text(), $number1) and not(contains(text(), '克破'))]/../@href",
                number1=number2)

            # if real_url:
            #     real_url = airav_url + '/' + real_url[0]
            # else:
            if not real_url:
                debug_info = '搜索结果: 未匹配到番号！'
                log_info += web_info + debug_info
                raise Exception(debug_info)

        if real_url:
            if isinstance(real_url, list) and real_url:
                real_url = real_url[0]
            debug_info = '番号地址: %s ' % real_url
            log_info += web_info + debug_info
            for i in range(3):
                html_info, title, outline, actor, cover_url, tag, studio, log_info = retry_request(real_url, log_info,
                                                                                                   web_info)
                temp_str = title + outline + actor + tag + studio
                if '�' not in temp_str:
                    break
                else:
                    debug_info = '%s 请求 airav_cc 返回内容存在乱码 �，尝试第 %s/3 次请求' % (number, (i + 1))
                    signal.add_log(debug_info)
                    log_info += web_info + debug_info
            else:
                debug_info = '%s 已请求三次，返回内容仍存在乱码 � ！视为失败！' % number
                signal.add_log(debug_info)
                log_info += web_info + debug_info
                raise Exception(debug_info)
            actor_photo = get_actor_photo(actor)
            number = get_number(html_info, number)
            release = get_release(html_info)
            year = get_year(release)
            runtime = ''
            score = ''
            series = ''
            director = ''
            publisher = ''
            extrafanart = ''
            if '无码' in tag or '無修正' in tag or '無码' in tag or 'uncensored' in tag.lower():
                mosaic = '无码'
            title_rep = ['第一集', '第二集', ' - 上', ' - 下', ' 上集', ' 下集', ' -上', ' -下']
            for each in title_rep:
                title = title.replace(each, '').strip()
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
                    'source': 'airav_cc',
                    'actor_photo': actor_photo,
                    'cover': cover_url,
                    'poster': cover_url.replace('big_pic', 'small_pic'),
                    'extrafanart': extrafanart,
                    'trailer': '',
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
    dic = {website_name: {language: dic}}
    js = json.dumps(
        dic,
        ensure_ascii=False,
        sort_keys=False,
        indent=4,
        separators=(',', ': '),
    )  # .encode('UTF-8')
    return js


if __name__ == '__main__':
    # yapf: disable
    # print(main('', 'https://airav5.fun/playon.aspx?hid=99-21-46640'))
    # print(main('PRED-300'))    # 马赛克破坏版
    print(main('snis-036', language='jp'))
    # print(main('snis-036'))
    # print(main('MIAE-346'))
    # print(main('STARS-1919'))    # poster图片
    # print(main('abw-157'))
    # print(main('abs-141'))
    # print(main('HYSD-00083'))
    # print(main('IESP-660'))
    # print(main('n1403'))
    # print(main('GANA-1910'))
    # print(main('heyzo-1031'))
    # print(main('x-art.19.11.03'))
    # print(main('032020-001'))
    # print(main('S2M-055'))
    # print(main('LUXU-1217'))
    # print(main('1101132', ''))
    # print(main('OFJE-318'))
    # print(main('110119-001'))
    # print(main('abs-001'))
    # print(main('SSIS-090', ''))
    # print(main('SSIS-090', ''))
    # print(main('SNIS-016', ''))
    # print(main('HYSD-00083', ''))
    # print(main('IESP-660', ''))
    # print(main('n1403', ''))
    # print(main('GANA-1910', ''))
    # print(main('heyzo-1031', ''))
    # print(main('x-art.19.11.03'))
    # print(main('032020-001', ''))
    # print(main('S2M-055', ''))
    # print(main('LUXU-1217', ''))
    # print(main('x-art.19.11.03', ''))
