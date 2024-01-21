import hashlib
import random
import re
import threading
import time
import traceback
import urllib

import deepl
import langid
import zhconv

from models.base.number import get_number_letters
from models.base.utils import get_used_time, remove_repeat
from models.base.web import get_html, post_html
from models.config.config import config
from models.config.resources import resources
from models.core.flags import Flags
from models.core.web import get_actorname, get_yesjav_title, google_translate
from models.signals import signal

deepl_result = {}


def youdao_translate(title, outline):
    url = 'https://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule'
    msg = '%s\n%s' % (title, outline)
    lts = str(int(time.time() * 1000))
    salt = lts + str(random.randint(0, 10))
    sign = hashlib.md5(("fanyideskweb" + msg + salt + config.youdaokey).encode('utf-8')).hexdigest()

    data = {
        'i': msg,
        'from': 'AUTO',
        'to': 'zh-CHS',
        'smartresult': 'dict',
        'client': 'fanyideskweb',
        'salt': salt,
        'sign': sign,
        'lts': lts,
        'bv': 'c6b8c998b2cbaa29bd94afc223bc106c',
        'doctype': 'json',
        'version': '2.1',
        'keyfrom': 'fanyi.web',
        'ue': 'UTF-8',
        'typoResult': 'true',
        'action': 'FY_BY_CLICKBUTTION',
    }
    headers = {
        'Cookie': random.choice([
            "OUTFOX_SEARCH_USER_ID=833904829@10.169.0.84",
            "OUTFOX_SEARCH_USER_ID=-10218418@11.136.67.24;",
            "OUTFOX_SEARCH_USER_ID=1989505748@10.108.160.19;",
            "OUTFOX_SEARCH_USER_ID=2072418438@218.82.240.196;",
            "OUTFOX_SEARCH_USER_ID=1768574849@220.181.76.83;",
            "OUTFOX_SEARCH_USER_ID=-2153895048@10.168.8.76;",
        ]),
        'Referer': 'https://fanyi.youdao.com/?keyfrom=dict2.top',
    }
    headers_o = config.headers
    headers.update(headers_o)
    result, res = post_html(url, data=data, headers=headers, json_data=True)
    if not result:
        return title, outline, f'请求失败！可能是被封了，可尝试更换代理！错误：{res}'
    else:
        translateResult = res.get('translateResult')
        if not translateResult:
            return title, outline, f'返回数据未找到翻译结果！返回内容：{res}'
        else:
            list_count = len(translateResult)
            if list_count:
                i = 0
                if title:
                    i = 1
                    title_result_list = translateResult[0]
                    title_list = [a.get('tgt') for a in title_result_list]
                    title_temp = ''.join(title_list)
                    if title_temp:
                        title = title_temp
                if outline:
                    outline_temp = ''
                    for j in range(i, list_count):
                        outline_result_list = translateResult[j]
                        outline_list = [a.get('tgt') for a in outline_result_list]
                        outline_temp += ''.join(outline_list) + '\n'
                    outline_temp = outline_temp.strip('\n')
                    if outline_temp:
                        outline = outline_temp
    return title, outline.strip('\n'), ''


def _deepl_trans_thread(ls, title, outline, json_data):
    global deepl_result
    result = ''
    try:
        if title:
            title = deepl.translate(source_language=ls, target_language="ZH", text=title)
        if outline:
            outline = deepl.translate(source_language=ls, target_language="ZH", text=outline)
    except Exception as e:
        result = f'网页接口请求失败! 错误：{e}'
        print(title, outline, f'网页接口请求失败! 错误：{e}')
    deepl_result[json_data['file_path']] = (title, outline, result)


