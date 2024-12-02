#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import time  # yapf: disable # NOQA: E402

import urllib3
from lxml import etree

from models.base.web import curl_html

urllib3.disable_warnings()  # yapf: disable


def getWebNumber(html):
    result = html.xpath('//h5[@class=" d-none d-md-block text-primary mb-3"]/text()')
    if result:
        result = result[0].strip()
    else:
        result = ''
    return result


def getTitle(html):
    result = str(html.xpath('//h5[@class=" d-none d-md-block"]/text()')).strip(" ['']")
    return result


def getActor(html):
    try:
        result = str(html.xpath('//li[@class="videoAvstarListItem"]/a/text()')).strip("['']").replace("'", '')
    except:
        result = ''
    return result


def getActorPhoto(actor):
    actor = actor.split(',')
    data = {}
    for i in actor:
        actor_photo = {i: ''}
        data.update(actor_photo)
    return data


def getStudio(html):
    result = str(html.xpath('//a[contains(@href,"video_factory")]/text()')).strip(" ['']")
    return result


def getRelease(html):
    result = str(html.xpath('//ul[@class="list-unstyled pl-2 "]/li/text()')[-1]).strip(" ['']")
    return result


def getYear(getRelease):
    try:
        result = str(re.search(r'\d{4}', getRelease).group())
        return result
    except:
        return getRelease


def getTag(html):
    result = str(html.xpath('//div[@class="tagBtnMargin"]/a/text()')).strip(" ['']").replace("'", "")
    return result


def getCover(html):
    try:
        result = str(html.xpath('//div[@class="videoPlayerMobile d-none "]/div/img/@src')[0]).strip(" ['']")
    except:
        result = ''
    return result


def getOutline(html, language, real_url):
    if language == 'zh_cn':
        real_url = real_url.replace('cn.airav.wiki', 'www.airav.wiki').replace('zh_CN', 'zh_TW')
        try:
            result, html_content = curl_html(real_url)
        except:
            pass
        html = etree.fromstring(html_content, etree.HTMLParser())
    result = str(html.xpath('//div[@class="synopsis"]/p/text()')).strip(" ['']")
    return result


def main(number, appoint_url='', log_info='', req_web='', language='zh_cn'):
    start_time = time.time()
    website_name = 'airav'
    req_web += f'-> {website_name}[{language}]'
    number = number.upper()
    if re.match(r'N\d{4}', number):  # n1403
        number = number.lower()
    real_url = appoint_url
    image_cut = 'right'
    image_download = False
    mosaic = '有码'
    if language == 'zh_cn':
        airav_url = 'https://cn.airav.wiki'
    elif language == 'zh_tw':
        airav_url = 'https://www.airav.wiki'
    else:
        airav_url = 'https://jp.airav.wiki'
    web_info = '\n       '
    log_info += f' \n    🌐 airav[{language.replace("zh_", "")}]'
    debug_info = ''

    try:  # 捕获主动抛出的异常
        if not real_url:

            # 通过搜索获取real_url
            url_search = airav_url + '/?search=' + number
            debug_info = f'搜索地址: {url_search} '
            log_info += web_info + debug_info

            # ========================================================================搜索番号
            result, html_search = curl_html(url_search)
            if not result:
                debug_info = f'网络请求错误: {html_search}'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            html = etree.fromstring(html_search, etree.HTMLParser())
            real_url = html.xpath(
                "//div[@class='coverImageBox']/img[@class='img-fluid video-item coverImage' and contains(@alt, $number1) and not(contains(@alt, '克破'))]/../../@href",
                number1=number)

            if real_url:
                real_url = airav_url + real_url[0]
            else:
                debug_info = '搜索结果: 未匹配到番号！'
                log_info += web_info + debug_info
                raise Exception(debug_info)

        if real_url:
            debug_info = f'番号地址: {real_url} '
            log_info += web_info + debug_info
            result, html_content = curl_html(real_url)
            if not result:
                debug_info = f'网络请求错误: {html_content}'
                log_info += web_info + debug_info
                raise Exception(debug_info)

            html_info = etree.fromstring(html_content, etree.HTMLParser())
            title = getTitle(html_info)  # 获取标题
            if not title:
                debug_info = '数据获取失败: 未获取到title！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            web_number = getWebNumber(html_info)  # 获取番号，用来替换标题里的番号
            title = title.replace(web_number, '').strip()
            actor = getActor(html_info)  # 获取actor
            actor_photo = getActorPhoto(actor)
            cover_url = getCover(html_info)  # 获取cover
            outline = getOutline(html_info, language, real_url)
            release = getRelease(html_info)
            year = getYear(release)
            tag = getTag(html_info)
            studio = getStudio(html_info)
            runtime = ''
            score = ''
            series = ''
            director = ''
            publisher = ''
            extrafanart = ''
            if '无码' in tag or '無修正' in tag or '無码' in tag or 'uncensored' in tag.lower():
                mosaic = '无码'

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
                    'source': 'airav',
                    'actor_photo': actor_photo,
                    'cover': cover_url,
                    'poster': '',
                    'extrafanart': extrafanart,
                    'trailer': '',
                    'image_download': image_download,
                    'image_cut': image_cut,
                    'log_info': log_info,
                    'error_info': '',
                    'req_web': req_web + f'({round((time.time() - start_time), )}s) ',
                    'mosaic': mosaic,
                    'website': real_url,
                    'wanted': '',
                }
                debug_info = '数据获取成功！'
                log_info += web_info + debug_info
                dic['log_info'] = log_info
            except Exception as e:
                debug_info = f'数据生成出错: {str(e)}'
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
            'req_web': req_web + f'({round((time.time() - start_time), )}s) ',
        }
    dic = {website_name: {'zh_cn': dic, 'zh_tw': dic, 'jp': dic}}
    js = json.dumps(dic, ensure_ascii=False, sort_keys=False, indent=4, separators=(',', ': '), )  # .encode('UTF-8')
    return js


if __name__ == '__main__':
    # yapf: disable
    # print(main('', 'https://cn.airav.wiki/video/DOCP-324'))
    # print(main('SIVR-160'))
    # print(main('STARS-199'))                                                    # poster图片
    # print(main('APNS-259', language='zh_cn'))
    # print(main('PRED-300')) # 马赛克破坏版
    print(main('abs-141'))  # print(main('HYSD-00083'))  # print(main('IESP-660'))  # print(main('n1403'))  # print(main('GANA-1910'))  # print(main('heyzo-1031'))  # print(main('x-art.19.11.03'))  # print(main('032020-001'))  # print(main('S2M-055'))  # print(main('LUXU-1217'))  # print(main('1101132', ''))  # print(main('OFJE-318'))  # print(main('110119-001'))  # print(main('abs-001'))  # print(main('SSIS-090', ''))  # print(main('SSIS-090', ''))  # print(main('SNIS-016', ''))  # print(main('HYSD-00083', ''))  # print(main('IESP-660', ''))  # print(main('n1403', ''))  # print(main('GANA-1910', ''))  # print(main('heyzo-1031', ''))  # print(main('x-art.19.11.03'))  # print(main('032020-001', ''))  # print(main('S2M-055', ''))  # print(main('LUXU-1217', ''))  # print(main('x-art.19.11.03', ''))
