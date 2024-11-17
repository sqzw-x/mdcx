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


# import traceback


def get_title(html):
    result = html.xpath('//h3/text()')
    if result:
        result = result[0].strip()
    else:
        result = ''
    return result


def getWebNumber(html, number):
    result = html.xpath('//span[@class="header"][contains(text(), "識別碼:")]/../span[2]/text()')
    return result[0] if result else number


def getActor(html):
    try:
        result = str(html.xpath('//div[@class="star-name"]/a/text()')).strip(" ['']").replace("'", '').replace(', ', ',')
    except:
        result = ''
    return result


def getActorPhoto(html, url):
    actor = html.xpath('//div[@class="star-name"]/../a/img/@title')
    photo = html.xpath('//div[@class="star-name"]/../a/img/@src')
    data = {}
    if len(actor) == len(photo):
        for i in range(len(actor)):
            if 'http' not in photo[i]:
                data[actor[i]] = url + photo[i]
            else:
                data[actor[i]] = photo[i]
    else:
        for each in actor:
            data[each] = ''
    return data


def getCover(html, url):  # 获取封面链接
    result = html.xpath('//a[@class="bigImage"]/@href')
    if result:
        if 'http' not in result[0]:
            cover_url = url + result[0]
        else:
            cover_url = result[0]
    else:
        cover_url = ''
    return cover_url


def get_poster_url(cover_url):  # 获取小封面链接
    poster_url = ''
    if '/pics/' in cover_url:
        poster_url = cover_url.replace('/cover/', '/thumb/').replace('_b.jpg', '.jpg')
    elif '/imgs/' in cover_url:
        poster_url = cover_url.replace('/cover/', '/thumbs/').replace('_b.jpg', '.jpg')
    return poster_url


def getRelease(html):  # 获取发行日期
    result = html.xpath('//span[@class="header"][contains(text(), "發行日期:")]/../text()')
    if result:
        result = result[0].strip()
    else:
        result = ''
    return result


def getYear(release):
    try:
        result = str(re.search(r'\d{4}', release).group())
        return result
    except:
        return release[:4]


def getMosaic(html):
    select_tab = str(html.xpath('//li[@class="active"]/a/text()'))
    if '有碼' in select_tab:
        mosaic = '有码'
    else:
        mosaic = '无码'
    return mosaic


def getRuntime(html):
    result = html.xpath('//span[@class="header"][contains(text(), "長度:")]/../text()')
    if result:
        result = result[0].strip()
        result = re.findall(r'\d+', result)
        if result:
            result = result[0]
        else:
            result = ''
    else:
        result = ''
    return result


def getStudio(html):
    result = html.xpath('//a[contains(@href, "/studio/")]/text()')
    if result:
        result = result[0].strip()
    else:
        result = ''
    return result


def getPublisher(html, studio):  # 获取发行商
    result = html.xpath('//a[contains(@href, "/label/")]/text()')
    if result:
        result = result[0].strip()
    else:
        result = studio
    return result


def getDirector(html):  # 获取导演
    result = html.xpath('//a[contains(@href, "/director/")]/text()')
    if result:
        result = result[0].strip()
    else:
        result = ''
    return result


def getSeries(html):
    result = html.xpath('//a[contains(@href, "/series/")]/text()')
    if result:
        result = result[0].strip()
    else:
        result = ''
    return result


def getExtraFanart(html, url):  # 获取封面链接
    result = html.xpath("//div[@id='sample-waterfall']/a/@href")
    if result:
        new_list = []
        for each in result:
            if 'http' not in each:
                each = url + each
            new_list.append(each)
    else:
        new_list = ''
    return new_list


def getTag(html):  # 获取标签
    result = html.xpath('//span[@class="genre"]/label/a[contains(@href, "/genre/")]/text()')
    if result:
        result = str(result).strip(" ['']").replace("'", "").replace(', ', ',')
    else:
        result = ''
    return result


