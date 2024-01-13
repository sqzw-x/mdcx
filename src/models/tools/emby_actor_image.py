import base64
import json
import os
import re
import time
import traceback

import requests
from lxml import etree

from models.base.image import cut_pic, fix_pic
from models.base.utils import get_used_time
from models.base.web import get_html
from models.config.config import config
from models.config.resources import resources
from models.core.web import download_file_with_filepath
from models.signals import signal


def update_emby_actor_photo():
    signal.change_buttons_status.emit()
    server_type = config.server_type
    if 'emby' in server_type:
        signal.show_log_text("👩🏻 开始补全 Emby 演员头像...")
    else:
        signal.show_log_text("👩🏻 开始补全 Jellyfin 演员头像...")
    actor_list = _get_emby_actor_list()
    if actor_list:
        gfriends_actor_data = _get_gfriends_actor_data()
        if gfriends_actor_data:
            _update_emby_actor_photo_execute(actor_list, gfriends_actor_data)
    signal.reset_buttons_status.emit()


def _get_emby_actor_list():
    # 获取 emby 的演员列表
    if 'emby' in config.server_type:
        server_name = 'Emby'
        url = config.emby_url + '/emby/Persons?api_key=' + config.api_key
        # http://192.168.5.191:8096/emby/Persons?api_key=ee9a2f2419704257b1dd60b975f2d64e
        # http://192.168.5.191:8096/emby/Persons/梦乃爱华?api_key=ee9a2f2419704257b1dd60b975f2d64e
    else:
        server_name = 'Jellyfin'
        url = config.emby_url + '/Persons?api_key=' + config.api_key

    if config.user_id:
        url += f'&userid={config.user_id}'

    signal.show_log_text(f"⏳ 连接 {server_name} 服务器...")

    if config.emby_url == '':
        signal.show_log_text(f'🔴 {server_name} 地址未填写！')
        signal.show_log_text("================================================================================")
    if config.api_key == '':
        signal.show_log_text(f'🔴 {server_name} API 密钥未填写！')
        signal.show_log_text("================================================================================")

    result, response = get_html(url, proxies=False, json_data=True)
    if not result:
        signal.show_log_text(
            f'🔴 {server_name} 连接失败！请检查 {server_name} 地址 和 API 密钥是否正确填写！ {response}')
        signal.show_log_text(traceback.format_exc())

    actor_list = response['Items']
    signal.show_log_text(f"✅ {server_name} 连接成功！共有 {len(actor_list)} 个演员！")
    if not actor_list:
        signal.show_log_text("================================================================================")
    return actor_list


def _upload_actor_photo(url, pic_path):
    try:
        with open(pic_path, 'rb') as f:
            b6_pic = base64.b64encode(f.read())  # 读取文件内容, 转换为base64编码

        if pic_path.endswith('jpg'):
            header = {
                "Content-Type": 'image/jpeg',
            }
        else:
            header = {
                "Content-Type": 'image/png',
            }
        requests.post(url=url, data=b6_pic, headers=header)
        return True
    except:
        signal.show_log_text(traceback.format_exc())
        return False


def _generate_server_url(actor_js):
    server_type = config.server_type
    emby_url = config.emby_url
    api_key = config.api_key
    actor_name = actor_js['Name'].replace(' ', '%20')
    actor_id = actor_js['Id']
    server_id = actor_js['ServerId']

    if 'emby' in server_type:
        actor_homepage = f"{emby_url}/web/index.html#!/item?id={actor_id}&serverId={server_id}"
        actor_person = f'{emby_url}/emby/Persons/{actor_name}?api_key={api_key}'
        pic_url = f"{emby_url}/emby/Items/{actor_id}/Images/Primary?api_key={api_key}"
        backdrop_url = f"{emby_url}/emby/Items/{actor_id}/Images/Backdrop?api_key={api_key}"
        backdrop_url_0 = f"{emby_url}/emby/Items/{actor_id}/Images/Backdrop/0?api_key={api_key}"
        update_url = f"{emby_url}/emby/Items/{actor_id}?api_key={api_key}"
    else:
        actor_homepage = f"{emby_url}/web/index.html#!/details?id={actor_id}&serverId={server_id}"
        actor_person = f'{emby_url}/Persons/{actor_name}?api_key={api_key}'
        pic_url = f"{emby_url}/Items/{actor_id}/Images/Primary?api_key={api_key}"
        backdrop_url = f"{emby_url}/Items/{actor_id}/Images/Backdrop?api_key={api_key}"
        backdrop_url_0 = f"{emby_url}/Items/{actor_id}/Images/Backdrop/0?api_key={api_key}"
        update_url = f"{emby_url}/Items/{actor_id}?api_key={api_key}"
        # http://192.168.5.191:8097/Items/f840883833eaaebd915822f5f39e945b/Images/Primary?api_key=9e0fce1acde54158b0d4294731ff7a46
        # http://192.168.5.191:8097/Items/f840883833eaaebd915822f5f39e945b/Images/Backdrop?api_key=9e0fce1acde54158b0d4294731ff7a46
    return actor_homepage, actor_person, pic_url, backdrop_url, backdrop_url_0, update_url


