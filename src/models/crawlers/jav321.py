#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import time  # yapf: disable # NOQA: E402

import urllib3
from lxml import etree

from models.base.web import post_html

urllib3.disable_warnings()  # yapf: disable


# import Function.config as cf
# import traceback


def getActorPhoto(actor):
    actor = actor.split(',')
    data = {}
    for i in actor:
        actor_photo = {i: ''}
        data.update(actor_photo)
    return data


def getTitle(response):
    return str(re.findall(r'<h3>(.+) <small>', response)).strip(" ['']")


def getActor(response):
    if re.search(r'<a href="/star/\S+">(\S+)</a> &nbsp;', response):
        return str(re.findall(r'<a href="/star/\S+">(\S+)</a> &nbsp;', response)).strip(" [',']").replace('\'', '')
    elif re.search(r'<a href="/heyzo_star/\S+">(\S+)</a> &nbsp;', response):
        return str(re.findall(r'<a href="/heyzo_star/\S+">(\S+)</a> &nbsp;', response)).strip(" [',']").replace('\'', '')
    else:
        return str(re.findall(r'<b>出演者</b>: ([^<]+) &nbsp; <br>', response)).strip(" [',']").replace('\'', '')


def getStudio(html):
    result = str(html.xpath('//div[@class="col-md-9"]/a[contains(@href,"/company/")]/text()')).strip(" ['']")
    return result


def getRuntime(response):
    return str(re.findall(r'<b>収録時間</b>: (\d+) \S+<br>', response)).strip(" ['']")


def getSeries(html):
    result = str(html.xpath('//div[@class="col-md-9"]/a[contains(@href,"/series/")]/text()')).strip(" ['']")
    return result


def getWebsite(detail_page):
    return 'https:' + detail_page.xpath('//a[contains(text(),"简体中文")]/@href')[0]


def getNum(response, number):
    result = re.findall(r'<b>品番</b>: (\S+)<br>', response)
    return result[0].strip().upper() if result else number


def getScore(response):
    if re.search(r'<b>平均評価</b>: <img data-original="/img/(\d+).gif" />', response):
        score = re.findall(r'<b>平均評価</b>: <img data-original="/img/(\d+).gif" />', response)[0]
        return str(float(score) / 10.0)
    else:
        return str(re.findall(r'<b>平均評価</b>: ([^<]+)<br>', response)).strip(" [',']").replace('\'', '')


def getYear(release):
    try:
        result = str(re.search(r'\d{4}', release).group())
        return result
    except:
        return release


def getRelease(response):
    return str(re.findall(r'<b>配信開始日</b>: (\d+-\d+-\d+)<br>', response)).strip(" ['']").replace('0000-00-00', '')


def getCover(detail_page):
    cover_url = str(detail_page.xpath("/html/body/div[@class='row'][2]/div[@class='col-md-3']/div[@class='col-xs-12 " "col-md-12'][1]/p/a/img[@class='img-responsive']/@src")).strip(
        " ['']")
    if cover_url == '':
        cover_url = str(detail_page.xpath("//*[@id='vjs_sample_player']/@poster")).strip(" ['']")
    return cover_url


def getExtraFanart(htmlcode):
    extrafanart_list = htmlcode.xpath("/html/body/div[@class='row'][2]/div[@class='col-md-3']/div[@class='col-xs-12 col-md-12']/p/a/img[@class='img-responsive']/@src")
    return extrafanart_list


def getCoverSmall(detail_page):
    return str(detail_page.xpath('//img[@class="img-responsive"]/@src')[0])


def getTag(response):  # 获取演员
    return re.findall(r'<a href="/genre/\S+">(\S+)</a>', response)


def getOutline(detail_page):
    # 修复路径，避免简介含有垃圾信息 "*根据分发方式，内容可能会有所不同”
    return detail_page.xpath("string(/html/body/div[2]/div[1]/div[1]/div[2]/div[3]/div/text())")


