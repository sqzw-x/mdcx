#!/usr/bin/env python3
import asyncio
import re
import socket
import threading
from io import BytesIO
from typing import List, Literal, Optional, Tuple, overload
from urllib.parse import quote

import requests
import urllib3.util.connection as urllib3_cn
from PIL import Image
from ping3 import ping

from ..config.manager import config
from ..signals import signal
from .utils import get_user_agent
from .web_sync import get_json_sync


def _allowed_gai_family():
    """
    https://github.com/shazow/urllib3/blob/master/urllib3/util/connection.py
    """
    family = socket.AF_INET
    return family


try:
    if config.ipv4_only:
        urllib3_cn.allowed_gai_family = _allowed_gai_family
except Exception:
    urllib3_cn.allowed_gai_family = _allowed_gai_family


def url_encode(url: str) -> str:
    new_url = ""
    for i in url:
        if i not in [":", "/", "&", "?", "=", "%"]:
            i = quote(i)
        new_url += i
    return new_url


@overload
async def check_url(url: str, length: Literal[False] = False, real_url: bool = False) -> Optional[str]: ...
@overload
async def check_url(url: str, length: Literal[True] = True, real_url: bool = False) -> Optional[int]: ...
async def check_url(url: str, length: bool = False, real_url: bool = False):
    """
    检测下载链接. 失败时返回 None.

    Args:
        url (str): 要检测的 URL
        length (bool, optional): 是否返回文件大小. Defaults to False.
        real_url (bool, optional): 直接返回真实 URL 不进行后续检查. Defaults to False.
    """
    if not url:
        return

    if "http" not in url:
        signal.add_log(f"🔴 检测链接失败: 格式错误 {url}")
        return

    try:
        # 使用 request 方法发送 HEAD 请求
        response, error = await config.async_client.request("HEAD", url)

        # 处理请求失败的情况
        if response is None:
            signal.add_log(f"🔴 检测链接失败: {error}")
            return

        # 不输出获取 dmm预览视频(trailer) 最高分辨率的测试结果到日志中
        if response.status_code == 404 and "_w.mp4" in url:
            return

        # 返回重定向的url
        true_url = str(response.url)
        if real_url:
            return true_url

        # 检查是否需要登录
        if "login" in true_url:
            signal.add_log(f"🔴 检测链接失败: 需登录 {true_url}")
            return

        # 检查是否带有图片不存在的关键词
        bad_url_keys = ["now_printing", "nowprinting", "noimage", "nopic", "media_violation"]
        for each_key in bad_url_keys:
            if each_key in true_url:
                signal.add_log(f"🔴 检测链接失败: 图片已被网站删除 {url}")
                return

        # 获取文件大小
        content_length = response.headers.get("Content-Length")
        if not content_length:
            # 如果没有获取到文件大小，尝试下载数据
            content, error = await config.async_client.get_content(true_url)

            if content is not None and len(content) > 0:
                signal.add_log(f"✅ 检测链接通过: 预下载成功 {true_url}")
                return 10240 if length else true_url
            else:
                signal.add_log(f"🔴 检测链接失败: 未返回大小且预下载失败 {true_url}")
                return
        # 如果返回内容的文件大小 < 8k，视为不可用
        elif int(content_length) < 8192:
            signal.add_log(f"🔴 检测链接失败: 返回大小({content_length}) < 8k {true_url}")
            return

        signal.add_log(f"✅ 检测链接通过: 返回大小({content_length}) {true_url}")
        return int(content_length) if length else true_url

    except Exception as e:
        signal.add_log(f"🔴 检测链接失败: 未知异常 {e} {url}")
        return


async def get_avsox_domain() -> str:
    issue_url = "https://tellme.pw/avsox"
    response, error = await config.async_client.get_text(issue_url)
    domain = "https://avsox.click"
    if response is not None:
        res = re.findall(r'(https://[^"]+)', response)
        for s in res:
            if s and "https://avsox.com" not in s or "api.qrserver.com" not in s:
                return s
    return domain


async def get_amazon_data(req_url: str) -> Tuple[bool, str]:
    """
    获取 Amazon 数据
    """
    headers = {
        "accept-encoding": "gzip, deflate, br",
        "Host": "www.amazon.co.jp",
        "User-Agent": get_user_agent(),
    }
    html_info, error = await config.async_client.get_text(req_url, encoding="Shift_JIS")
    if html_info is None:
        html_info, error = await config.async_client.get_text(req_url, headers=headers, encoding="Shift_JIS")
    if html_info is None:
        session_id = ""
        ubid_acbjp = ""
        if x := re.findall(r'sessionId: "([^"]+)', html_info or ""):
            session_id = x[0]
        if x := re.findall(r"ubid-acbjp=([^ ]+)", html_info or ""):
            ubid_acbjp = x[0]
        headers_o = {
            "cookie": f"session-id={session_id}; ubid_acbjp={ubid_acbjp}",
        }
        headers.update(headers_o)
        html_info, error = await config.async_client.get_text(req_url, headers=headers, encoding="Shift_JIS")
    if html_info is None:
        return False, error
    if "HTTP 503" in html_info:
        headers = {
            "Host": "www.amazon.co.jp",
            "User-Agent": get_user_agent(),
        }
        html_info, error = await config.async_client.get_text(req_url, headers=headers, encoding="Shift_JIS")
    if html_info is None:
        return False, error
    return True, html_info


