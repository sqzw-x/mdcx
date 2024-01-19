#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import time
import urllib

import unicodedata
import urllib3
from lxml import etree

from models.base.web import get_html
from models.crawlers import getchu_dl

urllib3.disable_warnings()  # yapf: disable


# import traceback


def get_web_number(html, number):
    result = html.xpath('//td[contains(text(), "品番：")]/following-sibling::td/text()')
    return result[0].strip().upper() if result else number


def get_title(html):
    result = html.xpath('//h1[@id="soft-title"]/text()')
    return result[0].strip() if result else ''


def get_studio(html):
    result = html.xpath('//a[@class="glance"]/text()')
    return result[0] if result else ''


def get_release(html):
    result = html.xpath("//td[contains(text(),'発売日：')]/following-sibling::td/a/text()")
    return result[0].replace('/', '-') if result and re.search(r'\d+', result[0]) else ''


def get_year(release):
    try:
        result = str(re.search(r'\d{4}', release).group())
        return result
    except:
        return release


def get_director(html):
    result = html.xpath("//td[contains(text(),'監督：')]/following-sibling::td/text()")
    if not result:
        result = html.xpath("//a[contains(@href,'person=')]/text()")
    if not result:
        result = html.xpath("//td[contains(text(),'キャラデザイン：')]/following-sibling::td/text()")
    return result[0] if result else ''


def get_runtime(html):
    result = html.xpath("//td[contains(text(),'時間：')]/following-sibling::td/text()")
    if result:
        result = re.findall(r'\d*', result[0])
    return result[0] if result else ''


def get_tag(html):
    result = html.xpath("//td[contains(text(), 'サブジャンル：') or contains(text(), 'カテゴリ：')]/following-sibling::td/a/text()")
    return ','.join(result).replace(',[一覧]', '') if result else ''


def get_cover(html):
    result = html.xpath('//meta[@property="og:image"]/@content')
    if result:
        return 'http://www.getchu.com' + result[0] if 'http' not in result[0] else result[0]
    return ''


def get_outline(html):
    all_info = html.xpath('//div[@class="tablebody"]')
    result = ''
    for each in all_info:
        info = each.xpath('normalize-space(string())')
        result += '\n' + info
    return result.strip()


def get_mosaic(html, mosaic):
    result = html.xpath('//li[@class="genretab current"]/text()')
    if result:
        r = result[0]
        if r == 'アダルトアニメ':
            mosaic = '里番'
        elif r == '書籍・雑誌':
            mosaic = '书籍'
        elif r == 'アニメ':
            mosaic = '动漫'

    return mosaic


def get_extrafanart(html):
    result_list = html.xpath("//div[contains(text(),'サンプル画像')]/following-sibling::div[1]/a/@href")
    result = []
    for each in result_list:
        each = each.replace('./', 'http://www.getchu.com/')
        result.append(each)
    return result


