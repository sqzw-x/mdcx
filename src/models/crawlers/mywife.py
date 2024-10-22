#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import time

import urllib3
from lxml import etree

from models.base.web import check_url, get_html

urllib3.disable_warnings()  # yapf: disable
# import traceback

seesaawiki_request_fail_flag = False


def get_title(html):
    result = html.xpath('//head/title/text()')
    if result:
        number, title = re.findall(r'(No\.\d*)(.*)', result[0])[0]
        return number, title.strip()
    return '', ''


def get_first_url(html, key):
    result = html.xpath('//h2[@class="heading heading-secondary"]/a/@href')
    temp_key = f'no{key}'
    for each in result:
        if temp_key in each:
            return each
    return ''


def get_second_url(html):
    result = html.xpath('//a[@class="wp-block-button__link has-luminous-vivid-amber-to-luminous-vivid-orange-gradient-background has-background"]/@href')
    return result[0] if result else ''


def get_actor_photo(actor):
    actor = actor.split(',')
    data = {}
    for i in actor:
        actor_photo = {i: ''}
        data.update(actor_photo)
    return data


def get_cover(html):
    result = html.xpath('//video[@id="video"]')
    if result:
        cover_url = result[0].get('poster')
        if not cover_url.startswith('http'):
            cover_url = 'https:' + cover_url
        trailer = result[0].get('src')
        return cover_url, trailer
    return '', ''


def get_outline(html):
    result = html.xpath('normalize-space(string(//div[@class="modelsamplephototop"]))')
    return result.strip()


def get_actor(html):
    result = html.xpath('//div[@class="modelwaku0"]/img/@alt')
    return result[0] if result else ''


def get_extrafanart(html):
    result = html.xpath("//div[@class='modelsample_photowaku']/img/@src")
    return result


def get_wiki_data():
    url = 'https://seesaawiki.jp/av_neme/d/%C9%F1%A5%EF%A5%A4%A5%D5'
    result, html_search = get_html(url, encoding='euc-jp')
    if not result:
        return False
    try:
        html = etree.fromstring(html_search, etree.HTMLParser())
        mywife_data = html.xpath("//div[@class='wiki-section-3']")
        mywife_dic = {}
        for each in mywife_data:
            number_id = each.xpath("div/h5/text()")
            if not number_id or 'No.' not in number_id[0]:
                continue
            number_id = number_id[0].replace('No.', '').strip()
            href = each.xpath("div[@class='wiki-section-body-3']/a/@href")
            if not href or len(href) < 2:
                continue
            poster, website = href[0], href[1]
            actor = each.xpath("div[@class='wiki-section-body-3']/span/a/text()")
            if not actor:
                actor = each.xpath("div[@class='wiki-section-body-3']/a[@rel='nofollow']/text()")
            if actor:
                actor = actor[0]
            mywife_dic[number_id] = {'number': number_id, 'actor': actor, 'poster': poster, 'website': website, }
        return mywife_dic
    except:
        # print(traceback.format_exc())
        return False


def get_number_data(number):
    global seesaawiki_request_fail_flag
    data = {}
    try:
        mywife_data = data['mywife']
    except:
        mywife_data = get_wiki_data()
        if not mywife_data:
            seesaawiki_request_fail_flag = True
            return False
        data['mywife'] = mywife_data
    return mywife_data.get(str(number))


