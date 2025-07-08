#!/usr/bin/env python3
import re
import threading
from io import BytesIO
from typing import List, Optional, Tuple, Union
from urllib.parse import quote

import requests
import urllib3.util.connection as urllib3_cn
from PIL import Image
from ping3 import ping
from requests.exceptions import (
    ChunkedEncodingError,
    ConnectionError,
    ConnectTimeout,
    ContentDecodingError,
    HTTPError,
    InvalidHeader,
    InvalidProxyURL,
    InvalidURL,
    ProxyError,
    ReadTimeout,
    SSLError,
    StreamConsumedError,
    Timeout,
    TooManyRedirects,
    URLRequired,
)

from ..config.manager import config
from ..signals import signal
from .utils import get_user_agent
from .web_sync import get_json, get_text


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


def check_url(url: str, length: bool = False, real_url: bool = False) -> Union[int, str]:
    proxies = config.proxies
    timeout = config.timeout
    retry_times = config.retry
    headers = config.headers

    if not url:
        return 0

    signal.add_log(f"⛑️ 检测链接 {url}")
    if "http" not in url:
        signal.add_log(f"🔴 检测未通过！链接格式错误！ {url}")
        return 0

    if "getchu" in url:
        headers_o = {
            "Referer": "http://www.getchu.com/top.html",
        }
        headers.update(headers_o)
    # javbus封面图需携带refer，refer似乎没有做强校验，但须符合格式要求，否则403
    elif "javbus" in url:
        headers_o = {
            "Referer": "https://www.javbus.com/",
        }
        headers.update(headers_o)

    for j in range(retry_times):
        try:
            r = requests.head(
                url, headers=headers, proxies=proxies, timeout=timeout, verify=False, allow_redirects=True
            )

            # 不输出获取 dmm预览视频(trailer) 最高分辨率的测试结果到日志中
            # get_dmm_trailer() 函数在多条错误的链接中找最高分辨率的链接，错误没有必要输出，避免误解为网络或软件问题
            if r.status_code == 404 and "_w.mp4" in url:
                if j + 1 < retry_times:
                    continue
                else:
                    return 0

            # 状态码 > 299，表示请求失败，视为不可用
            if r.status_code > 299:
                error_info = f"{r.status_code} {url}"
                signal.add_log(f"🔴 请求失败！ 重试: [{j + 1}/{retry_times}] {error_info}")
                continue

            # 返回重定向的url
            true_url = r.url
            if real_url:
                return true_url

            # 检查是否需要登录 https://lookaside.fbsbx.com/lookaside/crawler/media/?media_id=637921621668064
            if "login" in true_url:
                signal.add_log(f"🔴 检测未通过！需要登录查看 {true_url}")
                return 0

            # 检查是否带有图片不存在的关键词
            """
            如果跳转后的真实链接存在删图标识，视为不可用
            https://pics.dmm.co.jp/mono/movie/n/now_printing/now_printing.jpg dmm 删图的标识，javbus、javlib 用的是 dmm 图
            https://static.mgstage.com/mgs/img/common/actress/nowprinting.jpg mgstage 删图的标识
            https://jdbimgs.com/images/noimage_600x404.jpg javdb删除的图 WANZ-921
            https://www.javbus.com/imgs/cover/nopic.jpg
            https://assets.tumblr.com/images/media_violation/community_guidelines_v1_1280.png tumblr删除的图
            """
            bad_url_keys = ["now_printing", "nowprinting", "noimage", "nopic", "media_violation"]
            for each_key in bad_url_keys:
                if each_key in true_url:
                    signal.add_log(f"🔴 检测未通过！当前图片已被网站删除 {url}")
                    return 0

            # 获取文件大小。如果没有获取到文件大小，尝试下载15k数据，如果失败，视为不可用
            content_length = r.headers.get("Content-Length")
            if not content_length:
                response = requests.get(
                    true_url, headers=headers, proxies=proxies, timeout=timeout, verify=False, stream=True
                )
                i = 0
                chunk_size = 5120
                for _ in response.iter_content(chunk_size):
                    i += 1
                    if i == 3:
                        response.close()
                        signal.add_log(f"✅ 检测通过！未返回大小，预下载15k通过 {true_url}")
                        return 10240 if length else true_url
                signal.add_log(f"🔴 检测未通过！未返回大小，预下载15k失败 {true_url}")
                return 0

            # 如果返回内容的文件大小 < 8k，视为不可用
            elif int(content_length) < 8192:
                signal.add_log(f"🔴 检测未通过！返回大小({content_length}) < 8k {true_url}")
                return 0
            signal.add_log(f"✅ 检测通过！返回大小({content_length}) {true_url}")
            return int(content_length) if length else true_url
        except InvalidProxyURL as e:
            error_info = f" 无效的代理链接 ({e}) {url}"
        except ProxyError as e:
            error_info = f" 代理错误 {e} {url}"
        except SSLError as e:
            error_info = f" SSL错误 ({e}) {url}"
        except ConnectTimeout as e:
            error_info = f" 尝试连接到远程服务器时超时 ({e}) {url}"
        except ReadTimeout as e:
            error_info = f" 服务器未在分配的时间内发送任何数据 ({e}) {url}"
        except Timeout as e:
            error_info = f" 请求超时错误 ({e}) {url}"
        except ConnectionError as e:
            error_info = f" 连接错误 {e} {url}"
        except URLRequired as e:
            error_info = f" URL格式错误 ({e}) {url}"
        except TooManyRedirects as e:
            error_info = f" 过多的重定向 ({e}) {url}"
        except InvalidURL as e:
            error_info = f" 无效的url ({e}) {url}"
        except InvalidHeader as e:
            error_info = f" 无效的请求头 ({e}) {url}"
        except HTTPError as e:
            error_info = f" HTTP错误 {e} {url}"
        except ChunkedEncodingError as e:
            error_info = f" 服务器声明了分块编码，但发送了无效的分块 ({e}) {url}"
        except ContentDecodingError as e:
            error_info = f" 解码响应内容失败 ({e}) {url}"
        except StreamConsumedError as e:
            error_info = f" 该响应的内容已被占用 ({e}) {url}"
        except Exception as e:
            error_info = f" Error ({e}) {url}"
        signal.add_log(f"🔴 重试 [{j + 1}/{retry_times}] {error_info}")
    signal.add_log(f"🔴 检测未通过！ {url}")
    return 0


