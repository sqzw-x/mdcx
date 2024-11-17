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


def get_title(html):
    result = html.xpath('//h1[@class="h4 b"]/text()')
    result = str(result[0]).strip() if result else ''
    # 去掉无意义的简介(马赛克破坏版)，'克破'两字简繁同形
    if not result or '克破' in result:
        return ''
    return result


def get_real_title(title):
    temp_t = title.strip(' ').split(' ')
    if len(temp_t) > 1 and len(temp_t[-1]) < 5:
        temp_t.pop()
    return ' '.join(temp_t).strip()


def getWebNumber(title, number):
    result = title.split(' ')
    if len(result) > 1:
        result = result[-1]
    else:
        result = number.upper()
    return result.replace('_1pondo_', '').replace('1pondo_', '').replace('caribbeancom-', '').replace('caribbeancom', '').replace('-PPV', '').strip(' _-')


def getActor(html):
    actor_list = html.xpath('//a[contains(@href, "actor")]/span/text()')
    result = ','.join(actor_list) if actor_list else ""
    return result


def getActorPhoto(actor):
    actor = actor.split(',')
    data = {}
    for i in actor:
        actor_photo = {i: ''}
        data.update(actor_photo)
    return data


def getCover(html):
    result = html.xpath('//meta[@property="og:image"]/@content')
    if result:
        result = result[0]
    else:
        result = ''
    return result


def getOutline(html):
    result = html.xpath('//p[contains(., "简介") or contains(., "簡介")]/text()')
    result = str(result[0]).strip() if result else ''
    # 去掉无意义的简介(马赛克破坏版)，'克破'两字简繁同形
    if not result or '克破' in result:
        return ''
    else:
        # 去除简介中的无意义信息，中间和首尾的空白字符、简介两字、*根据分发等
        result = re.sub(r'[\n\t]|(简|簡)介：', '', result).split('*根据分发', 1)[0].strip()
    return result


def getRelease(html):
    result = html.xpath('//div[@class="date"]/text()')
    if result:
        result = result[0].replace('/', '-').strip()
    else:
        result = ''
    return result


def getYear(release):
    try:
        result = str(re.search(r'\d{4}', release).group())
        return result
    except:
        return release[:4]


def getTag(html):
    tag_list = html.xpath('//div[contains(@class,"tag-info")]//a[contains(@href, "tag")]/text()')
    if tag_list:
        result = ','.join(tag_list) if tag_list else ""
    else:
        result = ''
    return result


def getMosaic(tag):
    if '无码' in tag or '無碼' in tag or '無修正' in tag:
        mosaic = '无码'
    else:
        mosaic = '有码'
    return mosaic


def getStudio(html):
    result = html.xpath('//a[contains(@href, "fac")]/div[@itemprop]/text()')
    if result:
        result = result[0].strip()
    else:
        result = ''
    return result


def getRuntime(html):
    result = html.xpath('//meta[@itemprop="duration"]/@content')
    if result:
        result = result[0].strip().split(':')
        if len(result) == 3:
            result = int(int(result[0]) * 60 + int(result[1]) + int(result[2]) / 60)
    else:
        result = ''
    return str(result)


def get_series(html):
    result = html.xpath('//a[contains(@href, "series")]/text()')
    result = result[0] if result else ''
    return result


def get_extrafanart(html):
    extrafanart_list = html.xpath('//div[@class="cover"]//img[@src]/@data-src')
    return extrafanart_list


def get_real_url(html, number):
    number = number.replace('FC2', '').replace('-PPV', '')
    # 非 fc2 影片前面加入空格，可能会导致识别率降低
    # if not re.search(r'\d+[-_]\d+', number):
    #     number1 = ' ' + number.replace('FC2', '').replace('-PPV', '')
    item_list = html.xpath('//span[@class="title"]')
    for each in item_list:
        detail_url = each.xpath('./a/@href')[0]
        title = each.xpath('./a/@title')[0]
        # 注意去除马赛克破坏版等几乎没有有效字段的条目
        if number.upper() in title and all(keyword not in title for keyword in ['克破', '无码破解', '無碼破解', '无码流出', '無碼流出']):
            return detail_url
    return ''