def _get_gfriends_actor_data():
    emby_on = config.emby_on
    gfriends_github = config.gfriends_github
    raw_url = f'{gfriends_github}'.replace('github.com/', 'raw.githubusercontent.com/').replace('://www.', '://')
    # 'https://raw.githubusercontent.com/gfriends/gfriends'

    if 'actor_photo_net' in emby_on:
        update_data = False
        signal.show_log_text('⏳ 连接 Gfriends 网络头像库...')
        net_url = f'{gfriends_github}/commits/master/Filetree.json'
        result, response = get_html(net_url)
        if not result:
            signal.show_log_text('🔴 Gfriends 查询最新数据更新时间失败！')
            net_float = 0
            update_data = True
        else:
            try:
                date_time = re.findall(r'committedDate":"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', response)
                lastest_time = time.strptime(date_time[0], '%Y-%m-%dT%H:%M:%S')
                net_float = time.mktime(lastest_time) - time.timezone
                net_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(net_float))
            except:
                signal.show_log_text('🔴 Gfriends 历史页面解析失败！请向开发者报告! ')
                return False
            signal.show_log_text(f'✅ Gfriends 连接成功！最新数据更新时间: {net_time}')

        # 更新：本地无文件时；更新时间过期；本地文件读取失败时，重新更新
        gfriends_json_path = resources.userdata_path('gfriends.json')
        if not os.path.exists(gfriends_json_path) or os.path.getmtime(gfriends_json_path) < 1657285200:
            update_data = True
        else:
            try:
                with open(gfriends_json_path, 'r', encoding='utf-8') as f:
                    gfriends_actor_data = json.load(f)
            except:
                signal.show_log_text('🔴 本地缓存数据读取失败！需重新缓存！')
                update_data = True
            else:
                local_float = os.path.getmtime(gfriends_json_path)
                local_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(local_float))
                if not net_float or net_float > local_float:
                    signal.show_log_text(f'🍉 本地缓存数据需要更新！本地数据更新时间: {local_time}')
                    update_data = True
                else:
                    signal.show_log_text(f'✅ 本地缓存数据无需更新！本地数据更新时间: {local_time}')
                    return gfriends_actor_data

        # 更新数据
        if update_data:
            signal.show_log_text('⏳ 开始缓存 Gfriends 最新数据表...')
            filetree_url = f'{raw_url}/master/Filetree.json'
            result, response = get_html(filetree_url, content=True)
            if not result:
                signal.show_log_text('🔴 Gfriends 数据表获取失败！补全已停止！')
                return False
            with open(gfriends_json_path, "wb") as f:
                f.write(response)
            signal.show_log_text('✅ Gfriends 数据表已缓存！')
            try:
                with open(gfriends_json_path, 'r', encoding='utf-8') as f:
                    gfriends_actor_data = json.load(f)
            except:
                signal.show_log_text('🔴 本地缓存数据读取失败！补全已停止！')
                return False
            else:
                content = gfriends_actor_data.get('Content')
                new_gfriends_actor_data = {}
                content_list = list(content.keys())
                content_list.sort()
                for each_key in content_list:
                    for key, value in content.get(each_key).items():
                        if key not in new_gfriends_actor_data:
                            # https://raw.githubusercontent.com/gfriends/gfriends/master/Content/z-Derekhsu/%E5%A4%A2%E4%B9%83%E3%81%82%E3%81%84%E3%81%8B.jpg
                            actor_url = f'{raw_url}/master/Content/{each_key}/{value}'
                            new_gfriends_actor_data[key] = actor_url
                with open(gfriends_json_path, 'w', encoding='utf-8') as f:
                    json.dump(
                        new_gfriends_actor_data,
                        f,
                        ensure_ascii=False,
                        sort_keys=True,
                        indent=4,
                        separators=(',', ': '),
                    )
                return new_gfriends_actor_data
    else:
        return _get_local_actor_photo()


