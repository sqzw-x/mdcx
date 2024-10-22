#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os.path
import re
import time  # yapf: disable # NOQA: E402
import traceback
from difflib import SequenceMatcher

import oshash
import urllib3

from models.base.number import long_name, remove_escape_string
from models.base.web import get_html
from models.config.config import config
from models.crawlers import theporndb_movies

urllib3.disable_warnings()  # yapf: disable


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def read_data(data):
    title = data.get('title')
    if not title:
        title = ''
    outline = data.get('description')
    if not outline:
        outline = ''
    else:
        outline = outline.replace('＜p＞', '').replace('＜/p＞', '')
    release = data.get('date')
    if not release:
        release = ''
    year = get_year(release)
    trailer = data.get('trailer')
    if not trailer:
        trailer = ''
    try:
        cover = data['background']['large']
    except:
        cover = data.get('image')
    if not cover:
        cover = ''
    try:
        poster = data['posters']['large']
    except:
        poster = data.get('poster')
    if not poster:
        poster = ''
    try:
        runtime = str(int(int(data.get('duration')) / 60))
    except:
        runtime = ''
    try:
        series = data['site']['name']
    except:
        series = ''
    try:
        studio = data['site']['network']['name']
    except:
        studio = ''
    publisher = studio
    try:
        director = data['director']['name']
    except:
        director = ''
    tag_list = []
    try:
        for each in data['tags']:
            tag_list.append(each['name'])
    except:
        pass
    tag = ','.join(tag_list)
    slug = data['slug']
    real_url = f'https://api.theporndb.net/scenes/{slug}' if slug else ''
    all_actor_list = []
    actor_list = []
    try:
        for each in data['performers']:
            all_actor_list.append(each['name'])
            if each['parent']['extras']['gender'] != 'Male':
                actor_list.append(each['name'])
    except:
        pass
    all_actor = ','.join(all_actor_list)
    actor = ','.join(actor_list)
    number = get_number(series, release, title)

    return number, title, outline, actor, all_actor, cover, poster, trailer, release, year, runtime, tag, director, series, studio, publisher, real_url


def get_real_url(res_search, file_path, series_ex, date):
    search_data = res_search.get('data')
    file_name = os.path.split(file_path)[1].lower()
    new_file_name = re.findall(r'[\.-_]\d{2}\.\d{2}\.\d{2}(.+)', file_name)
    new_file_name = new_file_name[0] if new_file_name else file_name
    actor_number = len(new_file_name.replace('.and.', '&').split('&'))
    temp_file_path_space = re.sub(r'[\W_]', ' ', file_path.lower()).replace('  ', ' ').replace('  ', ' ')
    temp_file_path_nospace = temp_file_path_space.replace(' ', '')
    try:
        if search_data:
            res_date_list = []
            res_title_list = []
            res_actor_list = []
            for each in search_data:
                res_id_url = f"https://api.theporndb.net/scenes/{each['slug']}"
                try:
                    res_series = each['site']['short_name']
                except:
                    res_series = ''
                try:
                    res_url = each['site']['url'].replace('-', '')
                except:
                    res_url = ''
                res_date = each['date']
                res_title_space = re.sub(r'[\W_]', ' ', each['title'].lower())
                res_title_nospace = res_title_space.replace(' ', '')
                actor_list_space = []
                actor_list_nospace = []
                for a in each['performers']:
                    ac = re.sub(r'[\W_]', ' ', a['name'].lower())
                    actor_list_space.append(ac)
                    actor_list_nospace.append(ac.replace(' ', ''))
                res_actor_title_space = (' '.join(actor_list_space) + ' ' + res_title_space).replace('  ', ' ')

                # 有系列时
                if series_ex:
                    # 系列相同时，先判断日期，再判断标题，再判断演员（系列有时会缩写，比如 BellesaFilms.19.10.11；日期有时会错误，比如 Throated.17.01.17）
                    if series_ex == res_series or series_ex in res_url:
                        if date and res_date == date:
                            res_date_list.append([res_id_url, res_actor_title_space])
                        elif res_title_nospace in temp_file_path_nospace:
                            res_title_list.append([res_id_url, res_actor_title_space])
                        elif actor_list_nospace and len(actor_list_nospace) >= actor_number:
                            for a in actor_list_nospace:
                                if a not in temp_file_path_nospace:
                                    break
                            else:
                                res_actor_list.append([res_id_url, res_actor_title_space])
                    else:
                        # 系列不同时，当日期和标题同时命中，则视为系列错误（比如 AdultTime.20.02.14.Angela.White.And.Courtney.Trouble.Love.Lust.Respect）
                        if date and res_date == date and res_title_nospace in temp_file_path_nospace:
                            res_title_list.append([res_id_url, res_actor_title_space])

                # 没有系列时，只判断标题
                else:
                    res_title_list.append([res_id_url, res_actor_title_space])

            # 系列+日期命中时，一个结果，直接命中；多个结果，返回相似度高的
            if len(res_date_list):
                if len(res_date_list) == 1:
                    return res_date_list[0][0]
                m = 0
                for each in res_date_list:
                    n = similarity(each[1], temp_file_path_space)
                    if n > m:
                        m = n
                        real_url = each[0]
                return real_url

            # 标题命中时，一个结果，直接命中；多个结果，返回相似度高的
            if len(res_title_list):
                if len(res_title_list) == 1:
                    return res_title_list[0][0]
                m = 0
                for each in res_title_list:
                    n = similarity(each[1], temp_file_path_space)
                    if n > m:
                        m = n
                        real_url = each[0]
                return real_url

            # 演员命中时，一个结果，直接命中；多个结果，返回相似度高的
            if len(res_actor_list):
                if len(res_actor_list) == 1:
                    return res_actor_list[0][0]
                m = 0
                for each in res_actor_list:
                    n = similarity(each[1], temp_file_path_space)
                    if n > m:
                        m = n
                        real_url = each[0]
                return real_url
    except:
        print(traceback.format_exc())
    return False


