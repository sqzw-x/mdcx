#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import re
import time

import urllib3
import zhconv

from models.base.web import get_html, post_html
from models.config.config import config

urllib3.disable_warnings()  # yapf: disable


# import traceback


def get_api_actor(actor_list):
    actor = []
    for each in actor_list:
        if '♀' in each['sex']:
            actor.append(each['name'].replace('♀', ''))
    return ','.join(actor)


def get_api_tag(tag_list):
    tag = []
    for each in tag_list:
        tag.append(each['name'])
    return ','.join(tag)


def get_api_extrafanart(extrafanart_list):
    extrafanart = []
    for each in extrafanart_list:
        extrafanart.append(each['big_img'])
    return extrafanart


def get_actor_photo(actor):
    actor = actor.split(',')
    data = {}
    for i in actor:
        actor_photo = {i: ''}
        data.update(actor_photo)
    return data


def get_year(release):
    try:
        result = str(re.search(r'\d{4}', release).group())
        return result
    except:
        return release


def get_mosaic(title, studio, tag, mosaic):
    all_info = title + studio + tag
    if '国产' in all_info or '國產' in all_info:
        mosaic = '国产'
    return mosaic


def get_number_list(file_name, number, appoint_number):  # 处理国产番号
    number = number.upper()
    number_list = []  # 返回一个番号列表，用来搜索
    filename_list = []
    result = []

    # 指定番号时，优先使用指定番号
    if appoint_number:
        number_list.append(appoint_number)
        file_name = appoint_number.upper()

    # 获取文件名，有文件名时，优先使用文件名来生成number，并转换为简体
    else:
        file_name = zhconv.convert(file_name, 'zh-cn') if file_name else zhconv.convert(number, 'zh-cn')
        file_name = re.sub(r'-[^0-9]+?$', '', file_name)

    # 获取番号
    # 91CM-081.田恬.李琼.继母与女儿.三.爸爸不在家先上妹妹再玩弄母亲.果冻传媒
    # 91MS-015.张淑仪.19岁D奶少女.被男友甩后下海.疯狂滥交高潮喷水.91制片厂
    if re.search(r'(91[A-Z]{2,})-?(\d{3,})', file_name):
        result = re.search(r'(91[A-Z]{2,})-?(\d{3,})', file_name)
        if result:
            number_normal = '%s-%s' % (result[1], result[2])
            number_list.append(number_normal)

    # MDX-0236-02.沈娜娜.青梅竹马淫乱3P.麻豆传媒映画x逼哩逼哩blibli
    # MD-0140-2.蜜苏.家有性事EP2.爱在身边.麻豆传媒映画
    elif re.search(r'([A-Z]{2,})-?(\d{3,})-(\d+)', file_name):
        result = re.search(r'([A-Z]{2,})-?(\d{3,})-(\d+)', file_name)
        if result:
            number_normal = '%s-%s-%s' % (result[1], result[2], result[3])
            number_list.append(number_normal)

    # MXJ-0005.EP1.弥生美月.小恶魔高校生.与老师共度的放浪补课.麻豆传媒映画
    # MDJ0001 EP2  AV 淫兽鬼父 陈美惠  .TS
    # PMS-003.职场冰与火.EP3设局.宁静.苏文文.设局我要女人都臣服在我胯下.蜜桃影像传媒
    # 淫欲游戏王.EP6.情欲射龙门.性爱篇.郭童童.李娜.双英战龙根3P混战.麻豆传媒映画.ts
    # PMS-001 性爱公寓EP04 仨人.蜜桃影像传媒
    elif 'EP' in file_name:
        result = re.search(r'([A-Z]{2,})-?(\d{3,})(.*)(EP[\d]+)', file_name)
        if result:
            number_normal = '%s-%s.%s%s' % (result[1], result[2], result[3], result[4])
            number_normal = number_normal.replace('..', '.').replace(' ', '')
            number_list.append(number_normal)
            number_list.append(number_normal.replace('.', ' '))

            if len(result[2]) == 3:
                number_normal = '%s-0%s.%s%s' % (result[1], result[2], result[3], result[4])
                number_list.append(number_normal.replace('..', '.').replace(' ', ''))
        else:
            result = re.findall(r'([^. ]+\.EP[\d]+)\.', file_name)
            if result:
                number_list.append(result[0])

    # MKY-HS-004.周寗.催情民宿.偷下春药3P干爆夫妇.麻豆传媒映画
    # PH-US-002.色控.音乐老师全裸诱惑.麻豆传媒映画
    # MKY-TX-002.林芊彤.淫行出租车.负心女的淫奸报复.麻豆传媒映画
    elif re.search(r'([A-Z]{2,})-([A-Z]{2,})-(\d+)', file_name):
        result = re.search(r'([A-Z]{2,})-([A-Z]{2,})-(\d+)', file_name)
        if result:
            number_normal = '%s-%s-%s' % (result[1], result[2], result[3])
            number_list.append(number_normal)

    # MDUS系列[中文字幕].LAX0025.性感尤物渴望激情猛操.RUCK ME LIKE A SEX DOLL.麻豆传媒映画
    elif 'MDUS系列' in file_name:
        result = re.search(r'([A-Z]{3,})-?(\d{3,})', file_name.replace('MDUS系列', ''))
        if result:
            number_normal = '%s-%s' % (result[1], result[2])
            number_list.append(number_normal)

    # REAL野性派001-朋友的女友讓我最上火
    elif 'REAL野性派' in file_name:
        result = re.search(r'REAL野性派-?(\d{3,})', file_name)
        if result:
            number_normal = 'REAL野性派-%s' % (result[1])
            number_list.append(number_normal)

    # mini06.全裸家政.只为弟弟的学费打工.被玩弄的淫乱家政小妹.mini传媒
    elif re.search(r'([A-Z]{3,})-?(\d{2,})', file_name):
        result = re.search(r'([A-Z]{3,})-?(\d{2,})', file_name)
        if result:
            number_normal = '%s-%s' % (result[1], result[2])
            number_list.append(number_normal)

    # MDS-009.张芸熙.巨乳旗袍诱惑.搔首弄姿色气满点.麻豆传媒映画
    # MDS-0014苏畅.纯洁的爱爱.青梅竹马的性爱练习曲.麻豆传媒映画
    # MD-0208.夏晴子.苏清歌.荒诞家族淫游之春.快感刺激的极致调教.麻豆传媒映画
    # MDX-0184.沈娜娜.学生不乖怒操体罚.打屁股插穴样样来.麻豆传媒映画
    # MDXS-0011沈娜娜.足球宝贝射门淫球赚奖金
    # MDL-0002 夏晴子 苏语棠 请做我的奴隶 下集 在魔鬼面前每个人都是奴隶 麻豆传媒映画
    # MMZ-032.寻小小.女神的性辅导.我的老师是寻小小.麻豆出品X猫爪影像
    # MAD-022.穆雪.野性欢愉.爱豆x麻豆联合出品
    # MDWP-0013.璇元.淫行按摩院.麻豆传媒职场淫行系列
    # TT-005.孟若羽.F罩杯性感巨乳DJ.麻豆出品x宫美娱乐
    # MDS005 被雇主强上的熟女家政妇 大声呻吟被操到高潮 杜冰若
    elif re.search(r'([A-Z]{2,})-?(\d{3,})', file_name):
        result = re.search(r'([A-Z]{2,})-?(\d{3,})', file_name)
        if result:
            number_normal = '%s-%s' % (result[1], result[2])
            number_list.append(number_normal)

    # 台湾第一女优吴梦梦.OL误上痴汉地铁.惨遭多人轮番奸玩.麻豆传媒映画代理出品
    # PsychoPorn色控.找来大奶姐姐帮我乳交.麻豆传媒映画
    # 國産麻豆AV 麻豆番外 大番號女優空降上海 特別篇 沈芯語
    # 鲍鱼游戏SquirtGame.吸舔碰糖.失败者屈辱凌辱.麻豆传媒映画伙伴皇家华人
    # 导演系列 外卖员的色情体验 麻豆传媒映画
    # 过长时，可能有多余字段，取头尾
    filename_list.append(file_name[:30])
    if len(file_name) > 25:
        filename_list.append(file_name[-30:-4])
        filename_list.append(file_name[8:30])

    return number_list, filename_list