def get_avsox_domain() -> str:
    issue_url = "https://tellme.pw/avsox"
    response, error = get_text(issue_url)
    domain = "https://avsox.click"
    if response is not None:
        res = re.findall(r'(https://[^"]+)', response)
        for s in res:
            if s and "https://avsox.com" not in s or "api.qrserver.com" not in s:
                return s
    return domain


def get_amazon_data(req_url: str) -> Tuple[bool, str]:
    """
    获取 Amazon 数据
    """
    headers = {
        "accept-encoding": "gzip, deflate, br",
        "Host": "www.amazon.co.jp",
        "User-Agent": get_user_agent(),
    }
    html_info, error = get_text(req_url, encoding="Shift_JIS")
    if html_info is None:
        html_info, error = get_text(req_url, headers=headers, encoding="Shift_JIS")
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
        html_info, error = get_text(req_url, headers=headers, encoding="Shift_JIS")
    if html_info is None:
        return False, error
    if "HTTP 503" in html_info:
        headers = {
            "Host": "www.amazon.co.jp",
            "User-Agent": get_user_agent(),
        }
        html_info, error = get_text(req_url, headers=headers, encoding="Shift_JIS")
    if html_info is None:
        return False, error
    return True, html_info


def get_imgsize(url):
    proxies = config.proxies
    timeout = config.timeout
    retry_times = config.retry
    headers = config.headers

    for _ in range(int(retry_times)):
        try:
            response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout, verify=False, stream=True)
            if response.status_code == 200:
                file_head = BytesIO()
                chunk_size = 1024 * 10
                for chunk in response.iter_content(chunk_size):
                    file_head.write(chunk)
                    response.close()
                    try:
                        img = Image.open(file_head)
                        return img.size
                    except Exception:
                        return 0, 0
        except Exception:
            return 0, 0
    return 0, 0