def get_search_keyword(file_path):
    file_path = remove_escape_string(file_path)
    file_name = os.path.basename(file_path.replace('\\', '/')).replace(',', '.')
    file_name = os.path.splitext(file_name)[0]

    temp_number = re.findall(r'(([A-Z0-9-\.]{2,})[-_\. ]{1}2?0?(\d{2}[-\.]\d{2}[-\.]\d{2}))', file_path)
    keyword_list = []
    series_ex = ''
    date = ''
    if temp_number:
        full_number, series_ex, date = temp_number[0]
        series_ex = long_name(series_ex.lower().replace('-', '').replace('.', ''))
        date = '20' + date.replace('.', '-')
        keyword_list.append(series_ex + ' ' + date)  # 系列 + 发行时间
        temp_title = re.sub(r'[-_&\.]', ' ', file_name.replace(full_number, '')).strip()
        temp_title_list = []
        [temp_title_list.append(i) for i in temp_title.split(' ') if i and i != series_ex]
        keyword_list.append(series_ex + ' ' + ' '.join(temp_title_list[:2]))  # 系列 + 标题（去掉日期）
    else:
        keyword_list.append(' '.join(file_name.split('.')[:2]).replace('-', ' '))
    return keyword_list, series_ex, date


def get_number(series, release, title):
    try:
        if series and release:
            return series.replace(' ', '') + '.' + re.findall(r'\d{2}-\d{2}-\d{2}', release)[0].replace('-', '.')
    except:
        pass
    return title


def get_actor_photo(actor):
    actor = actor.split(',')
    data = {}
    for i in actor:
        actor_photo = {i: ''}
        data.update(actor_photo)
    return data


def get_year(release):
    try:
        return re.findall(r'\d{4}', release)[0]
    except:
        return ''


