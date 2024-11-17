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


def get_web_number(html, number):
    result = html.xpath('//h2[@class]//span[@class="truncate"]/text()')
    return result[0].strip() if result else number


def get_title(html):
    result = html.xpath('//span[@class="truncate p-2 text-primary font-bold dark:text-primary-200"]/text()')
    title = result[0] if result else ''
    rep_char_list = ['[VIP会员点播] ', '[VIP會員點播] ', '[VIP] ', '★ (请到免费赠片区观赏)', '(破解版獨家中文)']
    for rep_char in rep_char_list:
        title = title.replace(rep_char, '')
    return title.strip()


def get_actor(html):
    actor_list = html.xpath('//dd[@class="flex gap-2 flex-wrap"]/a[contains(@href, "actor")]/text()')
    new_list = [each.strip() for each in actor_list]
    return ','.join(new_list)


def get_actor_photo(actor):
    actor = actor.split(',')
    data = {}
    for i in actor:
        actor_photo = {i: ''}
        data.update(actor_photo)
    return data


def get_outline(html):
    result = html.xpath('string(//h2[contains(text(), "劇情簡介")]/following-sibling::p)')
    rep_list = ['(中文字幕1280x720)', '(日本同步最新‧中文字幕1280x720)', '(日本同步最新‧中文字幕)', '(日本同步最新‧完整激薄版‧中文字幕1280x720)',
                '＊日本女優＊ 劇情做愛影片 ＊完整日本版＊', '＊日本女優＊ 剧情做爱影片 ＊完整日本版＊', '&nbsp;', '<br/>', '<p>', '</p>',
                '<style type=\"text/css\"><!--td {border: 1px solid #ccc;}br {mso-data-placement:same-cell;}-->\n</style>\n',
                '<table style=\"border-collapse:collapse; width:54pt; border:none\" width=\"72\">\n\t<colgroup>\n\t\t<col style=\"width:54pt\" width=\"72\" />\n\t</colgroup>\n\t<tbody>\n\t\t<tr height=\"22\" style=\"height:16.5pt\">\n\t\t\t<td height=\"22\" style=\"border:none; height:16.5pt; width:54pt; padding-top:1px; padding-right:1px; padding-left:1px; vertical-align:middle; white-space:nowrap\" width=\"72\"><span style=\"font-size:12pt\"><span style=\"color:black\"><span style=\"font-weight:400\"><span style=\"font-style:normal\"><span style=\"text-decoration:none\"><span style=\"font-family:新細明體,serif\">',
                '</span></span></span></span></span></span></td>\n\t\t</tr>\n\t</tbody>\n</table>', '★ (请到免费赠片区观赏)']
    for each in rep_list:
        result = result.replace(each, '').strip()
    return result


def get_studio(html):
    result = html.xpath('string(//dt[contains(text(), "製作商")]/following-sibling::dd)')
    return result.strip()


def get_runtime(html):
    runtime = ''
    result = html.xpath('string(//dt[contains(text(), "片長")]/following-sibling::dd)').strip()
    result = re.findall(r'\d+', result)
    if len(result) == 3:
        runtime = int(result[0]) * 60 + int(result[1])
    return runtime


def get_series(html):
    result = html.xpath('//span[contains(text(), "系列：")]/following-sibling::span/text()')
    return result[0].strip() if result else ''


def get_director(html):
    result = html.xpath('//span[contains(text(), "导演：")]/following-sibling::span/a/text()')
    return result[0].strip() if result else ''


def get_release(html):
    result = html.xpath('//div/dt[contains(text(), "上架日")]/../dd/text()')
    return result[0].replace('/', '-').strip() if result else ''


def get_year(release):
    try:
        result = str(re.search(r'\d{4}', release).group())
        return result
    except:
        return release


def get_tag(html):
    result = html.xpath('//dt[contains(text(), "類別")]/following-sibling::dd/a/@title')
    return ','.join(result)