def get_dmm_trailer(trailer_url):  # 如果预览片地址为 dmm ，尝试获取 dmm 预览片最高分辨率
    if ".dmm.co" not in trailer_url:
        return trailer_url
    if trailer_url.startswith("//"):
        trailer_url = "https:" + trailer_url
    """
    '_sm_w.mp4': 320*180, 3.8MB     # 最低分辨率
    '_dm_w.mp4': 560*316, 10.1MB    # 中等分辨率
    '_dmb_w.mp4': 720*404, 14.6MB   # 次高分辨率
    '_mhb_w.mp4': 720*404, 27.9MB   # 最高分辨率
    https://cc3001.dmm.co.jp/litevideo/freepv/s/ssi/ssis00090/ssis00090_sm_w.mp4
    https://cc3001.dmm.co.jp/litevideo/freepv/s/ssi/ssis00090/ssis00090_dm_w.mp4
    https://cc3001.dmm.co.jp/litevideo/freepv/s/ssi/ssis00090/ssis00090_dmb_w.mp4
    https://cc3001.dmm.co.jp/litevideo/freepv/s/ssi/ssis00090/ssis00090_mhb_w.mp4
    """

    # keylist = ['_sm_w.mp4', '_dm_w.mp4', '_dmb_w.mp4', '_mhb_w.mp4']
    if "_mhb_w.mp4" not in trailer_url:
        t = re.findall(r"(.+)(_[sd]mb?_w.mp4)", trailer_url)
        if t:
            s, e = t[0]
            mhb_w = s + "_mhb_w.mp4"
            dmb_w = s + "_dmb_w.mp4"
            dm_w = s + "_dm_w.mp4"
            # 次高分辨率只需检查最高
            if e == "_dmb_w.mp4":
                if check_url(mhb_w):
                    trailer_url = mhb_w
            elif e == "_dm_w.mp4":
                if check_url(mhb_w):
                    trailer_url = mhb_w
                elif check_url(dmb_w):
                    trailer_url = dmb_w
            # 最差分辨率则依次检查最高，次高，中等
            elif e == "_sm_w.mp4":
                if check_url(mhb_w):
                    trailer_url = mhb_w
                elif check_url(dmb_w):
                    trailer_url = dmb_w
                elif check_url(dm_w):
                    trailer_url = dm_w
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
        res_json, error = get_json(url)
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


def _get_pic_by_google(pic_url):
    google_keyused = config.google_keyused
    google_keyword = config.google_keyword
    req_url = f"https://www.google.com/searchbyimage?sbisrc=2&image_url={pic_url}"
    # req_url = f'https://lens.google.com/uploadbyurl?url={pic_url}&hl=zh-CN&re=df&ep=gisbubu'
    response, error = get_text(req_url)
    big_pic = True
    if response is not None:
        url_list = re.findall(r'a href="([^"]+isz:l[^"]+)">', response)
        url_list_middle = re.findall(r'a href="([^"]+isz:m[^"]+)">', response)
        if not url_list and url_list_middle:
            url_list = url_list_middle
            big_pic = False
        if url_list:
            req_url = "https://www.google.com" + url_list[0].replace("amp;", "")
            response, error = get_text(req_url)
            if response is not None:
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

                        p_url = temp_url.encode("utf-8").decode(
                            "unicode_escape"
                        )  # url中的Unicode字符转义，不转义，url请求会失败
                        if "m.media-amazon.com" in p_url:
                            p_url = re.sub(r"\._[_]?AC_[^\.]+\.", ".", p_url)
                            pic_size = get_imgsize(p_url)
                            if pic_size[0]:
                                return p_url, pic_size, big_pic
                        else:
                            url = check_url(p_url)
                            if url:
                                pic_size = (w, h)
                                return url, pic_size, big_pic
    return "", "", ""


def get_big_pic_by_google(pic_url, poster=False):
    url, pic_size, big_pic = _get_pic_by_google(pic_url)
    if not poster:
        if big_pic or (
            pic_size and int(pic_size[0]) > 800 and int(pic_size[1]) > 539
        ):  # cover 有大图时或者图片高度 > 800 时使用该图片
            return url, pic_size
        return "", ""
    if url and int(pic_size[1]) < 1000:  # poster，图片高度小于 1500，重新搜索一次
        url, pic_size, big_pic = _get_pic_by_google(url)
    if pic_size and (
        big_pic or "blogger.googleusercontent.com" in url or int(pic_size[1]) > 560
    ):  # poster，大图或高度 > 560 时，使用该图片
        return url, pic_size
    else:
        return "", ""
