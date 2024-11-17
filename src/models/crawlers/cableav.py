#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import time

import urllib3
import zhconv
from lxml import etree

from models.base.web import curl_html
from models.config.config import config
from models.crawlers.guochan import get_extra_info, get_number_list

urllib3.disable_warnings()  # yapf: disable


# import traceback

def get_actor_photo(actor):
    actor = actor.split(',')
    data = {}
    for i in actor:
        actor_photo = {i: ''}
        data.update(actor_photo)
    return data


def get_detail_info(html, number, file_path):
    title_h1 = html.xpath('//div[@class="entry-content "]/p/text()')
    title = title_h1[0].replace(number + ' ', '').strip() if title_h1 else number
    actor = get_extra_info(title, file_path, info_type="actor")
    tmp_tag = html.xpath('//header//div[@class="categories-wrap"]/a/text()')
    # 标签转简体
    tag = zhconv.convert(tmp_tag[0], 'zh-cn') if tmp_tag else ''
    cover_url = html.xpath(f'//meta[@property="og:image"]/@content')
    cover_url = cover_url[0] if cover_url else ''

    return number, title, actor, cover_url, tag


def get_real_url(html, number_list):
    item_list = html.xpath('//h3[contains(@class,"title")]//a[@href and @title]')
    for each in item_list:
        # href="https://cableav.tv/Xq1Sg3SvZPk/"
        detail_url = each.get('href')
        title = each.xpath('text()')[0]
        if title and detail_url:
            for n in number_list:
                temp_n = re.sub(r'[\W_]', '', n).upper()
                temp_title = re.sub(r'[\W_]', '', title).upper()
                if temp_n in temp_title:
                    return True, n, title, detail_url
    return False, '', '', ''


def main(number, appoint_url='', log_info='', req_web='', language='zh_cn', file_path='', appoint_number=''):
    start_time = time.time()
    website_name = 'cableav'
    req_web += '-> %s' % website_name
    title = ''
    cover_url = ''
    web_info = '\n       '
    log_info += ' \n    🌐 cableav'
    debug_info = ''
    real_url = appoint_url
    cableav_url = getattr(config, 'cableav_website', 'https://cableav.tv')

    try:
        if not real_url:
            # 处理番号
            number_list, filename_list = get_number_list(number, appoint_number, file_path)
            n_list = number_list[:1] + filename_list
            for each in n_list:
                real_url = f'{cableav_url}/?s={each}'
                # real_url = 'https://cableav.tv/s?s=%E6%9F%9A%E5%AD%90%E7%8C%AB'
                debug_info = f'请求地址: {real_url} '
                log_info += web_info + debug_info
                result, response = curl_html(real_url)
                if not result:
                    debug_info = '网络请求错误: %s' % response
                    log_info += web_info + debug_info
                    raise Exception(debug_info)
                search_page = etree.fromstring(response, etree.HTMLParser())
                result, number, title, real_url = get_real_url(search_page, n_list)
                # real_url = 'https://cableav.tv/hyfaqwfjhio'
                if result:
                    break
            else:
                debug_info = '没有匹配的搜索结果'
                log_info += web_info + debug_info
                raise Exception(debug_info)

        debug_info = f'番号地址: {real_url} '
        log_info += web_info + debug_info
        result, response = curl_html(real_url)

        if not result:
            debug_info = '没有找到数据 %s ' % response
            log_info += web_info + debug_info
            raise Exception(debug_info)

        detail_page = etree.fromstring(response, etree.HTMLParser())
        number, title, actor, cover_url, tag = get_detail_info(detail_page, number, file_path)
        actor_photo = get_actor_photo(actor)

        try:
            dic = {
                'number': number,
                'title': title,
                'originaltitle': title,
                'actor': actor,
                'outline': '',
                'originalplot': '',
                'tag': tag,
                'release': '',
                'year': '',
                'runtime': '',
                'score': '',
                'series': '',
                'country': 'CN',
                'director': '',
                'studio': '',
                'publisher': '',
                'source': 'cableav',
                'website': real_url,
                'actor_photo': actor_photo,
                'cover': cover_url,
                'poster': '',
                'extrafanart': '',
                'trailer': '',
                'image_download': False,
                'image_cut': 'no',
                'log_info': log_info,
                'error_info': '',
                'req_web': req_web + '(%ss) ' % (round((time.time() - start_time), )),
                'mosaic': '国产',
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
    js = json.dumps(dic, ensure_ascii=False, sort_keys=False, indent=4, separators=(',', ': '), )
    return js


if __name__ == '__main__':
    # yapf: disable
    # print(main('SSN010'))
    # print(main('國產AV 麻豆傳媒 MD0312 清純嫩穴賣身葬父 露露', file_path='國產AV 麻豆傳媒 MD0312 清純嫩穴賣身葬父 露露'))
    # print(main('國產AV 大象傳媒 DA002 性感魅惑色兔兔 李娜娜', file_path='國產AV 大象傳媒 DA002 性感魅惑色兔兔 李娜娜'))
    # print(main('韓國高端攝影頂 Yeha 私拍福利', file_path='韓國高端攝影頂 Yeha 私拍福利'))
    print(main('EMTC-005', file_path='國產AV 愛神傳媒 EMTC005 怒操高冷社長秘書 米歐'))