def main(number, appoint_url='', log_info='', req_web='', language='jp'):
    if 'DLID' in number.upper() or 'ITEM' in number.upper() or 'GETCHU' in number.upper() or 'dl.getchu' in appoint_url:
        return getchu_dl.main(number, appoint_url, log_info, req_web, 'jp')
    start_time = time.time()
    website_name = 'getchu'
    getchu_url = 'http://www.getchu.com'
    req_web += '-> %s' % website_name
    real_url = appoint_url.replace('&gc=gc', '') + '&gc=gc' if appoint_url else ''
    cover_url = ''
    image_cut = ''
    image_download = True
    url_search = ''
    web_info = '\n       '
    log_info += ' \n    🌐 getchu'
    debug_info = ''

    # real_url = 'http://www.getchu.com/soft.phtml?id=1141110&gc=gc'
    # real_url = 'http://www.getchu.com/soft.phtml?id=1178713&gc=gc'
    # real_url = 'http://www.getchu.com/soft.phtml?id=1007200&gc=gc'

    try:  # 捕获主动抛出的异常
        if not real_url:
            number = number.replace('10bit', '').replace('裕未', '祐未').replace('“', '”').replace('·', '・')

            keyword = unicodedata.normalize('NFC', number)  # Mac 会拆成两个字符，即 NFD，而网页请求使用的是 NFC
            try:
                keyword = keyword.encode('cp932').decode('shift_jis')  # 转换为常见日文，比如～ 转换成 〜
            except:
                pass
            keyword2 = urllib.parse.quote_plus(keyword,
                                               encoding="EUC-JP")  # quote() 不编码斜线，空格‘ ’编码为‘%20’；quote_plus() 会编码斜线为‘%2F’; 空格‘ ’编码为‘+’
            url_search = f'http://www.getchu.com/php/search.phtml?genre=all&search_keyword={keyword2}&gc=gc'
            # http://www.getchu.com/php/search.phtml?genre=anime_dvd&search_keyword=_WORD_&check_key_dtl=1&submit=&genre=anime_dvd&gc=gc
            debug_info = f'搜索地址: {url_search} '
            log_info += web_info + debug_info

            # ========================================================================搜索番号
            result, html_search = get_html(url_search, encoding='euc-jp', timeout=40)
            if not result:
                debug_info = f'网络请求错误: {html_search} '
                log_info += web_info + debug_info
                raise Exception(debug_info)
            html = etree.fromstring(html_search, etree.HTMLParser())
            url_list = html.xpath("//a[@class='blueb']/@href")
            title_list = html.xpath("//a[@class='blueb']/text()")

            if url_list:
                real_url = getchu_url + url_list[0].replace('../', '/') + '&gc=gc'
                keyword_temp = re.sub(r'[ \[\]\［\］]+', '', keyword)
                for i in range(len(url_list)):
                    title_temp = re.sub(r'[ \[\]\［\］]+', '', title_list[i])
                    if keyword_temp in title_temp:  # 有多个分集时，用标题符合的
                        real_url = getchu_url + url_list[i].replace('../', '/') + '&gc=gc'
                        break
            else:
                debug_info = '搜索结果: 未匹配到番号！'
                log_info += web_info + debug_info
                return getchu_dl.main(number, appoint_url, log_info, req_web, 'jp')

        if real_url:
            debug_info = f'番号地址: {real_url} '
            log_info += web_info + debug_info

            result, html_content = get_html(real_url, encoding='euc-jp', timeout=40)
            if not result:
                debug_info = f'网络请求错误: {html_content} '
                log_info += web_info + debug_info
                raise Exception(debug_info)
            html_info = etree.fromstring(html_content, etree.HTMLParser())
            title = get_title(html_info)
            if not title:
                debug_info = '数据获取失败: 未获取到title！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            outline = get_outline(html_info)
            actor = ''
            actor_photo = {'': ''}
            cover_url = get_cover(html_info)
            number = get_web_number(html_info, number)
            tag = get_tag(html_info)
            studio = get_studio(html_info)
            release = get_release(html_info)
            year = get_year(release)
            runtime = get_runtime(html_info)
            score = ''
            series = ''
            director = get_director(html_info)
            publisher = ''
            extrafanart = get_extrafanart(html_info)
            mosaic = '动漫'
            if '18禁' in html_content:
                mosaic = '里番'
            mosaic = get_mosaic(html_info, mosaic)
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
                    'source': 'getchu',
                    'actor_photo': actor_photo,
                    'cover': cover_url,
                    'poster': cover_url,
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
    dic = {website_name: {'zh_cn': dic, 'zh_tw': dic, 'jp': dic}}
    js = json.dumps(
        dic,
        ensure_ascii=False,
        sort_keys=False,
        indent=4,
        separators=(',', ': '),
    )
    return js


if __name__ == '__main__':
    # yapf: disable
    # print(main('コンビニ○○Z 第三話 あなた、ヤンクレママですよね。旦那に万引きがバレていいんですか？'))
    # print(main('dokidokiりとる大家さん お家賃6突き目 妖しい踊りで悪霊祓い！『婦警』さんのきわどいオシオキ'))
    # print(main('[PoRO]エロコンビニ店長 泣きべそ蓮っ葉・栞～お仕置きじぇらしぃナマ逸機～'))
    print(main('人妻、蜜と肉 第二巻［月野定規］'))
    # print(main('ACHDL-1159'))
    # print(main('好きにしやがれ GOTcomics'))    # 書籍，没有番号
    # print(main('あまあまロ●ータ女装男子レズ キス・フェラ・69からの3P介入'))
    # print(main('DLID4033023'))
    # print(main('', appoint_url='https://dl.getchu.com/i/item4033023'))
    # print(main('ACMDP-1005')) # 有时间、导演，上下集ACMDP-1005B
    # print(main('ISTU-5391'))
    # print(main('INH-392'))
    # print(main('ISTU-5391', appoint_url='http://www.getchu.com/soft.phtml?id=1180483'))
    # print(main('SPY×FAMILY Vol.1 Blu-ray Disc＜初回生産限定版＞'))    # dmm 没有