def deepl_translate(title, outline, ls='JA', json_data=None):
    global deepl_result
    deepl_key = config.deepl_key
    if not deepl_key:
        if json_data:
            t_deepl = threading.Thread(target=_deepl_trans_thread, args=(ls, title, outline, json_data))
            t_deepl.setDaemon(True)
            t_deepl.start()
            t_deepl.join(timeout=config.timeout)
            t, o, r = title, outline, '翻译失败或超时！'
            if deepl_result.get(json_data['file_path']):
                t, o, r = deepl_result[json_data['file_path']]
            return t, o, r
        else:
            try:
                if title:
                    title = deepl.translate(source_language=ls, target_language="ZH", text=title)
                if outline:
                    outline = deepl.translate(source_language=ls, target_language="ZH", text=outline)
                return title, outline, ''
            except Exception as e:
                return title, outline, f'网页接口请求失败! 错误：{e}'

    deepl_url = 'https://api-free.deepl.com' if ':fx' in deepl_key else 'https://api.deepl.com'
    url = f'{deepl_url}/v2/translate?auth_key={deepl_key}&source_lang={ls}&target_lang=ZH'
    params_title = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'text': title,
    }
    params_outline = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'text': outline,
    }

    if title:
        result, res = post_html(url, data=params_title, json_data=True)
        if not result:
            return title, outline, f'API 接口请求失败！错误：{res}'
        else:
            if 'translations' in res:
                title = res["translations"][0]["text"]
            else:
                return title, outline, f'API 接口返回数据异常！返回内容：{res}'
    if outline:
        result, res = post_html(url, data=params_outline, json_data=True)
        if not result:
            return title, outline, f'API 接口请求失败！错误：{res}'
        else:
            if 'translations' in res:
                outline = res["translations"][0]["text"]
            else:
                return title, outline, f'API 接口返回数据异常！返回内容：{res}'
    return title, outline, ''


def translate_info(json_data):
    xml_info = resources.info_mapping_data
    if len(xml_info) == 0:
        return json_data
    tag_translate = config.tag_translate
    series_translate = config.series_translate
    studio_translate = config.studio_translate
    publisher_translate = config.publisher_translate
    director_translate = config.director_translate
    tag_language = config.tag_language
    series_language = config.series_language
    studio_language = config.studio_language
    publisher_language = config.publisher_language
    director_language = config.director_language
    fields_rule = config.fields_rule

    tag_include = config.tag_include
    tag = json_data['tag']
    remove_key = ['HD高画质', 'HD高畫質', '高画质', '高畫質', '無碼流出', '无码流出', '無碼破解', '无码破解',
                  '無碼片', '无码片', '有碼片', '有码片', '無碼', '无码', '有碼', '有码', '流出', '国产', '國產']
    for each_key in remove_key:
        tag = tag.replace(each_key, '')

    # 映射tag并且存在xml_info时，处理tag映射
    if tag_translate == 'on':
        tag_list = re.split(r'[,，]', tag)
        tag_new = []
        for each_info in tag_list:
            if each_info:  # 为空时会多出来一个
                info_data = resources.get_info_data(each_info)
                each_info = info_data.get(tag_language)
                if each_info and each_info not in tag_new:
                    tag_new.append(each_info)
        tag = ','.join(tag_new)

    # tag去重/去空/排序
    tag = remove_repeat(tag)

    # 添加演员
    if 'actor' in tag_include and json_data['actor']:
        tag = json_data['actor'] + ',' + tag
        tag = tag.strip(',')

    # 添加番号前缀
    letters = json_data['letters']
    if 'letters' in tag_include and letters and letters != '未知车牌':
        # 去除素人番号前缀数字
        if 'del_num' in fields_rule:
            temp_n = re.findall(r'\d{3,}([a-zA-Z]+-\d+)', json_data['number'])
            if temp_n:
                letters = get_number_letters(temp_n[0])
                json_data['letters'] = letters
                json_data['number'] = temp_n[0]
        tag = letters + ',' + tag
        tag = tag.strip(',')

    # 添加字幕、马赛克信息到tag中
    has_sub = json_data['has_sub']
    mosaic = json_data['mosaic']
    if has_sub and 'cnword' in tag_include:
        tag += ',中文字幕'
    if mosaic and 'mosaic' in tag_include:
        tag += ',' + mosaic

    # 添加系列、制作、发行信息到tag中
    series = json_data['series']
    studio = json_data['studio']
    publisher = json_data['publisher']
    director = json_data['director']
    if not studio and publisher:
        studio = publisher
    if not publisher and studio:
        publisher = studio

    # 系列
    if series:  # 为空时会匹配所有
        if series_translate == 'on':  # 映射
            info_data = resources.get_info_data(series)
            series = info_data.get(series_language)
        if series and 'series' in tag_include:  # 写nfo
            nfo_tag_series = config.nfo_tag_series.replace('series', series)
            if nfo_tag_series:
                tag += f',{nfo_tag_series}'

    # 片商
    if studio:
        if studio_translate == 'on':
            info_data = resources.get_info_data(studio)
            studio = info_data.get(studio_language)
        if studio and 'studio' in tag_include:
            nfo_tag_studio = config.nfo_tag_studio.replace('studio', studio)
            if nfo_tag_studio:
                tag += f',{nfo_tag_studio}'

    # 发行
    if publisher:
        if publisher_translate == 'on':
            info_data = resources.get_info_data(publisher)
            publisher = info_data.get(publisher_language)
        if publisher and 'publisher' in tag_include:
            nfo_tag_publisher = config.nfo_tag_publisher.replace('publisher', publisher)
            if nfo_tag_publisher:
                tag += f',{nfo_tag_publisher}'

    # 导演
    if director:
        if director_translate == 'on':
            info_data = resources.get_info_data(director)
            director = info_data.get(director_language)

    if tag_language == 'zh_cn':
        tag = zhconv.convert(tag, 'zh-cn')
    else:
        tag = zhconv.convert(tag, 'zh-hant')

    # tag去重/去空/排序
    tag = remove_repeat(tag)

    json_data['tag'] = tag.strip(',')
    json_data['series'] = series
    json_data['studio'] = studio
    json_data['publisher'] = publisher
    json_data['director'] = director
    return json_data


