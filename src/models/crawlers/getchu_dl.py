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

urllib3.disable_warnings()  # yapf: disable


# import traceback


def get_title(html):
    result = html.xpath('//meta[@property="og:title"]/@content')
    return result[0].strip() if result else ''


def get_studio(html):
    return html.xpath("string(//td[text()='サークル']/following-sibling::td)")


def get_release(html):
    result = html.xpath("//td[contains(text(),'配信開始日')]/following-sibling::td/text()")
    return result[0].replace('/', '-') if result and re.search(r'\d+', result[0]) else ''


def get_year(release):
    try:
        result = str(re.search(r'\d{4}', release).group())
        return result
    except:
        return release


def get_director(html):
    return html.xpath('string(//td[text()="作者"]/following-sibling::td)').strip()


def get_runtime(html):
    result = html.xpath("//td[contains(text(),'画像数&ページ数')]/following-sibling::td/text()")
    if result:
        result = re.findall(r'\d*', result[0])
    return result[0] if result else ''


def get_tag(html):
    result = html.xpath('//td[text()="趣向"]/following-sibling::td/a/text()')
    return ','.join(result) if result else ''


def get_cover(html):
    result = html.xpath('//meta[@property="og:image"]/@content')
    return result[0] if result else ''


def get_outline(html):
    return html.xpath('string(//td[text()="作品内容"]/following-sibling::td)').strip()


def get_extrafanart(html):
    result_list = html.xpath("//a[contains(@href,'/data/item_img/') and @class='highslide']/@href")
    result = []
    for each in result_list:
        result.append(f'https://dl.getchu.com{each}')
    return result


def main(number, appoint_url='', log_info='', req_web='', language='jp'):
    start_time = time.time()
    website_name = 'getchu'
    req_web += '-> %s' % website_name
    real_url = appoint_url
    cover_url = ''
    image_cut = ''
    image_download = True
    url_search = ''
    web_info = '\n       '
    log_info += ' \n    🌐 dl_getchu'
    debug_info = ''
    cookies = {"adult_check_flag": "1"}
    if not real_url and ('DLID' in number.upper() or 'ITEM' in number.upper() or 'GETCHU' in number.upper()):
        id = re.findall(r'\d+', number)[0]
        real_url = f'https://dl.getchu.com/i/item{id}'
        # real_url = 'https://dl.getchu.com/i/item4024984'

    try:  # 捕获主动抛出的异常
        if not real_url:

            keyword = unicodedata.normalize('NFC', number.replace('●', ' '))  # Mac 把会拆成两个字符，即 NFD，而网页请求使用的是 NFC
            try:
                keyword = keyword.encode('cp932').decode('shift_jis')  # 转换为常见日文，比如～ 转换成 〜
            except:
                pass
            keyword2 = urllib.parse.quote_plus(keyword,
                                               encoding="EUC-JP")  # quote() 不编码斜线，空格‘ ’编码为‘%20’；quote_plus() 会编码斜线为‘%2F’; 空格‘ ’编码为‘+’
            url_search = f'https://dl.getchu.com/search/search_list.php?dojin=1&search_category_id=&search_keyword={keyword2}&btnWordSearch=%B8%A1%BA%F7&action=search&set_category_flag=1'
            debug_info = f'搜索地址: {url_search} '
            log_info += web_info + debug_info

            # ========================================================================搜索番号
            result, html_search = get_html(url_search, cookies=cookies, encoding='euc-jp', timeout=40)
            if not result:
                debug_info = f'网络请求错误: {html_search} '
                log_info += web_info + debug_info
                raise Exception(debug_info)
            html = etree.fromstring(html_search, etree.HTMLParser())
            res_list = html.xpath("//table/tr/td[@valign='top' and not (@align)]/div/a")
            for each in res_list:
                temp_url = each.get('href')
                temp_title = each.xpath('string(.)')
                if temp_url and '/item' in temp_url and temp_title and temp_title.startswith(number):
                    real_url = temp_url
                    break
            else:
                debug_info = '搜索结果: 未匹配到番号！'
                log_info += web_info + debug_info
                raise Exception(debug_info)

        if real_url:
            debug_info = f'番号地址: {real_url} '
            log_info += web_info + debug_info

            result, html_content = get_html(real_url, cookies=cookies, encoding='euc-jp', timeout=40)
            if not result:
                debug_info = f'网络请求错误: {html_content} '
                log_info += web_info + debug_info
                raise Exception(debug_info)
            html_info = etree.fromstring(html_content, etree.HTMLParser())
            number = 'DLID-' + re.findall(r'\d+', real_url)[0]
            title = get_title(html_info)
            if not title:
                debug_info = '数据获取失败: 未获取到title！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            outline = get_outline(html_info)
            actor = ''
            actor_photo = {'': ''}
            cover_url = get_cover(html_info)
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
            mosaic = '同人'
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
                    'source': 'dl_getchu',
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
    # print(main('[PoRO]エロコンビニ店長 泣きべそ蓮っ葉・栞～お仕置きじぇらしぃナマ逸機～'))
    # print(main('母ちゃんの友達にシコってるところ見られた。'))
    # print(main('DLID4024984'))
    print(
        main('【姫始めセックス流出】人気Y●u●berリアル彼女とのプライベートハメ撮り映像流出!!初詣帰りに振袖姿のまま彼女にしゃぶらせ生中出し！生々しい映像データ'))
    # print(main('好きにしやがれ GOTcomics'))    # 書籍，没有番号
