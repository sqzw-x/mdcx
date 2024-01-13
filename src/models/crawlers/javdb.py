#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import random
import re
import time  # yapf: disable # NOQA: E402

import urllib3
from lxml import etree

from models.base.web import curl_html, get_dmm_trailer
from models.config.config import config

urllib3.disable_warnings()  # yapf: disable
# import traceback

sleep = True


def get_number(html, number):
    result = html.xpath('//a[@class="button is-white copy-to-clipboard"]/@data-clipboard-text')
    if result:
        result = result[0]
    else:
        result = number
    return result


def get_title(html, org_language):
    title = html.xpath('string(//h2[@class="title is-4"]/strong[@class="current-title"])')
    originaltitle = html.xpath('string(//h2[@class="title is-4"]/span[@class="origin-title"])')
    if originaltitle:
        if org_language == 'jp':
            title = originaltitle
    else:
        originaltitle = title
    return title.strip(), originaltitle.strip()


def get_actor(html):
    actor_result = html.xpath(
        '//div[@class="panel-block"]/strong[contains(text(), "演員:") or contains(text(), "Actor(s):")]/../span[@class="value"]/a/text()')
    gender_result = html.xpath(
        '//div[@class="panel-block"]/strong[contains(text(), "演員:") or contains(text(), "Actor(s):")]/../span[@class="value"]/strong/@class')
    i = 0
    actor_list = []
    for gender in gender_result:
        if gender == 'symbol female':
            actor_list.append(actor_result[i])
        i += 1
    return ','.join(actor_list), ','.join(actor_result)


def get_actor_photo(actor):
    actor = actor.split(',')
    data = {}
    for i in actor:
        actor_photo = {i: ''}
        data.update(actor_photo)
    return data


def get_studio(html):
    result1 = str(html.xpath('//strong[contains(text(),"片商:")]/../span/a/text()')).strip(" ['']")
    result2 = str(html.xpath('//strong[contains(text(),"Maker:")]/../span/a/text()')).strip(" ['']")
    return str(result1 + result2).strip('+').replace("', '", '').replace('"', '')


def get_publisher(html):
    result1 = str(html.xpath('//strong[contains(text(),"發行:")]/../span/a/text()')).strip(" ['']")
    result2 = str(html.xpath('//strong[contains(text(),"Publisher:")]/../span/a/text()')).strip(" ['']")
    return str(result1 + result2).strip('+').replace("', '", '').replace('"', '')


def get_runtime(html):
    result1 = str(html.xpath('//strong[contains(text(),"時長")]/../span/text()')).strip(" ['']")
    result2 = str(html.xpath('//strong[contains(text(),"Duration:")]/../span/text()')).strip(" ['']")
    return str(result1 + result2).replace(' 分鍾', '').replace(' minute(s)', '')


def get_series(html):
    result1 = str(html.xpath('//strong[contains(text(),"系列:")]/../span/a/text()')).strip(" ['']")
    result2 = str(html.xpath('//strong[contains(text(),"Series:")]/../span/a/text()')).strip(" ['']")
    return str(result1 + result2).strip('+').replace("', '", '').replace('"', '')


def get_release(html):
    result1 = str(html.xpath('//strong[contains(text(),"日期:")]/../span/text()')).strip(" ['']")
    result2 = str(html.xpath('//strong[contains(text(),"Released Date:")]/../span/text()')).strip(" ['']")
    return str(result1 + result2).strip('+')


def get_year(get_release):
    try:
        result = str(re.search(r'\d{4}', get_release).group())
        return result
    except:
        return get_release


def get_tag(html):
    result1 = str(html.xpath('//strong[contains(text(),"類別:")]/../span/a/text()')).strip(" ['']")
    result2 = str(html.xpath('//strong[contains(text(),"Tags:")]/../span/a/text()')).strip(" ['']")
    return str(result1 + result2).strip('+').replace(",\\xa0", "").replace("'", "").replace(' ', '').replace(',,',
                                                                                                             '').lstrip(
        ',')


def get_cover(html):
    try:
        result = str(html.xpath("//img[@class='video-cover']/@src")[0]).strip(" ['']")
    except:
        result = ''
    return result


def get_extrafanart(html):  # 获取封面链接
    extrafanart_list = html.xpath("//div[@class='tile-images preview-images']/a[@class='tile-item']/@href")
    return extrafanart_list