def get_cover(html):
    result = html.xpath('//div[@class="relative overflow-hidden rounded-md"]/img/@src')
    return result[0] if result else ''


def get_extrafanart(html):
    ex_list = html.xpath('//h2[contains(text(), "精彩劇照")]/following-sibling::ul/li/div[@class="relative overflow-hidden rounded-md"]/img/@src')
    return ex_list


def get_mosaic(html, studio):
    result = html.xpath('string(//h1[@class="vv_title col-12"])')
    mosaic = '无码' if '無碼' in result and '破解版' not in result else '有码'
    return '国产' if '國產' in studio else mosaic


def get_poster(html):
    result = html.xpath('//div[@class="img_box col-4 col-sm-3 col-md-3 d-lg-none"]/img/@src')
    if result:
        return 'https://9sex.tv/cn' + result[0] if 'http' not in result[0] else result[0]


def get_real_url(html, number):
    res_list = html.xpath("//ul[@class]/li/a")
    for each in res_list:
        temp_title = each.xpath('div/h4[contains(@class,"truncate")]/text()')
        temp_url = each.get('href')
        temp_poster = each.xpath('div[@class="relative overflow-hidden rounded-t-md"]/img/@src')
        if temp_title:
            temp_title = temp_title[0]
            if temp_title.upper().startswith(number.upper()) or (f'{number.upper()}-' in temp_title.upper() and temp_title[:1].isdigit()):
                # https://9sex.tv/web/video?id=317900
                # https://9sex.tv/#/home/video/340496
                real_url = temp_url
                poster_url = temp_poster[0] if temp_poster else ''
                return real_url, poster_url
    else:
        return ''