def main(number, appoint_url='', log_info='', req_web='', language='zh_cn', file_path='', appoint_number='', mosaic=''):
    start_time = time.time()
    number = number.strip()
    website_name = 'hdouban'
    req_web += '-> %s' % website_name

    real_url = appoint_url
    cover_url = ''
    image_cut = ''
    image_download = False
    url_search = ''
    mosaic = ''
    web_info = '\n       '
    log_info += ' \n    🌐 hdouban'
    debug_info = ''
    cover_url = ''
    poster = ''
    outline = ''
    director = ''
    studio = ''
    title = ''
    release = ''
    runtime = ''
    score = ''
    series = ''
    trailer = ''
    hdouban_url = getattr(config, 'hdouban_website', 'https://ormtgu.com')

    # real_url = 'https://byym21.com/moviedetail/153858'
    # real_url = 'https://byym21.com/moviedetail/2202'
    # real_url = 'https://byym21.com/moviedetail/435868'

    try:  # 捕获主动抛出的异常
        if not real_url:
            number_org = [number]
            file_name = os.path.splitext(os.path.split(file_path)[1])[0].upper() if file_path else ''
            number_list, filename_list = get_number_list(file_name, number, appoint_number)
            if mosaic == '国产' or mosaic == '國產':
                total_number_list = number_list + filename_list
            else:
                total_number_list = number_org + number_list + filename_list
            number_list_new = list(set(total_number_list))
            number_list_new.sort(key=total_number_list.index)

            for number in number_list_new:
                # https://api.6dccbca.com/api/search?search=JUL-401&ty=movie&page=1&pageSize=12
                # https://api.6dccbca.com/api/search?ty=movie&search=heyzo-1032&page=1&pageSize=12
                url_search = f'https://api.6dccbca.com/api/search?ty=movie&search={number}&page=1&pageSize=12'
                debug_info = '搜索地址: %s ' % url_search
                log_info += web_info + debug_info

                # ========================================================================搜索番号
                result, html_search = get_html(url_search, json_data=True)
                if not result:
                    debug_info = '网络请求错误: %s ' % html_search
                    log_info += web_info + debug_info
                    raise Exception(debug_info)
                try:
                    result = html_search['data']['list']
                except:
                    debug_info = '搜索结果解析错误: %s ' % str(html_search)
                    log_info += web_info + debug_info
                    raise Exception(debug_info)

                temp_number = number.upper().replace('-', '').strip()
                bingo = False
                for each in result:
                    each_number = each['number'].upper().replace('-', '').strip()
                    each_id = each['id']
                    name = each['name']
                    if temp_number == each_number or temp_number in name.upper().replace('-', '').strip():
                        # https://byym21.com/moviedetail/2202
                        real_url = f'{hdouban_url}/moviedetail/{each_id}'
                        bingo = True
                        break
                if bingo:
                    break
            else:
                debug_info = '搜索结果: 未匹配到番号！'
                log_info += web_info + debug_info
                raise Exception(debug_info)

        if real_url:
            debug_info = '番号地址: %s ' % real_url
            log_info += web_info + debug_info

            # 请求api获取详细数据
            detail_id = re.findall(r'moviedetail/(\d+)', real_url)
            if not detail_id:
                debug_info = f'详情页链接中未获取到详情页 ID: {detail_id}'
                log_info += web_info + debug_info
                raise Exception(debug_info)

            detail_url = 'https://api.6dccbca.com/api/movie/detail'
            data = {"id": str(detail_id[0])}
            result, response = post_html(detail_url, data=data, json_data=True)
            if not result:
                debug_info = '网络请求错误: %s' % response
                log_info += web_info + debug_info
                raise Exception(debug_info)
            res = response['data']
            number = res['number']
            if not re.search(r'n\d{3,}', number):
                number = number.upper()
            title = res['name'].replace(number, '').strip()
            if not title:
                debug_info = '数据获取失败: 未获取到title！'
                log_info += web_info + debug_info
                raise Exception(debug_info)
            cover_url = res['big_cove']
            poster = res['small_cover']
            actor = get_api_actor(res['actors'])
            tag = get_api_tag(res['labels'])
            director = res['director'][0]['name'] if res['director'] else ''
            studio = res['company'][0]['name'] if res['company'] else ''
            series = res['series'][0]['name'] if res['series'] else ''
            release = res['release_time'].replace(' 00:00:00', '')
            runtime = res['time']
            runtime = str(int(int(runtime) / 3600)) if runtime else ''
            score = res['score']
            trailer = res['trailer']
            extrafanart = get_api_extrafanart(res['map'])
            year = get_year(release)
            mosaic = get_mosaic(title, studio, tag, mosaic)

            # 清除标题中的演员
            actor_photo = get_actor_photo(actor)
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
                    'publisher': studio,
                    'source': 'hdouban',
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
                    'website': re.sub(r'http[s]?://[^/]+', hdouban_url, real_url),
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
    # print(main('MKY-JB-010 '))
    # print(main('91CM-248 '))    # 无结果
    # print(main('MDTZ-059'))
    # print(main('SSIS-334'))
    # print(main('snis-036')) # 双人
    # print(main('SSNI-826'))
    # print(main('大胸母女勾引家教被爆操'))
    print(main('CEMD-248'))  # print(main('TMG-019'))  # print(main('FC2-2473284 '))  # print(main('SHYN-147 '))    # 有系列  # print(main('MIAE-346'))     # 无结果  # print(main('STARS-191'))    # poster图片  # print(main('abw-157'))  # print(main('abs-141'))  # print(main('HYSD-00083'))  # print(main('IESP-660'))  # print(main('n1403'))  # print(main('GANA-1910'))  # print(main('heyzo-1031'))  # print(main('x-art.19.11.03'))  # print(main('032020-001'))  # print(main('S2M-055'))  # print(main('LUXU-1217'))  # print(main('1101132', ''))  # print(main('OFJE-318'))  # print(main('110119-001'))  # print(main('abs-001'))  # print(main('SSIS-090', ''))  # print(main('SSIS-090', ''))  # print(main('SNIS-016', ''))  # print(main('HYSD-00083', ''))  # print(main('IESP-660', ''))  # print(main('n1403', ''))  # print(main('GANA-1910', ''))  # print(main('heyzo-1031', ''))  # print(main('x-art.19.11.03'))  # print(main('032020-001', ''))  # print(main('S2M-055', ''))  # print(main('LUXU-1217', ''))  # print(main('x-art.19.11.03', ''))