def get_real_url(number, url_type, javbus_url, json_log, headers, cookie):  # 获取详情页链接
    if url_type == 'us':  # 欧美
        url_search = 'https://www.javbus.hair/search/' + number
    elif url_type == 'censored':  # 有码
        url_search = javbus_url + '/search/' + number + '&type=&parent=ce'
    else:  # 无码
        url_search = javbus_url + '/uncensored/search/' + number + '&type=0&parent=uc'

    debug_info = '搜索地址: %s ' % url_search
    json_log['log_info_javbus'] += json_log['web_info'] + debug_info
    # ========================================================================搜索番号
    result, html_search = get_html(url_search, headers)
    # 判断是否需要登录
    if 'lostpasswd' in html_search:
        # 有 cookie
        if cookie:
            raise Exception('Cookie 无效！请重新填写 Cookie 或更新节点！')
        else:
            raise Exception('当前节点需要填写 Cookie 才能刮削！请到 设置-网络 填写 Cookie 或更换节点！')

    if not result:
        debug_info = '网络请求错误: %s ' % html_search
        json_log['log_info_javbus'] += json_log['web_info'] + debug_info
        raise Exception(debug_info)

    html = etree.fromstring(html_search, etree.HTMLParser())
    url_list = html.xpath("//a[@class='movie-box']/@href")
    for each in url_list:
        each_url = each.upper().replace('-', '')
        number_1 = '/' + number.upper().replace('.', '').replace('-', '')
        number_2 = number_1 + '_'
        if each_url.endswith(number_1) or number_2 in each_url:
            debug_info = '番号地址: %s ' % each
            json_log['log_info_javbus'] += json_log['web_info'] + debug_info
            return each
    debug_info = '搜索结果: 未匹配到番号！'
    json_log['log_info_javbus'] += json_log['web_info'] + debug_info
    raise Exception(debug_info)


def main(number, appoint_url='', log_info='', req_web='', language='jp', mosaic=''):
    start_time = time.time()
    website_name = 'javbus'
    req_web += '-> %s' % website_name
    real_url = appoint_url
    javbus_url = getattr(config, 'javbus_website', 'https://www.javbus.com')
    headers = config.headers
    cookie = config.javbus
    headers_o = {'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6', 'cookie': cookie, }
    headers.update(headers_o)

    title = ''
    cover_url = ''
    poster_url = ''
    image_download = False
    image_cut = 'right'
    dic = {}
    web_info = '\n       '
    debug_info = ''
    json_log = {}
    json_log['log_info_javbus'] = log_info + ' \n    🌐 javbus'
    json_log['web_info'] = web_info

    try:
        if not real_url:

            # 欧美去搜索，其他尝试直接拼接地址，没有结果时再搜索
            if '.' in number or re.search(r'[-_]\d{2}[-_]\d{2}[-_]\d{2}', number):  # 欧美影片
                number = number.replace('-', '.').replace('_', '.')
                real_url = get_real_url(number, 'us', javbus_url, json_log, headers, cookie)
            else:
                real_url = javbus_url + '/' + number
                if number.upper().startswith('CWP') or number.upper().startswith('LAF'):
                    temp_number = number.replace('-0', '-')
                    if temp_number[-2] == '-':
                        temp_number = temp_number.replace('-', '-0')
                    real_url = javbus_url + '/' + temp_number

        debug_info = '番号地址: %s ' % real_url
        json_log['log_info_javbus'] += web_info + debug_info
        result, htmlcode = get_html(real_url, headers)

        # 判断是否需要登录
        if 'lostpasswd' in htmlcode:
            # 有 cookie
            if cookie:
                raise Exception('Cookie 无效！请重新填写 Cookie 或更新节点！')
            else:
                raise Exception('当前节点需要填写 Cookie 才能刮削！请到 设置-网络 填写 Cookie 或更换节点！')

        if not result:

            # 有404时尝试再次搜索 DV-1175
            if '404' not in htmlcode:
                debug_info = '番号地址:%s \n       网络请求错误: %s ' % (real_url, htmlcode)
                json_log['log_info_javbus'] += web_info + debug_info
                raise Exception(debug_info)

            # 欧美的不再搜索
            if '.' in number:
                debug_info = '未匹配到番号！'
                json_log['log_info_javbus'] += web_info + debug_info
                raise Exception(debug_info)

            # 无码搜索结果
            elif mosaic == '无码' or mosaic == '無碼':
                real_url = get_real_url(number, 'uncensored', javbus_url, json_log, headers, cookie)

            # 有码搜索结果
            else:
                real_url = get_real_url(number, 'censored', javbus_url, json_log, headers, cookie)

            result, htmlcode = get_html(real_url, headers)
            if not result:
                debug_info = '未匹配到番号！'
                json_log['log_info_javbus'] += web_info + debug_info
                raise Exception(debug_info)

        # 获取详情页内容
        html_info = etree.fromstring(htmlcode, etree.HTMLParser())
        title = get_title(html_info)
        if not title:
            debug_info = '数据获取失败: 未获取到title'
            json_log['log_info_javbus'] += web_info + debug_info
            raise Exception(debug_info)
        number = getWebNumber(html_info, number)  # 获取番号，用来替换标题里的番号
        title = title.replace(number, '').strip()
        actor = getActor(html_info)  # 获取actor
        actor_photo = getActorPhoto(html_info, javbus_url)
        cover_url = getCover(html_info, javbus_url)  # 获取cover
        poster_url = get_poster_url(cover_url)
        release = getRelease(html_info)
        year = getYear(release)
        tag = getTag(html_info)
        mosaic = getMosaic(html_info)
        if mosaic == '无码':
            image_cut = 'center'
            if '_' in number and poster_url:  # 一本道，并且有小图时，下载poster
                image_download = True
            elif 'HEYZO' in number and len(poster_url.replace(javbus_url + '/imgs/thumbs/', '')) == 7:
                image_download = True
            else:
                poster_url = ''  # 非一本道的无码/欧美影片，清空小图地址，因为小图都是未裁剪的低分辨率图片
        runtime = getRuntime(html_info)
        studio = getStudio(html_info)
        publisher = getPublisher(html_info, studio)
        director = getDirector(html_info)
        series = getSeries(html_info)
        extrafanart = getExtraFanart(html_info, javbus_url)
        if 'KMHRS' in number:  # 剧照第一张是高清图
            image_download = True
            if extrafanart:
                poster_url = extrafanart[0]
        try:
            dic = {
                'number': number,
                'title': title,
                'originaltitle': title,
                'actor': actor,
                'outline': '',
                'originalplot': '',
                'tag': tag,
                'release': release,
                'year': year,
                'runtime': runtime,
                'score': '',
                'series': series,
                'director': director,
                'studio': studio,
                'publisher': publisher,
                'source': 'javbus',
                'website': real_url,
                'actor_photo': actor_photo,
                'cover': cover_url,
                'poster': poster_url,
                'extrafanart': extrafanart,
                'trailer': '',
                'image_download': image_download,
                'image_cut': image_cut,
                'log_info': json_log['log_info_javbus'],
                'error_info': '',
                'req_web': req_web + '(%ss) ' % (round((time.time() - start_time), )),
                'mosaic': mosaic,
                'wanted': '',
            }
            debug_info = '数据获取成功！'
            json_log['log_info_javbus'] += web_info + debug_info
            dic['log_info'] = json_log['log_info_javbus']
        except Exception as e:
            debug_info = '数据生成出错: %s' % str(e)
            json_log['log_info_javbus'] += web_info + debug_info
            raise Exception(debug_info)
    except Exception as e:
        debug_info = str(e)
        dic = {
            'title': '',
            'cover': '',
            'website': '',
            'log_info': json_log['log_info_javbus'],
            'error_info': debug_info,
            'req_web': req_web + '(%ss) ' % (round((time.time() - start_time), )),
        }
    dic = {website_name: {'zh_cn': dic, 'zh_tw': dic, 'jp': dic}}
    js = json.dumps(dic, ensure_ascii=False, sort_keys=False, indent=4, separators=(',', ': '), )  # .encode('UTF-8')
    return js


