#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import time
import urllib.parse

import urllib3
from lxml import etree

from models.base.web import curl_html
from models.config import config
from models.signals import signal

urllib3.disable_warnings()  # yapf: disable


# import traceback


def get_web_number(html):
    result = html.xpath('//*[contains(text(), "番號") or contains(text(), "番号")]//span/text()')
    return result[0].strip() if result else ''


def get_number(html, number):
    result = html.xpath('//*[contains(text(), "番號") or contains(text(), "番号")]//span/text()')
    num = result[0].strip() if result else ''
    return number if number else num


def get_title(html):
    result = html.xpath('//div[@class="video-title my-3"]/h1/text()')
    result = str(result[0]).strip() if result else ''
    # 去掉无意义的简介(马赛克破坏版)，'克破'两字简繁同形
    if not result or '克破' in result:
        return ''
    return result


def get_actor(html):
    try:
        actor_list = html.xpath('//*[contains(text(), "女優") or contains(text(), "女优")]//a/text()')
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
    result = html.xpath('//*[contains(text(), "廠商") or contains(text(), "厂商")]//a/text()')
    return result[0] if result else ''


def get_release(html):
    result = html.xpath('//i[@class="fa fa-clock me-2"]/../text()')
    if result:
        s = re.search(r'\d{4}-\d{2}-\d{2}', result[0]).group()
        return s if s else ''
    return ''


def get_year(release):
    try:
        result = str(re.search(r'\d{4}', release).group())
        return result
    except:
        return release


def get_tag(html):
    result = html.xpath('//*[contains(text(), "標籤") or contains(text(), "标籤")]//a/text()')
    return ','.join(result) if result else ''


def get_cover(html):
    result = html.xpath('//script[@type="application/ld+json"]/text()')[0]
    if result:
        data_dict = json.loads(result)
        result = data_dict.get("thumbnailUrl", "")[0]
    return result if result else ''


def get_outline(html):
    result = html.xpath('//div[@class="video-info"]/p/text()')
    result = str(result[0]).strip() if result else ''
    # 去掉无意义的简介(马赛克破坏版)，'克破'两字简繁同形
    if not result or '克破' in result:
        return ''
    else:
        # 去除简介中的无意义信息，中间和首尾的空白字符、*根据分发等
        result = re.sub(r'[\n\t]', '', result).split('*根据分发', 1)[0].strip()
    return result


def get_series(html):
    result = html.xpath('//*[contains(text(), "系列")]//a/text()')
    result = result[0] if result else ''
    return result


def retry_request(real_url, log_info, web_info):
    result, html_content = curl_html(real_url)
    if not result:
        debug_info = f'网络请求错误: {html_content} '
        log_info += web_info + debug_info
        raise Exception(debug_info)
    html_info = etree.fromstring(html_content, etree.HTMLParser())
    title = get_title(html_info)  # 获取标题
    if not title:
        debug_info = '数据获取失败: 未获取到title！'
        log_info += web_info + debug_info
        raise Exception(debug_info)
    web_number = get_web_number(html_info)  # 获取番号，用来替换标题里的番号
    web_number1 = f'[{web_number}]'
    title = title.replace(web_number1, '').strip()
    outline = get_outline(html_info)
    actor = get_actor(html_info)  # 获取actor
    cover_url = get_cover(html_info)  # 获取cover
    tag = get_tag(html_info)
    studio = get_studio(html_info)
    return html_info, title, outline, actor, cover_url, tag, studio, log_info


def get_real_url(html, number):
    item_list = html.xpath('//div[@class="col oneVideo"]')
    for each in item_list:
        # href="/video?hid=99-21-39624"
        detail_url = each.xpath('.//a/@href')[0]
        title = each.xpath('.//h5/text()')[0]
        # 注意去除马赛克破坏版这种几乎没有有效字段的条目
        if number.upper() in title and all(keyword not in title for keyword in ['克破', '无码破解', '無碼破解']):
            return detail_url
    return ''


def main(number, appoint_url='', log_info='', req_web='', language='zh_cn'):
    start_time = time.time()
    website_name = 'airav_cc'
    req_web += f'-> {website_name}[{language}]'
    number = number.upper()
    if re.match(r'N\d{4}', number):  # n1403
        number = number.lower()
    real_url = appoint_url
    image_cut = 'right'
    image_download = False
    mosaic = '有码'
    airav_url = getattr(config, 'airav_cc_website', 'https://airav.io')
    if language == 'zh_cn':
        airav_url += '/cn'
    web_info = '\n       '
    log_info += f' \n    🌐 airav[{language.replace("zh_", "")}]'

    # real_url = 'https://airav5.fun/jp/playon.aspx?hid=44733'

    try:  # 捕获主动抛出的异常
        if not real_url:

            # 通过搜索获取real_url https://airav.io/search_result?kw=ssis-200
            url_search = airav_url + f'/search_result?kw={number}'
            debug_info = f'搜索地址: {url_search} '
            log_info += web_info + debug_info

            # ========================================================================搜索番号
            result, html_search = curl_html(url_search)
            if not result:
                debug_info = f'网络请求错误: {html_search} '
                log_info += web_info + debug_info
                raise Exception(debug_info)
            html = etree.fromstring(html_search, etree.HTMLParser())
            real_url = html.xpath('//div[@class="col oneVideo"]//a[@href]/@href')
            # if real_url:
            #     real_url = airav_url + '/' + real_url[0]
            # else:
            # 没有搜索结果
            if not real_url:
                debug_info = '搜索结果: 未匹配到番号！'
                log_info += web_info + debug_info
                raise Exception(debug_info)

        if real_url:
            # 只有一个搜索结果时直接取值 多个则进入判断
            real_url = real_url[0] if len(real_url) == 1 else get_real_url(html, number)
            # 搜索结果页面有条目，但无法匹配到番号
            if not real_url:
                debug_info = '搜索结果: 未匹配到番号！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            else:
                real_url = urllib.parse.urljoin(airav_url, real_url) if real_url.startswith("/") else real_url

            debug_info = f'番号地址: {real_url} '
            log_info += web_info + debug_info
            for i in range(3):
                html_info, title, outline, actor, cover_url, tag, studio, log_info = (retry_request(real_url, log_info, web_info))

                if cover_url.startswith("/"):  # coverurl 可能是相对路径
                    cover_url = urllib.parse.urljoin(airav_url, cover_url)

                temp_str = title + outline + actor + tag + studio
                if '�' not in temp_str:
                    break
                else:
                    debug_info = f'{number} 请求 airav_cc 返回内容存在乱码 �，尝试第 {(i + 1)}/3 次请求'
                    signal.add_log(debug_info)
                    log_info += web_info + debug_info
            else:
                debug_info = f'{number} 已请求三次，返回内容仍存在乱码 � ！视为失败！'
                signal.add_log(debug_info)
                log_info += web_info + debug_info
                raise Exception(debug_info)
            actor_photo = get_actor_photo(actor)
            number = get_number(html_info, number)
            release = get_release(html_info)
            year = get_year(release)
            runtime = ''
            score = ''
            series = get_series(html_info)
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
        # print(traceback.format_exc())
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
    # print(main('', 'https://airav.io/playon.aspx?hid=99-21-46640'))
    # print(main('PRED-300'))    # 马赛克破坏版
    # print(main('snis-036', language='jp'))
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
    # print(main('ssis-200', ''))     # 多个搜索结果
    # print(main('JUY-331', ''))      # 存在系列字段
    # print(main('SONE-248', ''))      # 简介存在无效信息  "*根据分发方式,内容可能会有所不同"
    print('CAWD-688', '')  # 无码破解