async def get_imgsize(url) -> tuple[int, int]:
    response, err = await config.async_client.request("GET", url, stream=True)
    if response is None or response.status_code != 200:
        return 0, 0
    file_head = BytesIO()
    chunk_size = 1024 * 10
    for chunk in response.iter_content(chunk_size):
        file_head.write(chunk)
        response.close()
        try:

            def _get_size():
                return Image.open(file_head).size

            await asyncio.to_thread(_get_size)
        except Exception:
            return 0, 0
    return 0, 0


async def get_dmm_trailer(trailer_url):
    """
    异步版本的 get_dmm_trailer 函数
    如果预览片地址为 dmm ，尝试获取 dmm 预览片最高分辨率

    Args:
        trailer_url (str): 预览片地址

    Returns:
        str: 最高分辨率的预览片地址
    """
    # 如果不是DMM域名或已经是最高分辨率，则直接返回
    if ".dmm.co" not in trailer_url or "_mhb_w.mp4" in trailer_url:
        return trailer_url

    # 将相对URL转换为绝对URL
    if trailer_url.startswith("//"):
        trailer_url = "https:" + trailer_url

    """
    DMM预览片分辨率对应关系:
    '_sm_w.mp4': 320*180, 3.8MB     # 最低分辨率
    '_dm_w.mp4': 560*316, 10.1MB    # 中等分辨率
    '_dmb_w.mp4': 720*404, 14.6MB   # 次高分辨率
    '_mhb_w.mp4': 720*404, 27.9MB   # 最高分辨率
    
    示例:
    https://cc3001.dmm.co.jp/litevideo/freepv/s/ssi/ssis00090/ssis00090_sm_w.mp4
    https://cc3001.dmm.co.jp/litevideo/freepv/s/ssi/ssis00090/ssis00090_dm_w.mp4
    https://cc3001.dmm.co.jp/litevideo/freepv/s/ssi/ssis00090/ssis00090_dmb_w.mp4
    https://cc3001.dmm.co.jp/litevideo/freepv/s/ssi/ssis00090/ssis00090_mhb_w.mp4
    """

    # 解析URL获取基础部分和当前分辨率标识
    pattern = r"(.+)(_[sd]mb?_w.mp4)"
    match = re.findall(pattern, trailer_url)
    if not match:
        return trailer_url

    # 解析URL基础部分和分辨率标识
    base_url, resolution_tag = match[0]

    # 构建各种分辨率的URL
    resolutions = {
        "_mhb_w.mp4": base_url + "_mhb_w.mp4",  # 最高分辨率
        "_dmb_w.mp4": base_url + "_dmb_w.mp4",  # 次高分辨率
        "_dm_w.mp4": base_url + "_dm_w.mp4",  # 中等分辨率
    }

    # 根据当前分辨率选择检查策略
    check_list = []
    if resolution_tag == "_dmb_w.mp4":
        # 已经是次高分辨率，只需检查最高分辨率
        check_list = ["_mhb_w.mp4"]
    elif resolution_tag == "_dm_w.mp4":
        # 中等分辨率，按优先级检查最高和次高分辨率
        check_list = ["_mhb_w.mp4", "_dmb_w.mp4"]
    elif resolution_tag == "_sm_w.mp4":
        # 最低分辨率，按优先级检查所有更高分辨率
        check_list = ["_mhb_w.mp4", "_dmb_w.mp4", "_dm_w.mp4"]

    # 按优先级检查更高分辨率
    for res_key in check_list:
        if await check_url(resolutions[res_key]):
            return resolutions[res_key]

    # 如果所有检查都失败，则返回原始URL
    return trailer_url


def _ping_host_thread(host_address: str, result_list: List[Optional[int]], i: int) -> None:
    response = ping(host_address, timeout=1)
    result_list[i] = int(response * 1000) if response else 0


def ping_host(host_address: str) -> str:
    count = config.retry
    result_list: List[Optional[int]] = [None] * count
    thread_list: List[threading.Thread] = [None] * count  # type: ignore # todo
    for i in range(count):
        thread_list[i] = threading.Thread(target=_ping_host_thread, args=(host_address, result_list, i))
        thread_list[i].start()
    for i in range(count):
        thread_list[i].join()
    new_list = [each for each in result_list if each]
    return (
        f"  ⏱ Ping {int(sum(new_list) / len(new_list))} ms ({len(new_list)}/{count})"
        if new_list
        else f"  🔴 Ping - ms (0/{count})"
    )