def get_trailer(html):  # 获取预览片
    trailer_url_list = html.xpath("//video[@id='preview-video']/source/@src")
    return get_dmm_trailer(trailer_url_list[0]) if trailer_url_list else ''


def get_director(html):
    result1 = str(html.xpath('//strong[contains(text(),"導演:")]/../span/a/text()')).strip(" ['']")
    result2 = str(html.xpath('//strong[contains(text(),"Director:")]/../span/a/text()')).strip(" ['']")
    return str(result1 + result2).strip('+').replace("', '", '').replace('"', '')


def get_score(html):
    result = str(html.xpath("//span[@class='score-stars']/../text()")).strip(" ['']")
    try:
        score = re.findall(r'(\d{1}\..+)分', result)
        if score:
            score = score[0]
        else:
            score = ''
    except:
        score = ''
    return score


def get_mosaic(title):
    if '無碼' in title or '無修正' in title or 'Uncensored' in title:
        mosaic = '无码'
    else:
        mosaic = ''
    return mosaic


def get_real_url(html, number):  # 获取详情页链接
    res_list = html.xpath("//a[@class='box']")
    info_list = []
    if '.' in number:
        old_date = re.findall(r'\D+(\d{2}\.\d{2}\.\d{2})$', number)
        if old_date:
            old_date = old_date[0]
            new_date = '20' + old_date
            number = number.replace(old_date, new_date)
    for each in res_list:
        href = each.xpath("@href")
        title = each.xpath("div[@class='video-title']/strong/text()")
        meta = each.xpath("div[@class='meta']/text()")
        href = href[0] if href else ''
        title = title[0] if title else ''
        meta = meta[0].strip() if meta else ''
        info_list.append([href, title, meta])
    for each in info_list:  # 先从所有结果里精确匹配，避免gs067模糊匹配问题
        if number.upper() in each[1].upper():
            return each[0]
    for each in info_list:  # 再从所有结果模糊匹配
        if number.upper().replace('.', '').replace('-', '').replace(' ', '') in (each[1] + each[2]).upper().replace('-',
                                                                                                                    '').replace(
            '.', '').replace(' ', ''):
            return each[0]
    return False


def get_website(real_url, javdb_website):
    real_url = real_url.replace(javdb_website, 'https://javdb.com') if javdb_website else real_url
    return real_url.replace('?locale=zh', '')


def get_wanted(html):
    result = re.findall(r'(\d+)人想看', html)
    return str(result[0]) if result else ''