def main(number, appoint_url='', log_info='', req_web='', language='jp'):
    global seesaawiki_request_fail_flag
    try:  # 捕获主动抛出的异常
        start_time = time.time()
        website_name = 'mywife'
        req_web += '-> %s' % website_name
        real_url = appoint_url
        cover_url = ''
        image_cut = ''
        image_download = True
        web_info = '\n       '
        log_info += ' \n    🌐 mywife'
        debug_info = ''
        key = re.findall(r'NO\.(\d*)', number.upper())
        key = key[0] if key else ''
        if not key:
            key = re.findall(r'\d{3,}', number)
            if key:
                key = key[0]
                if int(key) >= 1450:
                    real_url = f'https://mywife.cc/teigaku/model/no/{key}'
        if not key:
            debug_info = f'番号中未识别到三位及以上数字: {number} '
            log_info += web_info + debug_info
            raise Exception(debug_info)
        actor = ''
        poster = ''
        req_wiki_data = False

        if not real_url:
            req_wiki_data = True
            debug_info = '请求 seesaawiki.jp 数据... '
            log_info += web_info + debug_info

            number_data = get_number_data(key)
            if number_data:
                number = number_data['number']
                actor = number_data['actor']
                poster = number_data['poster']
                real_url = number_data['website']
                if 'mywife.cc' not in real_url:
                    web_url = check_url(real_url, real_url=True)
                    real_url = re.sub(r'\?.*$', '', web_url) if web_url else ''

        if not real_url:
            if not number_data:
                debug_info = 'seesaawiki.jp 暂未收录该番号！当前尝试使用官网搜索查询...'
                if seesaawiki_request_fail_flag:
                    debug_info = 'seesaawiki.jp 获取数据失败！无法获取真实演员名字！建议更换代理！当前尝试使用官网搜索查询...'
            else:
                debug_info = 'track.bannerbridge.net 无法访问！无法快速获取官网详情页地址！建议更换代理！当前尝试使用官网搜索查询...'
            log_info += web_info + debug_info

            url_search = f'https://mywife.jp/?s={key}'
            debug_info = f'搜索页地址: {url_search} '
            log_info += web_info + debug_info

            result, html_content = get_html(url_search)
            if not result:
                debug_info = f'网络请求错误: {html_content} '
                log_info += web_info + debug_info
                raise Exception(debug_info)
            html_info = etree.fromstring(html_content, etree.HTMLParser())
            first_url = get_first_url(html_info, key)

            if first_url:
                debug_info = f'中间页地址: {first_url} '
                log_info += web_info + debug_info

                result, html_content = get_html(first_url)
                if not result:
                    debug_info = f'网络请求错误: {html_content} '
                    log_info += web_info + debug_info
                    raise Exception(debug_info)
                html_info = etree.fromstring(html_content, etree.HTMLParser())
                real_url = get_second_url(html_info)
                if not real_url:
                    debug_info = f'中间页未获取到详情页地址！ {first_url} '
                    log_info += web_info + debug_info
                    raise Exception(debug_info)
            else:
                debug_info = f'搜索页未获取到匹配数据！ {url_search} '
                log_info += web_info + debug_info

                debug_info = '尝试拼接番号地址'
                log_info += web_info + debug_info
                real_url = f'https://mywife.cc/teigaku/model/no/{key}'

        if real_url:
            debug_info = f'番号地址: {real_url} '
            log_info += web_info + debug_info

            result, html_content = get_html(real_url)
            if not result:
                debug_info = f'网络请求错误: {html_content} '
                log_info += web_info + debug_info
                raise Exception(debug_info)
            html_info = etree.fromstring(html_content, etree.HTMLParser())
            number, title = get_title(html_info)
            if not title:
                debug_info = '数据获取失败: 未获取到title！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            outline = get_outline(html_info)
            if not actor:
                actor = get_actor(html_info)
            actor_photo = get_actor_photo(actor)
            cover_url, trailer = get_cover(html_info)
            if not poster:
                poster = cover_url.replace('topview.jpg', 'thumb.jpg')
            extrafanart = get_extrafanart(html_info)
            studio = '舞ワイフ'
            release = ''
            year = ''
            runtime = ''
            score = ''
            series = ''
            director = ''
            publisher = '舞ワイフ'
            mosaic = '有码'
            if not req_wiki_data:
                debug_info = '请求 seesaawiki.jp 获取真实演员... '
                log_info += web_info + debug_info

                key = number.replace('No.', '')
                number_data = get_number_data(key)
                if number_data:
                    actor = number_data['actor']
                    poster = number_data['poster']
                    actor_photo = get_actor_photo(actor)

            try:
                dic = {
                    'number': f'Mywife {number}',
                    'title': title,
                    'originaltitle': title,
                    'actor': actor,
                    'outline': outline,
                    'originalplot': outline,
                    'tag': '',
                    'release': release,
                    'year': year,
                    'runtime': runtime,
                    'score': score,
                    'series': series,
                    'director': director,
                    'studio': studio,
                    'publisher': publisher,
                    'source': 'mywife',
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
    # print(main('mywife No.776', 'https://mywife.cc/teigaku/model/no/1303'))
    # print(main('mywife 171'))           # 都无数据
    # print(main('mywife No.1005'))     # 官网搜不到， seesaawiki 有数据
    # print(main('mywife-1525'))    # 无 No.
    # print(main('mywife-1578'))    # 无 No.
    # print(main('mywife-1370'))    # 无 No.
    print(main('mywife-1307'))  # 无 No.  # print(main('mywife-1161'))      # 无 No. 其实是 No  # print(main('mywife No.1161'))  # print(main('mywife No.1164'))  # print(main('mywife No.1167'))  # print(main('mywife No.1171'))  # print(main('mywife No.1229'))