def check_version() -> Optional[int]:
    if config.update_check:
        url = "https://api.github.com/repos/sqzw-x/mdcx/releases/latest"
        res_json, error = get_json_sync(url)
        if res_json is not None:
            try:
                latest_version = res_json["tag_name"]
                latest_version = int(latest_version)
                return latest_version
            except Exception:
                signal.add_log(f"❌ 获取最新版本失败！{res_json}")
    return None


def check_theporndb_api_token() -> str:
    tips = "✅ 连接正常! "
    headers = config.headers
    proxies = config.proxies
    timeout = config.timeout
    api_token = config.theporndb_api_token
    url = "https://api.theporndb.net/scenes/hash/8679fcbdd29fa735"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": get_user_agent(),
    }
    if not api_token:
        tips = "❌ 未填写 API Token，影响欧美刮削！可在「设置」-「网络」添加！"
    else:
        try:
            response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout, verify=False)
            if response.status_code == 401 and "Unauthenticated" in str(response.text):
                tips = "❌ API Token 错误！影响欧美刮削！请到「设置」-「网络」中修改。"
            elif response.status_code == 200:
                if response.json().get("data"):
                    tips = "✅ 连接正常！"
                else:
                    tips = "❌ 返回数据异常！"
            else:
                tips = f"❌ 连接失败！请检查网络或代理设置！ {response.status_code} {response.text}"
        except Exception as e:
            tips = f"❌ 连接失败!请检查网络或代理设置！ {e}"
    signal.show_log_text(tips.replace("❌", " ❌ ThePornDB").replace("✅", " ✅ ThePornDB"))
    return tips


async def _get_pic_by_google(pic_url):
    google_keyused = config.google_keyused
    google_keyword = config.google_keyword
    req_url = f"https://www.google.com/searchbyimage?sbisrc=2&image_url={pic_url}"
    # req_url = f'https://lens.google.com/uploadbyurl?url={pic_url}&hl=zh-CN&re=df&ep=gisbubu'
    response, error = await config.async_client.get_text(req_url)
    big_pic = True
    if response is None:
        return "", "", ""
    url_list = re.findall(r'a href="([^"]+isz:l[^"]+)">', response)
    url_list_middle = re.findall(r'a href="([^"]+isz:m[^"]+)">', response)
    if not url_list and url_list_middle:
        url_list = url_list_middle
        big_pic = False
    if url_list:
        req_url = "https://www.google.com" + url_list[0].replace("amp;", "")
        response, error = await config.async_client.get_text(req_url)
    if response is None:
        return "", "", ""
    url_list = re.findall(r'\["(http[^"]+)",(\d{3,4}),(\d{3,4})\],[^[]', response)
    # 优先下载放前面
    new_url_list = []
    for each_url in url_list.copy():
        if int(each_url[2]) < 800:
            url_list.remove(each_url)

    for each_key in google_keyused:
        for each_url in url_list.copy():
            if each_key in each_url[0]:
                new_url_list.append(each_url)
                url_list.remove(each_url)
    # 只下载关时，追加剩余地址
    if "goo_only" not in config.download_hd_pics:
        new_url_list += url_list
    # 解析地址
    for each in new_url_list:
        temp_url = each[0]
        for temp_keyword in google_keyword:
            if temp_keyword in temp_url:
                break
        else:
            h = int(each[1])
            w = int(each[2])
            if w > h and w / h < 1.4:  # thumb 被拉高时跳过
                continue

            p_url = temp_url.encode("utf-8").decode("unicode_escape")  # url中的Unicode字符转义，不转义，url请求会失败
            if "m.media-amazon.com" in p_url:
                p_url = re.sub(r"\._[_]?AC_[^\.]+\.", ".", p_url)
                pic_size = await get_imgsize(p_url)
                if pic_size[0]:
                    return p_url, pic_size, big_pic
            else:
                url = await check_url(p_url)
                if url:
                    pic_size = (w, h)
                    return url, pic_size, big_pic
    return "", "", ""


async def get_big_pic_by_google(pic_url, poster=False):
    url, pic_size, big_pic = await _get_pic_by_google(pic_url)
    if not poster:
        if big_pic or (
            pic_size and int(pic_size[0]) > 800 and int(pic_size[1]) > 539
        ):  # cover 有大图时或者图片高度 > 800 时使用该图片
            return url, pic_size
        return "", ""
    if url and int(pic_size[1]) < 1000:  # poster，图片高度小于 1500，重新搜索一次
        url, pic_size, big_pic = await _get_pic_by_google(url)
    if pic_size and (
        big_pic or "blogger.googleusercontent.com" in url or int(pic_size[1]) > 560
    ):  # poster，大图或高度 > 560 时，使用该图片
        return url, pic_size
    else:
        return "", ""