def main(number, appoint_url='', log_info='', req_web='', language='jp'):
    start_time = time.time()
    website_name = 'jav321'
    req_web += '-> %s' % website_name
    title = ''
    cover_url = ''
    poster_url = ''
    image_download = False
    image_cut = 'right'
    mosaic = '有码'
    web_info = '\n       '
    log_info += ' \n    🌐 jav321'
    debug_info = ''

    try:
        result_url = "https://www.jav321.com/search"
        if appoint_url != '':
            result_url = appoint_url
            debug_info = '番号地址: %s' % result_url
            log_info += web_info + debug_info
        else:
            debug_info = '搜索地址: %s {"sn": %s}' % (result_url, number)
            log_info += web_info + debug_info
        result, response = post_html(result_url, data={"sn": number})
        if not result:
            debug_info = '网络请求错误: %s' % response
            log_info += web_info + debug_info
            raise Exception(debug_info)
        if 'AVが見つかりませんでした' in response:
            debug_info = '搜索结果: 未匹配到番号！'
            log_info += web_info + debug_info
            raise Exception(debug_info)
        detail_page = etree.fromstring(response, etree.HTMLParser())
        website = getWebsite(detail_page)
        if website:
            debug_info = '番号地址: %s ' % website
            log_info += web_info + debug_info
        actor = getActor(response)
        actor_photo = getActorPhoto(actor)
        title = getTitle(response).strip()  # 获取标题
        if not title:
            debug_info = '数据获取失败: 未获取到标题！'
            log_info += web_info + debug_info
            raise Exception(debug_info)
        cover_url = getCover(detail_page)  # 获取cover
        poster_url = getCoverSmall(detail_page)
        if not cover_url:
            cover_url = poster_url
        release = getRelease(response)
        year = getYear(release)
        runtime = getRuntime(response)
        number = getNum(response, number)
        outline = getOutline(detail_page)
        tag = getTag(response)
        score = getScore(response)
        studio = getStudio(detail_page)
        series = getSeries(detail_page)
        extrafanart = getExtraFanart(detail_page)
        # 判断无码
        uncensorted_list = ['一本道', 'HEYZO', 'サムライポルノ', 'キャットウォーク', 'サイクロン', 'ルチャリブレ', 'スーパーモデルメディア', 'スタジオテリヤキ',
                            'レッドホットコレクション', 'スカイハイエンターテインメント', '小天狗', 'オリエンタルドリーム', 'Climax Zipang', 'CATCHEYE', 'ファイブスター',
                            'アジアンアイズ', 'ゴリラ', 'ラフォーレ ガール', 'MIKADO', 'ムゲンエンターテインメント', 'ツバキハウス', 'ザーメン二郎', 'トラトラトラ',
                            'メルシーボークー', '神風', 'Queen 8', 'SASUKE', 'ファンタドリーム', 'マツエンターテインメント', 'ピンクパンチャー', 'ワンピース',
                            'ゴールデンドラゴン', 'Tokyo Hot', 'Caribbean']
        for each in uncensorted_list:
            if each == studio:
                mosaic = '无码'
                break
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
                'director': '',
                'studio': studio,
                'publisher': studio,
                'source': 'jav321',
                'website': website,
                'actor_photo': actor_photo,
                'cover': cover_url,
                'poster': poster_url,
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
    dic = {website_name: {'zh_cn': dic, 'zh_tw': dic, 'jp': dic}}
    js = json.dumps(dic, ensure_ascii=False, sort_keys=False, indent=4, separators=(',', ': '), )  # .encode('UTF-8')
    return js


if __name__ == '__main__':
    # print(main('blk-495'))
    # print(main('hkgl-004'))
    # print(main('snis-333'))
    # print(main('GERK-326'))
    # print(main('msfh-010'))
    # print(main('msfh-010'))
    # print(main('kavr-065'))
    # print(main('ssni-645'))
    # print(main('sivr-038'))
    # print(main('ara-415'))
    # print(main('luxu-1257'))
    # print(main('heyzo-1031'))
    # print(main('ABP-905'))
    # print(main('heyzo-1031', ''))
    # print(main('ymdd-173', 'https://www.jav321.com/video/ymdd00173'))
    print(main('MIST-409'))