def _get_graphis_pic(actor_name):
    emby_on = config.emby_on

    # 生成图片路径和请求地址
    actor_folder = resources.userdata_path('actor/graphis')
    pic_old = os.path.join(actor_folder, f'{actor_name}-org-old.jpg')
    fix_old = os.path.join(actor_folder, f'{actor_name}-fix-old.jpg')
    big_old = os.path.join(actor_folder, f'{actor_name}-big-old.jpg')
    pic_new = os.path.join(actor_folder, f'{actor_name}-org-new.jpg')
    fix_new = os.path.join(actor_folder, f'{actor_name}-fix-new.jpg')
    big_new = os.path.join(actor_folder, f'{actor_name}-big-new.jpg')
    if 'graphis_new' in emby_on:
        pic_path = pic_new
        backdrop_path = big_new
        if 'graphis_backgrop' not in emby_on:
            backdrop_path = fix_new
        url = f'https://graphis.ne.jp/monthly/?K={actor_name}'
    else:
        pic_path = pic_old
        backdrop_path = big_old
        if 'graphis_backgrop' not in emby_on:
            backdrop_path = fix_old
        url = f'https://graphis.ne.jp/monthly/?S=1&K={actor_name}'
        # https://graphis.ne.jp/monthly/?S=1&K=夢乃あいか

    # 查看本地有没有缓存
    logs = ''
    has_pic = False
    has_backdrop = False
    if os.path.isfile(pic_path):
        has_pic = True
    if os.path.isfile(backdrop_path):
        has_backdrop = True
    if 'graphis_face' not in emby_on:
        pic_path = ''
        if has_backdrop:
            logs += '✅ graphis.ne.jp 本地背景！ '
            return '', backdrop_path, logs
    elif 'graphis_backdrop' not in emby_on:
        if has_pic:
            logs += '✅ graphis.ne.jp 本地头像！ '
            return pic_path, '', logs
    elif has_pic and has_backdrop:
        return pic_path, backdrop_path, ''

    # 请求图片
    result, res = get_html(url)
    if not result:
        logs += f'🔴 graphis.ne.jp 请求失败！\n{res}'
        return '', '', logs
    html = etree.fromstring(res, etree.HTMLParser())
    src = html.xpath("//div[@class='gp-model-box']/ul/li/a/img/@src")
    jp_name = html.xpath("//li[@class='name-jp']/span/text()")
    if actor_name not in jp_name:
        # logs += '🍊 graphis.ne.jp 无结果！'
        return '', '', logs
    small_pic = src[jp_name.index(actor_name)]
    big_pic = small_pic.replace('/prof.jpg', '/model.jpg')

    # 保存图片
    if not has_pic and pic_path:
        if download_file_with_filepath({'logs': ''}, small_pic, pic_path, actor_folder):
            logs += '🍊 使用 graphis.ne.jp 头像！ '
            if 'graphis_backdrop' not in emby_on:
                if not has_backdrop:
                    fix_pic(pic_path, backdrop_path)
                return pic_path, backdrop_path, logs
        else:
            logs += '🔴 graphis.ne.jp 头像获取失败！ '
            pic_path = ''
    if not has_backdrop and 'graphis_backdrop' in emby_on:
        if download_file_with_filepath({'logs': ''}, big_pic, backdrop_path, actor_folder):
            logs += '🍊 使用 graphis.ne.jp 背景！ '
            fix_pic(backdrop_path, backdrop_path)
        else:
            logs += '🔴 graphis.ne.jp 背景获取失败！ '
            backdrop_path = ''
    return pic_path, backdrop_path, logs