def main(number, appoint_url='', log_info='', req_web='', language='zh_cn'):
    start_time = time.time()
    website_name = 'iqqtv'
    req_web += '-> %s[%s]' % (website_name, language)

    if not re.match(r'n\d{4}', number):
        number = number.upper()
    if appoint_url:
        real_url = appoint_url
    else:
        real_url = ''
    iqqtv_url = getattr(config, "iqqtv_website", "https://iqq5.xyz")
    cover_url = ''
    image_cut = 'right'
    image_download = False
    mosaic = ''
    url_search = ''
    if language == 'zh_cn':
        iqqtv_url = iqqtv_url + '/cn/'
    elif language == 'zh_tw':
        iqqtv_url = iqqtv_url + '/'
    else:
        iqqtv_url = iqqtv_url + '/jp/'
    # web_info = ' \n    >>> ' + "%-10s" % '[iqqtv] '
    web_info = '\n       '
    log_info += ' \n    🌐 iqqtv[%s]' % language
    debug_info = ''

    try:  # 捕获主动抛出的异常
        if not real_url:

            # 通过搜索获取real_url
            url_search = iqqtv_url + 'search.php?kw=' + number
            debug_info = '搜索地址: %s ' % url_search
            log_info += web_info + debug_info

            # ========================================================================搜索番号
            result, html_search = get_html(url_search)
            if not result:
                debug_info = '网络请求错误: %s' % html_search
                log_info += web_info + debug_info
                raise Exception(debug_info)
            html = etree.fromstring(html_search, etree.HTMLParser())
            real_url = html.xpath('//a[@class="ga_click"]/@href')
            if real_url:
                real_url_tmp = get_real_url(html, number)
                real_url = iqqtv_url + real_url_tmp.replace('/cn/', '').replace('/jp/', '').replace('&cat=19', '')
            else:
                debug_info = '搜索结果: 未匹配到番号！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
        else:
            real_url = iqqtv_url + re.sub(r'.*player', 'player', appoint_url)

        debug_info = '番号地址: %s ' % real_url
        log_info += web_info + debug_info
        result, html_content = get_html(real_url)
        if not result:
            debug_info = '网络请求错误: %s' % html_content
            log_info += web_info + debug_info
            raise Exception(debug_info)
        html_info = etree.fromstring(html_content, etree.HTMLParser())

        title = get_title(html_info)  # 获取标题
        if not title:
            debug_info = '数据获取失败: 未获取到title！'
            log_info += web_info + debug_info
            raise Exception(debug_info)
        web_number = getWebNumber(title, number)  # 获取番号，用来替换标题里的番号
        title = title.replace(' %s' % web_number, '').strip()
        actor = getActor(html_info)  # 获取actor
        actor_photo = getActorPhoto(actor)
        title = get_real_title(title)
        cover_url = getCover(html_info)  # 获取cover
        outline = getOutline(html_info)
        release = getRelease(html_info)
        year = getYear(release)
        tag = getTag(html_info)
        mosaic = getMosaic(tag)
        if mosaic == '无码':
            image_cut = 'center'
        studio = getStudio(html_info)
        runtime = ''
        score = ''
        series = get_series(html_info)
        director = ''
        publisher = studio
        extrafanart = get_extrafanart(html_info)
        tag = tag.replace('无码片', '').replace('無碼片', '').replace('無修正', '')
        try:
            dic = {
                'number': web_number,
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
                'source': 'iqqtv',
                'website': real_url,
                'actor_photo': actor_photo,
                'cover': cover_url,
                'poster': '',
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
    dic = {website_name: {language: dic}}
    js = json.dumps(dic, ensure_ascii=False, sort_keys=False, indent=4, separators=(',', ': '), )  # .encode('UTF-8')
    return js


if __name__ == '__main__':
    # yapf: disable
    # print(main('mimk-095'))
    # print(main('abp-554'))
    # print(main('gs-067'))
    # print(main('110912-179'))
    # print(main('abs-141'))
    # print(main('FC2-906625'))
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
    # print(main_us('x-art.19.11.03'))
    # print(main('032020-001', ''))
    # print(main('S2M-055', ''))
    # print(main('LUXU-1217', ''))
    # print(main('aldn-334', ''))           # 存在系列字段
    # print(main('ssni-200', ''))           # 存在多个搜索结果
    # print(main('START-104', language='zh_tw'))      # 简介存在无效信息  "*根据分发方式,内容可能会有所不同"
    print(main('abs-141'))  # 一个搜索结果
    print(main('MIAB-204'))  # 多个搜索结果
    print(main('ABF-131', ''))  # 无码破解