def main(number, appoint_url='', log_info='', req_web='', language='zh_cn', file_path='', appoint_number=''):
    if not file_path:
        file_path = number + '.mp4'
    start_time = time.time()
    website_name = 'theporndb'
    req_web += '-> %s' % website_name

    api_token = config.theporndb_api_token
    theporndb_no_hash = config.theporndb_no_hash
    real_url = appoint_url.replace("//theporndb", "//api.theporndb")
    title = number
    cover_url = ''
    poster_url = ''
    image_download = False
    image_cut = ''
    log_info += '\n    🌐 theporndb'
    web_info = '\n       '
    debug_info = ''
    mosaic = '无码'
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.202 Safari/537.36',
    }
    hash_data = ''

    try:  # 捕获主动抛出的异常
        if not api_token:
            debug_info = '请添加 API Token 后刮削！（「设置」-「网络」-「API Token」）'
            log_info += web_info + debug_info
            raise Exception(debug_info)

        if not real_url:
            # 通过hash搜索
            try:
                if not theporndb_no_hash:
                    hash = oshash.oshash(file_path)
                    # hash = '8679fcbdd29fa735'
                    url_hash = f'https://api.theporndb.net/scenes/hash/{hash}'
                    debug_info = '请求地址: %s ' % url_hash
                    log_info += web_info + debug_info
                    result, hash_search = get_html(url_hash, headers=headers, json_data=True)

                    if not result:
                        # 判断返回内容是否有问题
                        debug_info = '请求错误: %s' % hash_search
                        log_info += web_info + debug_info
                        if '401 http' in hash_search:
                            debug_info = '请检查 API Token 是否正确: %s ' % api_token
                            log_info += web_info + debug_info
                        raise Exception(debug_info)
                    hash_data = hash_search.get('data')
                    if hash_data:
                        number, title, outline, actor, all_actor, cover_url, poster_url, trailer, release, year, runtime, tag, director, series, studio, publisher, real_url = read_data(
                            hash_data)
            except:
                pass

            # 通过文件名搜索
            if title and not hash_data:
                search_keyword_list, series_ex, date = get_search_keyword(file_path)
                for search_keyword in search_keyword_list:
                    url_search = f'https://api.theporndb.net/scenes?parse={search_keyword}&per_page=100'
                    debug_info = f'请求地址: {url_search} '
                    log_info += web_info + debug_info
                    result, res_search = get_html(url_search, headers=headers, json_data=True)

                    if not result:
                        # 判断返回内容是否有问题
                        debug_info = f'请求错误: {url_search}'
                        log_info += web_info + debug_info
                        if '401 http' in res_search:
                            debug_info = f'请检查 API Token 是否正确: {api_token} '
                            log_info += web_info + debug_info
                        raise Exception(debug_info)

                    real_url = get_real_url(res_search, file_path, series_ex, date)
                    if real_url:
                        break
                else:
                    debug_info = f'未找到匹配的内容: {url_search}'
                    log_info += web_info + debug_info
                    raise Exception(debug_info)

        if not hash_data:
            debug_info = '番号地址: %s ' % real_url
            log_info += web_info + debug_info
            result, res_real = get_html(real_url, headers=headers, json_data=True)
            if not result:
                # 判断返回内容是否有问题
                debug_info = '请求错误: %s ' % res_real
                log_info += web_info + debug_info
                if '401 http' in res_real:
                    debug_info = '请检查 API Token 是否正确: %s ' % api_token
                    log_info += web_info + debug_info
                raise Exception(debug_info)

            real_data = res_real.get('data')
            if real_data:
                number, title, outline, actor, all_actor, cover_url, poster_url, trailer, release, year, runtime, tag, director, series, studio, publisher, real_url = read_data(
                    real_data)
            else:
                debug_info = '未获取正确数据: %s' % real_url
                log_info += web_info + debug_info
                raise Exception(debug_info)

        actor_photo = get_actor_photo(actor)
        all_actor_photo = get_actor_photo(all_actor)

        try:
            dic = {
                'number': number,
                'title': title,
                'originaltitle': title,
                'actor': actor,
                'all_actor': all_actor,
                'outline': outline,
                'originalplot': outline,
                'tag': tag,
                'release': release,
                'year': year,
                'runtime': runtime,
                'score': '',
                'series': series,
                'director': director,
                'studio': studio,
                'publisher': publisher,
                'source': 'theporndb',
                'actor_photo': actor_photo,
                'all_actor_photo': all_actor_photo,
                'cover': cover_url,
                'poster': poster_url,
                'extrafanart': [],
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

    except:
        # print(traceback.format_exc())
        req_web = req_web + '(%ss) ' % (round((time.time() - start_time), ))
        return theporndb_movies.main(number,
                                     appoint_url=appoint_url,
                                     log_info=log_info,
                                     req_web=req_web,
                                     language='zh_cn',
                                     file_path=file_path,
                                     appoint_number=appoint_number)

    dic = {website_name: {'zh_cn': dic, 'zh_tw': dic, 'jp': dic}}
    js = json.dumps(dic, ensure_ascii=False, sort_keys=False, indent=4, separators=(',', ': '), )  # .encode('UTF-8')
    return js


if __name__ == '__main__':
    # yapf: disable
    # print(main('blacked.21.07.03'))
    # print(main('sexart.20.05.31'))
    # print(main('vixen.18.07.18', ''))
    # print(main('vixen.16.08.02', ''))
    # print(main('bangbros18.19.09.17'))
    # print(main('x-art.19.11.03'))
    # print(main('teenslovehugecocks.22.09.14'))
    # print(main('x-art.19.11.03'))
    # print(main('x-art.13.03.29'))
    # print(main('Strawberries and Wine Hdv'))
    # print(main('', file_path='BellesaFilms.19.10.11.Angela.White.Open.House.XXX.1080p.MP4-KTR.mp4'))    # 系列 日期命中（系列有缩写，命中url）
    # print(main('', file_path='Bang.Confessions.18.02.16.Angela.White.XXX.1080p.MP4-KTR.mp4')) # 系列 日期命中（系列中有.）
    # print(main('', file_path='AngelaWhite.17.12.20.Angela.White.And.Mandingo.129.XXX.1080p.MP4-KTR.mp4'))   # 仅命中一个演员，视为失败
    # print(main('', file_path='Throated.17.01.17.Jillian.Janson.XXX.1080p.MP4-KTR.mp4'))   # 系列、标题命中
    # print(main('', file_path='ZZSeries.19.03.12.Lela.Star.BrazziBots.Part.3.XXX.1080p.MP4-KTR[rarbg].mp4'))   # date（系列缩写zzs）
    # print(main('', file_path='PurgatoryX.19.11.01.Angela.White.The.Dentist.Episode.3.XXX.1080p.MP4-KTR.mp4'))   # 系列 日期命中（系列错了，命中url）
    # print(main('', file_path='AdultTime.20.02.14.Angela.White.And.Courtney.Trouble.Love.Lust.Respect.XXX.1080p.MP4-KTR.mp4'))   # 系列错了
    # print(main('', file_path='AdultTime.20.02.17.Angela.White.Full.Body.Physical.Exam.XXX.1080p.MP4-KTR.mp4'))   # 无命中演员，视为失败
    # print(main('', file_path='SexArt_12.04.13-Elle Alexandra & Lexi Bloom & Malena Morgan-Stepping-Out_SexArt-1080p.mp4'))   # 多个，按相似度命中
    # print(main('', file_path='SexArt.12.04.13 Sex Art.mp4'))   # 多个，按相似度命中
    print(main('nubilefilms-all-work-and-no-play',
               file_path=''))  # print(main('', file_path='SexArt_12.04.13-Elle Alexandra & Malena Morgan-Under-The-Elle-Tree_SexArt-1080p.mp4'))   # 多个，按相似度命中  # print(main('', file_path='SexArt_12.04.13-Elle Alexandra & Rilee Marks-Whispers_SexArt-1080p.mp4'))   # 多个，按相似度命中  # print(main('', file_path='SexArt_12.04.13-Hayden Hawkens & Malena Morgan-Golden_SexArt-1080p.mp4'))   # 多个，按相似度命中  # print(main('', file_path='SexArt_12.04.13-Hayden Hawkens-Butterfly-Blue_SexArt-1080p.mp4'))   # 多个，按相似度命中  # print(main('', file_path='SexArt_12.04.13-Lexi Bloom & Logan Pierce-My-First_SexArt-1080p.mp4'))   # 多个，按相似度命中  # print(main('', file_path='LittleCaprice-Dreams.23.02.18.sky.pierce.and.little.caprice.nasstyx.4k.mp4'))   # 日期不对，缺失演员，标题名顺序不匹配，待调研方案  # print(main('', file_path='LittleCaprice-Dreams.23.02.18.nasstyx.little.caprice.sky.pierce.max.4k.mp4'))   # 缺失演员  # print(main('', file_path='ClubSeventeen.18.09.24.Alecia.Fox.Hardcore.XXX.2160p.MP4-KTR[rarbg].mp4'))   # 系列转换  # print(main('', file_path='ClubSeventeen.18.06.11.Alecia.Fox.And.Gia.Mulino.Lesbian.XXX.2160p.MP4-KTR[rarbg].mp4'))   # 系列转换  # print(main('', file_path='ClubSeventeen.18.07.23.Alecia.Fox.And.Angela.Allison.Lesbian.XXX.2160p.MP4-KTR[rarbg].mp4'))   # 系列转换  # print(main('', file_path='ClubSeventeen.18.10.09.Alecia.Fox.Solo.XXX.2160p.MP4-KTR[rarbg].mp4')) # 多个，按相似度命中  # print(main('', file_path='WhiteTeensBlackCocks.17.07.09.Alecia.Fox.XXX.2160p.MP4-KTR[rarbg].mp4'))   # 缺失资源  # print(main('', file_path='Z:\\分类\\A-日本系列-1080P\\working2\\问题\\blacked.23.02.04.agatha.vega.lika.star.and.jazlyn.ray.mp4'))   # 缺失资源  # print(main('', file_path='brazzersexxtra.23.02.09.aria.lee.and.lulu.chu.pervy.practices.part.1.mp4'))  # print(main('', file_path='brazzersexxtra.23.02.09.lulu.chu.pervy.practices.part.2..mp4'))  # print(main('blacked-2015-03-22-karla-kush', file_path='blacked-2015-03-22-karla-kush.ts'))  # print(main('', file_path='tft-2019-01-14-rachael-cavalli-my-teachers-secrets.ts'))  # print(main('', file_path='hussie-pass-bts-new-boobies-a-brand-new-girl.ts'))    # 演员没有性别  # print(main('SWhores.23.02.14', file_path='SWhores.23.02.14..Anal Girl with No Extras.1080P.ts'))    # 未获取到演员  # print(main('', file_path='/test/work/CzechStreets.2019-01-01.18 Y O Virtuoso with Ddd Tits.Nada.mp4'))    # 未获取到演员  # print(main('Evolvedfights.20.10.30',  #            file_path='AARM-018 - 2021-09-28 - 未知演员 - アロマ企画，アロマ企画/evolvedfights.20.10.30.kay.carter.vs.nathan.bronson.mp4'))