def main(number, appoint_url='', log_info='', req_web='', language=''):
    start_time = time.time()
    website_name = 'avsex'
    req_web += '-> %s' % website_name

    if not re.match(r'n\d{4}', number):
        number = number.upper()
    avsex_url = getattr(config, 'avsex_website', 'https://gg5.co')
    if appoint_url:
        if 'http' in appoint_url:
            avsex_url = re.findall(r'(.*//[^/]*)\/', appoint_url)[0]
        else:
            avsex_url = 'https://' + re.findall(r'([^/]*)\/', appoint_url)[0]
    real_url = appoint_url
    image_cut = 'right'
    mosaic = ''
    url_search = ''
    web_info = '\n       '
    log_info += ' \n    🌐 avsex'
    debug_info = ''
    poster_url = ''
    # real_url = 'https://paycalling.com/#/home/video/332642'
    # real_url = 'https://9sex.tv/web/video?id=317900'
    # real_url = 'https://gg5.co/cn/video/detail/359635'

    try:  # 捕获主动抛出的异常
        if not real_url:

            # https://avsex.cc/web/search?page=1&keyWord=ssis
            # https://paycalling.com/tw/search?_type=films&query=CAWD-582
            # https://gg5.co/cn/search?type=films&query=CAWD-582
            # 获取结果后简繁之后会统一转换，这里优先繁体可能是更稳定些？
            url_search = f'{avsex_url}/tw/search?query={number.lower()}'
            debug_info = '搜索地址: %s ' % url_search
            log_info += web_info + debug_info

            # ========================================================================搜索番号
            result, html_search = curl_html(url_search)
            if not result:
                debug_info = '网络请求错误: %s ' % html_search
                log_info += web_info + debug_info
                raise Exception(debug_info)
            html = etree.fromstring(html_search, etree.HTMLParser())
            real_url, poster_url = get_real_url(html, number)
            if not real_url:
                debug_info = '搜索结果: 未匹配到番号！'
                log_info += web_info + debug_info
                raise Exception(debug_info)

        if real_url:
            debug_info = '番号地址: %s ' % real_url
            log_info += web_info + debug_info

            # https://9sex.tv/#/home/video/332642
            # https://paycalling.com/web/video?id=340715
            result, html_content = curl_html(real_url)
            if not result:
                debug_info = '网络请求错误: %s ' % html_content
                log_info += web_info + debug_info
                raise Exception(debug_info)

            html_info = etree.fromstring(html_content, etree.HTMLParser())
            title = get_title(html_info)
            if not title:
                debug_info = '数据获取失败: 未获取到title！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            number = get_web_number(html_info, number)
            release = get_release(html_info)
            cover_url = get_cover(html_info)
            # poster_url = get_poster(html_info)
            studio = get_studio(html_info)
            publisher = ''
            runtime = get_runtime(html_info)
            score = ''
            series = ''
            director = ''
            trailer = ''
            outline = get_outline(html_info)
            actor = get_actor(html_info)
            actor_photo = get_actor_photo(actor)
            tag = get_tag(html_info)
            year = get_year(release)
            extrafanart = get_extrafanart(html_info)
            mosaic = get_mosaic(html_info, studio)

            try:
                dic = {
                    'number': number,
                    'title': title,
                    'originaltitle': title,
                    'actor': actor,
                    'outline': outline,
                    'originalplot': outline,
                    'tag': tag,
                    'release': release.replace('N/A', ''),
                    'year': year,
                    'runtime': str(runtime).replace('N/A', ''),
                    'score': str(score).replace('N/A', ''),
                    'series': series.replace('N/A', ''),
                    'director': director.replace('N/A', ''),
                    'studio': studio.replace('N/A', ''),
                    'publisher': publisher.replace('N/A', ''),
                    'source': 'avsex',
                    'actor_photo': actor_photo,
                    'cover': cover_url,
                    'poster': poster_url,
                    'extrafanart': extrafanart,
                    'trailer': trailer,
                    'image_download': False,
                    'image_cut': image_cut,
                    'log_info': log_info,
                    'error_info': '',
                    'req_web': req_web + '(%ss) ' % (round((time.time() - start_time), )),
                    'mosaic': mosaic,
                    'website': re.sub(r'http[s]?://[^/]+', avsex_url, real_url),
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
    # print(main('ssni-871'))
    # print(main('stko-003'))
    # print(main('abw-123'))
    # print(main('', 'https://9sex.tv/#/home/video/332642'))
    # print(main('EVA-088'))
    # print(main('SNIS-216'))
    print(main('CAWD-582'))  # print(main('ALDN-107'))  # print(main('ten-024'))  # print(main('459ten-024'))  # print(main('IPX-729'))  # print(main('STARS-199'))    # 无结果  # print(main('SIVR-160'))  # print(main('', 'https://avsex.club/web/video?id=333778'))  # print(main('', 'avsex.club/web/video?id=333778'))  # print(main('ssni-700'))  # print(main('ssis-200'))  # print(main('heyzo-2026'))  # print(main('110219-001'))  # print(main('abw-157'))  # print(main('010520-001'))  # print(main('hbad-599', 'https://avsex.club/web/video?id=333777'))  # print(main('hbad-599', 'https://avsex.club/web/video?id=oo'))  # print(main('abs-141'))  # print(main('HYSD-00083'))  # print(main('IESP-660'))  # print(main('n1403'))  # print(main('GANA-1910'))  # print(main('heyzo-1031'))  # print(main_us('x-art.19.11.03'))  # print(main('032020-001'))  # print(main('S2M-055'))  # print(main('LUXU-1217'))  # print(main('1101132', ''))  # print(main('OFJE-318'))  # print(main('110119-001'))  # print(main('abs-001'))  # print(main('SSIS-090', ''))  # print(main('SSIS-090', ''))  # print(main('SNIS-016', ''))  # print(main('HYSD-00083', ''))  # print(main('IESP-660', ''))  # print(main('n1403', ''))  # print(main('GANA-1910', ''))  # print(main('heyzo-1031', ''))  # print(main_us('x-art.19.11.03'))  # print(main('032020-001', ''))  # print(main('S2M-055', ''))  # print(main('LUXU-1217', ''))  # print(main_us('x-art.19.11.03', ''))