def translate_actor(json_data):
    # 网络请求真实的演员名字
    actor_realname = config.actor_realname
    mosaic = json_data['mosaic']
    number = json_data['number']

    # 非读取模式，勾选了使用真实名字时; 读取模式，勾选了允许更新真实名字时
    if actor_realname == 'on':
        start_time = time.time()
        if mosaic != '国产' and (
                number.startswith('FC2') or number.startswith('SIRO') or re.search(r'\d{3,}[A-Z]{3,}-', number)):
            result, temp_actor = get_actorname(json_data['number'])
            if result:
                json_data['actor'] = temp_actor
                json_data[
                    'logs'] += f"\n 👩🏻 Av-wiki done! Actor's real Japanese name is '{temp_actor}' ({get_used_time(start_time)}s)"
            else:
                json_data['logs'] += f"\n 🔴 Av-wiki failed! {temp_actor} ({get_used_time(start_time)}s)"

    # 如果不映射，返回
    if config.actor_translate == 'off':
        return json_data

    # 映射表数据加载失败，返回
    xml_actor = resources.actor_mapping_data
    if len(xml_actor) == 0:
        return json_data

    # 未知演员，返回
    actor = json_data['actor']
    if "actor_all," in config.nfo_include_new:
        actor = json_data['all_actor']
    if actor == config.actor_no_name:
        return json_data

    # 查询映射表
    actor_list = actor.split(',')
    actor_new_list = []
    actor_href_list = []
    actor_language = config.actor_language
    for each_actor in actor_list:
        if each_actor:
            actor_data = resources.get_actor_data(each_actor)
            new_actor = actor_data.get(actor_language)
            if actor_language == 'zh_cn':
                new_actor = zhconv.convert(new_actor, 'zh-cn')
            elif actor_language == 'zh_tw':
                new_actor = zhconv.convert(new_actor, 'zh-hant')
            if new_actor not in actor_new_list:
                actor_new_list.append(new_actor)
                if actor_data.get('href'):
                    actor_href_list.append(actor_data.get('href'))
    json_data['actor'] = ','.join(actor_new_list)
    if "actor_all," in config.nfo_include_new:
        json_data['all_actor'] = ','.join(actor_new_list)

    # 演员主页
    if actor_href_list:
        json_data['actor_href'] = actor_href_list[0]
    elif json_data['actor']:
        json_data['actor_href'] = 'https://javdb.com/search?f=actor&q=' + \
                                  urllib.parse.quote(
                                      json_data['actor'].split(',')[0])  # url转码，避免乱码

    return json_data


def get_youdao_key():
    try:
        t = threading.Thread(target=_get_youdao_key_thread)
        t.start()  # 启动线程,即让线程开始执行
    except:
        signal.show_traceback_log(traceback.format_exc())
        signal.show_log_text(traceback.format_exc())


def _get_youdao_key_thread():
    # 获取 js url
    js_url = ''
    youdao_url = 'https://fanyi.youdao.com'
    result, req = get_html(youdao_url)
    if result:
        # https://shared.ydstatic.com/fanyi/newweb/v1.1.11/scripts/newweb/fanyi.min.js
        url_temp = re.search(r'(https://shared.ydstatic.com/fanyi/newweb/.+/scripts/newweb/fanyi.min.js)', req)
        if url_temp:
            js_url = url_temp.group(1)
    if not js_url:
        signal.show_log_text(' ⚠️ youdao js url get failed!!!')
        signal.show_traceback_log('youdao js url get failed!!!')
        return

    # 请求 js url ，获取 youdao key
    result, req = get_html(js_url)
    try:
        youdaokey = re.search(r'(?<="fanyideskweb" \+ e \+ i \+ ")[^"]+', req).group(0)
        # sign: n.md5("fanyideskweb" + e + i + "Ygy_4c=r#e#4EX^NUGUc5")
    except:
        try:
            youdaokey = re.search(r'(?<="fanyideskweb"\+e\+i\+")[^"]+', req).group(0)
        except Exception as e:
            youdaokey = "Ygy_4c=r#e#4EX^NUGUc5"
            signal.show_traceback_log(traceback.format_exc())
            signal.show_traceback_log('🔴 有道翻译接口key获取失败！' + str(e))
            signal.show_log_text(traceback.format_exc())
            signal.show_log_text(' 🔴 有道翻译接口key获取失败！请检查网页版有道是否正常！%s' % str(e))
    return youdaokey