def _update_emby_actor_photo_execute(actor_list, gfriends_actor_data):
    start_time = time.time()
    emby_on = config.emby_on
    actor_folder = resources.userdata_path('actor')

    i = 0
    succ = 0
    fail = 0
    skip = 0
    count_all = len(actor_list)
    for actor_js in actor_list:
        i += 1
        deal_percent = '{:.2%}'.format(i / count_all)
        # Emby 有头像时处理
        actor_name = actor_js['Name']
        actor_imagetages = actor_js["ImageTags"]
        actor_backdrop_imagetages = actor_js["BackdropImageTags"]
        if ' ' in actor_name:
            skip += 1
            continue
        actor_homepage, actor_person, pic_url, backdrop_url, backdrop_url_0, update_url = _generate_server_url(actor_js)
        if actor_imagetages and 'actor_photo_miss' in emby_on:
            # self.show_log_text(f'\n{deal_percent} ✅ {i}/{count_all} 已有头像！跳过！ 👩🏻 {actor_name} \n{actor_homepage}')
            skip += 1
            continue

        # 获取演员日文名字
        actor_name_data = resources.get_actor_data(actor_name)
        has_name = actor_name_data['has_name']
        jp_name = actor_name
        if has_name:
            jp_name = actor_name_data['jp']

        # graphis 判断
        pic_path, backdrop_path, logs = '', '', ''
        if 'actor_photo_net' in emby_on and has_name:
            if 'graphis_backdrop' in emby_on or 'graphis_face' in emby_on:
                pic_path, backdrop_path, logs = _get_graphis_pic(jp_name)

        # 要上传的头像图片未找到时
        if not pic_path:
            pic_path = gfriends_actor_data.get(f'{jp_name}.jpg')
            if not pic_path:
                pic_path = gfriends_actor_data.get(f'{jp_name}.png')
                if not pic_path:
                    if actor_imagetages:
                        signal.show_log_text(
                            f'\n{deal_percent} ✅ {i}/{count_all} 没有找到头像！继续使用原有头像！ 👩🏻 {actor_name} {logs}\n{actor_homepage}')
                        succ += 1
                        continue
                    signal.show_log_text(
                        f'\n{deal_percent} 🔴 {i}/{count_all} 没有找到头像！ 👩🏻 {actor_name}  {logs}\n{actor_homepage}')
                    fail += 1
                    continue
        else:
            pass

        # 头像需要下载时
        if 'https://' in pic_path:
            file_name = pic_path.split('/')[-1]
            file_name = re.findall(r'^[^?]+', file_name)[0]
            file_path = os.path.join(actor_folder, file_name)
            if not os.path.isfile(file_path):
                if not download_file_with_filepath({'logs': ''}, pic_path, file_path, actor_folder):
                    signal.show_log_text(
                        f'\n{deal_percent} 🔴 {i}/{count_all} 头像下载失败！ 👩🏻 {actor_name}  {logs}\n{actor_homepage}')
                    fail += 1
                    continue
            pic_path = file_path

        # 检查背景是否存在
        if not backdrop_path:
            backdrop_path = pic_path.replace('.jpg', '-big.jpg')
            if not os.path.isfile(backdrop_path):
                fix_pic(pic_path, backdrop_path)

        # 检查图片尺寸并裁剪为2:3
        cut_pic(pic_path)

        # 清理旧图片（backdrop可以多张，不清理会一直累积）
        if actor_backdrop_imagetages:
            for _ in range(len(actor_backdrop_imagetages)):
                requests.delete(backdrop_url_0)

        # 上传头像到 emby
        if _upload_actor_photo(pic_url, pic_path) and _upload_actor_photo(backdrop_url, backdrop_path):
            if not logs or logs == '🍊 graphis.ne.jp 无结果！':
                if 'actor_photo_net' in config.emby_on:
                    logs += ' ✅ 使用 Gfriends 头像和背景！'
                else:
                    logs += ' ✅ 使用本地头像库头像和背景！'
            signal.show_log_text(
                f'\n{deal_percent} ✅ {i}/{count_all} 头像更新成功！ 👩🏻 {actor_name}  {logs}\n{actor_homepage}')
            succ += 1
        else:
            signal.show_log_text(
                f'\n{deal_percent} 🔴 {i}/{count_all} 头像上传失败！ 👩🏻 {actor_name}  {logs}\n{actor_homepage}')
            fail += 1
    signal.show_log_text(
        f'\n\n 🎉🎉🎉 演员头像补全完成！用时: {get_used_time(start_time)}秒 成功: {succ} 失败: {fail} 跳过: {skip}\n')


def _get_local_actor_photo():
    actor_photo_folder = config.actor_photo_folder
    if actor_photo_folder == '' or not os.path.isdir(actor_photo_folder):
        signal.show_log_text('🔴 本地头像库文件夹不存在！补全已停止！')
        signal.show_log_text("================================================================================")
        return False
    else:
        local_actor_photo_dic = {}
        all_files = os.walk(actor_photo_folder)
        for root, dirs, files in all_files:
            for file in files:
                if file.endswith('jpg') or file.endswith('png'):
                    if file not in local_actor_photo_dic:
                        pic_path = os.path.join(root, file)
                        local_actor_photo_dic[file] = pic_path

        if not local_actor_photo_dic:
            signal.show_log_text('🔴 本地头像库文件夹未发现头像图片！请把图片放到文件夹中！')
            signal.show_log_text("================================================================================")
            return False
        return local_actor_photo_dic

if __name__ == '__main__':
    _get_gfriends_actor_data()