def main(number, appoint_url='', log_info='', req_web='', language='jp', org_language='zh_cn'):
    global sleep
    start_time = time.time()
    website_name = 'javdb'
    req_web += '-> %s' % website_name

    javdb_time = config.javdb_time
    cookies = config.javdb_cookie
    javdb_url = 'https://javdb.com'
    if hasattr(config, 'javdb_website'):
        javdb_url = config.javdb_website
    if appoint_url and '?locale' not in appoint_url:
        appoint_url += '?locale=zh'
    real_url = appoint_url
    title = ''
    cover_url = ''
    poster_url = ''
    image_download = False
    image_cut = 'right'
    url_search = ''
    web_info = '\n       '
    debug_info = ''

    if javdb_time > 0 and sleep:
        rr = random.randint(int(javdb_time / 2), javdb_time)
        log_info += '\n    🌐 javdb (⏱ %sS)' % rr
        for i in range(rr):  # 检查是否手动停止刮削
            time.sleep(1)
    else:
        log_info += '\n    🌐 javdb'

    try:  # 捕获主动抛出的异常
        if not real_url:

            # 生成搜索地址
            url_search = javdb_url + '/search?q=' + number.strip() + '&locale=zh'
            debug_info = '搜索地址: %s ' % url_search
            log_info += web_info + debug_info

            # 先使用scraper方法请求，失败时再使用get请求
            result, html_search = curl_html(url_search, cookies=cookies)
            if not result:
                # 判断返回内容是否有问题
                if html_search.startswith('403'):
                    debug_info = f'网站禁止访问！！请更换其他非日本节点！点击 {url_search} 查看详情！'
                else:
                    debug_info = '请求错误: %s' % html_search
                log_info += web_info + debug_info
                raise Exception(debug_info)

            # 判断返回内容是否有问题
            if "The owner of this website has banned your access based on your browser's behaving" in html_search:
                debug_info = f'由于请求过多，javdb网站暂时禁止了你当前IP的访问！！点击 {url_search} 查看详情！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            if "Due to copyright restrictions" in html_search:
                debug_info = f'由于版权限制，javdb网站禁止了日本IP的访问！！请更换日本以外代理！点击 {url_search} 查看详情！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            if 'ray-id' in html_search:
                real_url = ''
                debug_info = '搜索结果: 被 Cloudflare 5 秒盾拦截！请尝试更换cookie！'
                log_info += web_info + debug_info
                raise Exception(debug_info)

            # 获取链接
            html = etree.fromstring(html_search, etree.HTMLParser())
            real_url = get_real_url(html, number)
            if not real_url:
                debug_info = '搜索结果: 未匹配到番号！'
                log_info += web_info + debug_info
                raise Exception(debug_info)

        if real_url:
            javdbid = ''
            if real_url.startswith("/v/"):
                javdbid = real_url.replace("/v/", "")
            if not appoint_url:
                real_url = javdb_url + real_url + '?locale=zh'
            debug_info = '番号地址: %s ' % real_url
            log_info += web_info + debug_info

            result, html_info = curl_html(real_url, cookies=cookies)
            if not result:
                debug_info = '请求错误: %s' % html_info
                log_info += web_info + debug_info
                raise Exception(debug_info)

            # 判断返回内容是否有问题
            if "The owner of this website has banned your access based on your browser's behaving" in html_info:
                debug_info = f'由于请求过多，javdb网站暂时禁止了你当前IP的访问！！点击 {real_url} 查看详情！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            if "Due to copyright restrictions" in html_info:
                debug_info = f'由于版权限制，javdb网站禁止了日本IP的访问！！请更换日本以外代理！点击 {real_url} 查看详情！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            if "/plans/sfpay_order" in html_info or 'payment-methods' in html_info:
                debug_info = f'需要 VIP 权限才能访问此内容！点击 {real_url} 查看详情！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            if "/password_resets" in html_info:
                debug_info = f'此內容需要登入才能查看或操作！点击 {real_url} 查看详情！'
                log_info += web_info + debug_info
                if cookies and cookies.get('cookie'):
                    debug_info = 'Cookie 已失效，请到设置中更新 javdb Cookie！'
                    log_info += web_info + debug_info
                else:
                    debug_info = '请到【设置】-【网络】中添加 javdb Cookie！'
                    log_info += web_info + debug_info
                raise Exception(debug_info)
            if 'Cloudflare' in html_info:
                real_url = ''
                debug_info = '返回结果: 被 Cloudflare 5 秒盾拦截！请尝试更换cookie！'
                log_info += web_info + debug_info
                raise Exception(debug_info)

            html_detail = etree.fromstring(html_info, etree.HTMLParser())

            # ========================================================================收集信息
            title, originaltitle = get_title(html_detail, org_language)  # 获取标题并去掉头尾歌手名
            if not title:
                debug_info = '数据获取失败: 未获取到标题！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            mosaic = get_mosaic(title)
            actor, all_actor = get_actor(html_detail)  # 获取actor
            actor_photo = get_actor_photo(actor)
            all_actor_photo = get_actor_photo(all_actor)
            number = get_number(html_detail, number)
            title = title.replace('中文字幕', '').replace('無碼', '').replace("\\n", '').replace('_', '-').replace(
                number.upper(), '').replace(number, '').replace('--', '-').strip()
            originaltitle = originaltitle.replace('中文字幕', '').replace('無碼', '').replace("\\n", '').replace('_',
                                                                                                                 '-').replace(
                number.upper(), '').replace(number, '').replace('--', '-').strip()
            cover_url = get_cover(html_detail)  # 获取cover
            poster_url = cover_url.replace('/covers/', '/thumbs/')
            outline = ''
            tag = get_tag(html_detail)
            release = get_release(html_detail)
            year = get_year(release)
            runtime = get_runtime(html_detail)
            score = get_score(html_detail)
            series = get_series(html_detail)
            director = get_director(html_detail)
            studio = get_studio(html_detail)
            publisher = get_publisher(html_detail)
            extrafanart = get_extrafanart(html_detail)
            trailer = get_trailer(html_detail)
            website = get_website(real_url, javdb_url)
            wanted = get_wanted(html_info)
            title_rep = ['第一集', '第二集', ' - 上', ' - 下', ' 上集', ' 下集', ' -上', ' -下']
            for each in title_rep:
                title = title.replace(each, '').strip()
            try:
                dic = {
                    'number': number,
                    'title': title,
                    'originaltitle': originaltitle,
                    'actor': actor,
                    'all_actor': all_actor,
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
                    'source': 'javdb',
                    'actor_photo': actor_photo,
                    'all_actor_photo': all_actor_photo,
                    'cover': cover_url,
                    'poster': poster_url,
                    'extrafanart': extrafanart,
                    'trailer': trailer,
                    'image_download': image_download,
                    'image_cut': image_cut,
                    'log_info': log_info,
                    'error_info': '',
                    'req_web': req_web + '(%ss) ' % (round((time.time() - start_time), )),
                    'mosaic': mosaic,
                    'website': website,
                    'wanted': wanted,
                }
                if javdbid:
                    dic['javdbid'] = javdbid
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
    sleep = False
    # yapf: disable
    # print(main('FC2-2792171')) # 开通vip才能查看
    # print(main('080815_130'))   # trailer url is http, not https
    # print(main('', 'https://javdb.com/v/dWmGB'))
    # print(main('CEMD-133'))
    # print(main('FC2-880652'))
    # print(main('PLA-018'))
    # print(main('SIVR-060'))
    # print(main('STCV-067'))
    # print(main('SIVR-100', 'https://javdb.com/v/x9KWn?locale=zh'))
    # print(main('MIDV-018'))
    # print(main('MIDV-018', appoint_url='https://javdb.com/v/BnMY9'))
    # print(main('SVSS-003'))
    # print(main('SIVR-008'))
    # print(main('blacked.21.07.03'))
    # print(main('sexart.20.05.31'))
    # print(main('FC2-2656208'))
    # print(main('aoz-301z'))
    # print(main('', 'https://javdb.com/v/GAO75'))
    # print(main('SIRO-4770 '))
    # print(main('4030-2405'))  # 需要登录
    print(main('FC2-1262472'))  # 需要登录
    # print(main('HUNTB-107'))  # 预告片返回url错误，只有https
    # print(main('FC2-2392657'))                                                  # 需要登录
    # print(main('GS-067'))                                                       # 两个同名番号
    # print(main('MIDE-022'))
    # print(main('KRAY-001'))
    # print(main('ssis-243'))
    # print(main('MIDE-900', 'https://javdb.com/v/MZp24?locale=en'))
    # print(main('TD-011'))
    # print(main('stars-011'))    # 发行商SOD star，下载封面
    # print(main('stars-198'))  # 发行商SOD star，下载封面
    # print(main('mium-748'))
    # print(main('KMHRS-050'))    # 剧照第一张作为poster
    # print(main('SIRO-4042'))
    # print(main('snis-035'))
    # print(main('snis-036'))
    # print(main('vixen.18.07.18', ''))
    # print(main('vixen.16.08.02', ''))
    # print(main('SNIS-016', ''))
    # print(main('bangbros18.19.09.17'))
    # print(main('x-art.19.11.03'))
    # print(main('abs-141'))
    # print(main('HYSD-00083'))
    # print(main('IESP-660'))
    # print(main('n1403'))
    # print(main('GANA-1910'))
    # print(main('heyzo-1031'))
    # print(main('032020-001'))
    # print(main('S2M-055'))
    # print(main('LUXU-1217'))
    # print(main('SSIS-001', ''))
    # print(main('SSIS-090', ''))
    # print(main('DANDY-520', ''))
    # print(main('teenslovehugecocks.22.09.14'))
    # print(main('HYSD-00083', ''))
    # print(main('IESP-660', ''))
    # print(main('n1403', ''))
    # print(main('GANA-1910', ''))
    # print(main('heyzo-1031', ''))
    # print(main_us('x-art.19.11.03'))
    # print(main('032020-001', ''))
    # print(main('S2M-055', ''))
    # print(main('LUXU-1217', ''))
    # print(main_us('x-art.19.11.03', ''))