if __name__ == '__main__':
    # yapf: disable
    # print(main('LAFBD-034'))    # cwp,cwpbd 数字为2位时不带0
    print(main('PMAXVR-008'))  # print(main('cwpbd-034'))    # cwp,cwpbd 数字为2位时不带0  # print(main('FC2-1262472'))    # 无结果  # print(main('STARS-199'))    # 禁止  # print(main('EDVR-043'))    # 无结果  # print(main('SSIS-243'))  # print(main('ABW-015'))  # print(main('DASD-972'))  # print(main('ss-036'))    # 无结果  # print(main('KMHRS-050'))  # print(main('KV-115'))    # 无结果  # print(main('070621_001'))  # print(main('heyzo-1031'))  # print(main('heyzo-0811'))  # print(main('heyzo-1673'))  # print(main('dv-1175'))    # 无结果，通过搜索有结果  # print(main('dv1175'))  # print(main('ssni-644'))  # print(main('010115-001'))  # print(main('ssni644'))  # print(main('BigTitsatWork-17-09-26'))  # print(main('BrazzersExxtra.21.02.01'))  # print(main('KA-001'))   # 无结果  # print(main('012715-793'))  # print(main('ssni-644', "https://www.javbus.com/SSNI-644"))  # print(main('ssni-802', ""))  # print(main('DirtyMasseur.20.07.26', "https://www.javbus.hair/DirtyMasseur-21-01-31"))
