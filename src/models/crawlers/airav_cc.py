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

#2024年7月7日16:43:00，页面改版后xpath重新定位
# import traceback


def get_web_number(html):
    # result = html.xpath('//p/span[contains(text(), "番號") or contains(text(), "番号")]/following-sibling::span/text()')
    result = html.xpath('//li[contains(text(), "番號") or contains(text(), "番号")]/span/text()')#更新
    return result[0].strip() if result else ''


def get_number(html, number):
    # result = html.xpath('//p/span[contains(text(), "番號") or contains(text(), "番号")]/following-sibling::span/text()')
    result = html.xpath('//li[contains(text(), "番號") or contains(text(), "番号")]/span/text()')#更新
    num = result[0].strip() if result else ''
    return number if number else num


def get_title(html):
    # result = html.xpath('//li[@class="vediotitle"]/h1/span/text()')
    result = html.xpath('//div[@class="video-title my-3"]/h1/text()')#更新
    return result[0].strip() if result else ''

def get_actor(html):
    try:
        # actor_list = html.xpath('//li[@class="allavgirls"]//a/text()')
        actor_list = html.xpath('//li[contains(text(), "女優") or contains(text(), "女优")]/a/text()')#更新
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
    # result = html.xpath('//li[@class="series"]//a/text()')
    result = html.xpath('//li[contains(text(), "厂商") or contains(text(), "廠商")]/a/text()')#更新
    return result[0] if result else ''

def get_series(html):#获取系列，更新
    result = html.xpath('//li[contains(text(), "系列")]/a/text()')#更新
    print('获取到的系列为：\n',result)
    return result[0] if result else ''#更新

def get_release(html):
    # result = html.xpath('//span[@itemprop="datePublished"]/text()')
    result = html.xpath('//div[@class="video-item"]/div[1]/text()')#更新发行日期
    # if result:
    #     s = re.search(r'\d{4}-\d{2}-\d{2}', result[0]).group()
    #     return s if s else ''
    # return ''
    return result[0].split(" ",1)[0].strip() if result else ''#更新


def get_year(release):
    try:
        result = str(re.search(r'\d{4}', release).group())
        return result
    except:
        return release


def get_tag(html):
    # result = html.xpath('//li[@class="keyword"]//a/text()')
    result = html.xpath('//li[contains(text(), "標籤") or contains(text(), "标籤")]/a/text()')#更新
    return ','.join(result) if result else ''


def get_cover(html):
    # result = html.xpath('//div[@class="front-video-cover-img"]//img/@src')
    result = html.xpath('(//link[@rel="alternate"])[1]/@href')#更新
    # return result[0] if result else ''
    return '/storage/cover/big/'+result[0].split("=",1)[1]+'.jpg' if result else ''#更新



def get_outline(html):
    # result = html.xpath('//span[@itemprop="description"]/text()')
    result = html.xpath('//div[@class="video-info"]/p/text()')#更新
    if result:#更新
        index = result[0].find('*根')#更新,去掉简介中“*根据分发方式XXX”后面的内容
        if index !=-1:#更新
            return result[0][:index].strip()#更新
        else:#更新
            return result[0].strip()#更新
    else:#更新
        return ''#更新
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
    series = get_series(html_info)#获取系列，更新
    
    # return html_info, title, outline, actor, cover_url, tag, studio, log_info
    return html_info, title, outline, actor, cover_url, tag, studio, series,log_info#更新


def main(number, appoint_url='', log_info='', req_web='', language='zh_cn'):
    start_time = time.time()
    website_name = 'airav_cc'
    req_web += f'-> {website_name}[{language}]'
    number = number.upper()
    if re.match(r'N\d{4}', number):  # n1403
        number = number.lower()
    real_url = appoint_url
    cover_url = ''
    image_cut = 'right'
    image_download = False
    url_search = ''
    mosaic = '有码'
    airav_url = getattr(config, 'airav_cc_website', 'https://airav.io')
    if language == 'zh_cn':
        airav_url += '/cn'
    web_info = '\n       '
    log_info += f' \n    🌐 airav[{language.replace("zh_", "")}]'
    debug_info = ''

    # real_url = 'https://airav5.fun/jp/playon.aspx?hid=44733'

    try:  # 捕获主动抛出的异常
        if not real_url:#未指定url

            # 通过搜索获取real_url https://airav5.fun/cn/searchresults.aspx?Search=ssis-200&Type=0
            # url_search = airav_url + f'/searchresults.aspx?Search={number}&Type=0'
            url_search = airav_url + f'/search_result?kw=+{number}'#更新
            debug_info = '搜索地址: %s ' % url_search
            log_info += web_info + debug_info

            # ========================================================================搜索番号
            result, html_search = curl_html(url_search)
            if not result:
                debug_info = '网络请求错误: %s ' % html_search
                log_info += web_info + debug_info
                raise Exception(debug_info)
            html = etree.fromstring(html_search, etree.HTMLParser())
            # number2 = ' ' + number.upper()
            number2 =  number.upper()#更新
            # real_url = html.xpath(
            #     "//h3[@class='one_name ga_name' and contains(text(), $number1) and not(contains(text(), '克破'))]/../@href",
            #     number1=number2)
            h5_elements = html.xpath("//h5[contains(text(), {})]".format(repr(number2.strip())))
            filtered_h5_elements = [h5 for h5 in h5_elements if '克破' not in h5.text]
            hrefs = []  
            for h5 in filtered_h5_elements:
                preceding_divs = h5.xpath("../preceding-sibling::div[1]") 
                if preceding_divs:   
                    a_href = preceding_divs[0].xpath("a/@href")  
                    if a_href:  
                        hrefs.append(a_href[0]) 
            real_url = hrefs

            # if real_url:
            #     real_url = airav_url + '/' + real_url[0]
            # else:
            if not real_url:
                debug_info = '搜索结果: 未匹配到番号！'
                log_info += web_info + debug_info
                raise Exception(debug_info)

        if real_url:
            if isinstance(real_url, list) and real_url:
                # real_url = real_url[0]
                real_url = 'https://airav.io' + real_url[-1]#更新
            debug_info = '番号地址: %s ' % real_url
            log_info += web_info + debug_info
            for i in range(3):
                # html_info, title, outline, actor, cover_url, tag, studio, log_info = (
                html_info, title, outline, actor, cover_url, tag, studio, series,log_info = (#更新
                    retry_request(real_url, log_info, web_info))

                if cover_url.startswith("/"):  # coverurl 可能是相对路径
                    cover_url = urllib.parse.urljoin(airav_url, cover_url)

                # temp_str = title + outline + actor + tag + studio
                temp_str = title + outline + actor + tag + studio +series#更新
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
            # series = ''
            series = get_series(html_info)#更新
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
                    # 'poster': cover_url.replace('big_pic', 'small_pic'),
                    'poster': cover_url.replace('big', 'small'),#更新
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
    )  # .encode('UTF-8')
    return js


if __name__ == '__main__':
    # yapf: disable
    print(main('', 'https://airav.io/playon.aspx?hid=99-21-46640'))
    # print(main('PRED-300'))    # 马赛克破坏版
    # print(main('snis-036', language='jp'))
    # print(main('snis-036'))
    # print(main('IESP-611'))
    # print(main('MIAE-346'))
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