def translate_title_outline(json_data, movie_number):
    title_language = config.title_language
    title_translate = config.title_translate
    outline_language = config.outline_language
    outline_translate = config.outline_translate
    translate_by = config.translate_by
    if title_language == 'jp' and outline_language == 'jp':
        return
    trans_title = ''
    trans_outline = ''
    title_sehua = config.title_sehua
    title_sehua_zh = config.title_sehua_zh
    title_yesjav = config.title_yesjav
    json_data_title_language = langid.classify(json_data['title'])[0]

    # 处理title
    if title_language != 'jp':
        movie_title = ''

        # 匹配本地高质量标题(色花标题数据)
        if title_sehua_zh == 'on' or (json_data_title_language == 'ja' and title_sehua == 'on'):
            start_time = time.time()
            try:
                movie_title = resources.sehua_title_data.get(movie_number)
            except:
                signal.show_traceback_log(traceback.format_exc())
                signal.show_log_text(traceback.format_exc())
            if movie_title:
                json_data['title'] = movie_title
                json_data['logs'] += '\n 🌸 Sehua title done!(%ss)' % (get_used_time(start_time))

        # 匹配网络高质量标题（yesjav， 可在线更新）
        if not movie_title and title_yesjav == 'on' and json_data_title_language == 'ja':
            start_time = time.time()
            movie_title = get_yesjav_title(json_data, movie_number)
            if movie_title and langid.classify(movie_title)[0] != 'ja':
                json_data['title'] = movie_title
                json_data['logs'] += '\n 🆈 Yesjav title done!(%ss)' % (get_used_time(start_time))

        # 使用json_data数据
        if not movie_title and title_translate == 'on' and json_data_title_language == 'ja':
            trans_title = json_data['title']

    # 处理outline
    if json_data['outline'] and outline_language != 'jp':
        if outline_translate == 'on' and langid.classify(json_data['outline'])[0] == 'ja':
            trans_outline = json_data['outline']

    # 翻译
    if Flags.translate_by_list:
        if (trans_title and title_translate == 'on') or (trans_outline and outline_translate == 'on'):
            start_time = time.time()
            translate_by_list = Flags.translate_by_list.copy()
            if not json_data['cd_part']:
                random.shuffle(translate_by_list)
            for each in translate_by_list:
                if each == 'youdao':  # 使用有道翻译
                    t, o, r = youdao_translate(trans_title, trans_outline)
                elif each == 'google':  # 使用 google 翻译
                    t, o, r = google_translate(trans_title, trans_outline)
                else:  # 使用deepl翻译
                    t, o, r = deepl_translate(trans_title, trans_outline, 'JA', json_data)
                if r:
                    json_data[
                        'logs'] += f'\n 🔴 Translation failed!({each.capitalize()})({get_used_time(start_time)}s) Error: {r}'
                else:
                    if t:
                        json_data['title'] = t
                    if o:
                        json_data['outline'] = o
                    json_data[
                        'logs'] += f'\n 🍀 Translation done!({each.capitalize()})({get_used_time(start_time)}s)'
                    json_data['outline_from'] = each
                    break
            else:
                translate_by = translate_by.strip(',').capitalize()
                json_data[
                    'logs'] += f'\n 🔴 Translation failed! {translate_by} 不可用！({get_used_time(start_time)}s)'

    # 简繁转换
    if title_language == 'zh_cn':
        json_data['title'] = zhconv.convert(json_data['title'], 'zh-cn')
    elif title_language == 'zh_tw':
        json_data['title'] = zhconv.convert(json_data['title'], 'zh-hant')
        json_data['mosaic'] = zhconv.convert(json_data['mosaic'], 'zh-hant')

    if outline_language == 'zh_cn':
        json_data['outline'] = zhconv.convert(json_data['outline'], 'zh-cn')
    elif outline_language == 'zh_tw':
        json_data['outline'] = zhconv.convert(json_data['outline'], 'zh-hant')

    return json_data
