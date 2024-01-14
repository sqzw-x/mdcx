#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import socket
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from threading import Lock
from urllib.parse import quote

import cloudscraper
import curl_cffi.requests
import requests
import urllib3.util.connection as urllib3_cn
from PIL import Image
from ping3 import ping
from requests.exceptions import ChunkedEncodingError, ConnectTimeout, ConnectionError, ContentDecodingError, HTTPError, \
    InvalidHeader, InvalidProxyURL, InvalidURL, ProxyError, ReadTimeout, SSLError, StreamConsumedError, Timeout, \
    TooManyRedirects, URLRequired

from models.base.utils import get_user_agent, singleton
from models.config.config import config
from models.signals import signal


def _allowed_gai_family():
    """
     https://github.com/shazow/urllib3/blob/master/urllib3/util/connection.py
    """
    family = socket.AF_INET
    return family


try:
    if config.ipv4_only:
        urllib3_cn.allowed_gai_family = _allowed_gai_family
except:
    urllib3_cn.allowed_gai_family = _allowed_gai_family


@singleton
class WebRequests:
    def __init__(self):
        self.session_g = requests.Session()
        self.session_g.mount('https://', requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100))
        self.session_g.mount('http://', requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100))
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'firefox', 'platform': 'windows', 'mobile': False})  # returns a CloudScraper instance
        self.lock = Lock()
        self.pool = ThreadPoolExecutor(32)
        self.curl_session = curl_cffi.requests.Session()

    def get_html(self, url: str, headers=None, cookies=None, proxies=True, allow_redirects=True, json_data=False,
                 content=False,
                 res=False, keep=True, timeout=False, encoding='utf-8', back_cookie=False):
        # 获取代理信息
        retry_times = config.retry
        if proxies:
            proxies = config.proxies
        else:
            proxies = {
                "http": None,
                "https": None,
            }

        if not headers:
            headers = config.headers
        if not timeout:
            timeout = config.timeout
        if 'getchu' in url:
            headers_o = {
                'Referer': 'http://www.getchu.com/top.html',
            }
            headers.update(headers_o)
        elif 'xcity' in url:
            headers_o = {
                'referer': 'https://xcity.jp/result_published/?genre=%2Fresult_published%2F&q=2&sg=main&num=60',
            }
            headers.update(headers_o)

        signal.add_log(f'🔎 请求 {url}')
        for i in range(int(retry_times)):
            try:
                if keep:
                    response = self.session_g.get(url, headers=headers, cookies=cookies, proxies=proxies,
                                                  timeout=timeout,
                                                  verify=False, allow_redirects=allow_redirects)
                else:
                    response = requests.get(url, headers=headers, cookies=cookies, proxies=proxies, timeout=timeout,
                                            verify=False, allow_redirects=allow_redirects)
                # print(response.headers.items())
                # print(response.status_code, url)
                _header = response.headers
                if back_cookie:
                    _header = response.cookies if response.cookies else _header
                if response.status_code > 299:
                    if response.status_code == 302 and allow_redirects:
                        pass
                    else:
                        error_info = f"{response.status_code} {url}"
                        signal.add_log('🔴 重试 [%s/%s] %s' % (i + 1, retry_times, error_info))
                        continue
                else:
                    signal.add_log(f'✅ 成功 {url}')
                if res:
                    return _header, response
                if content:
                    return _header, response.content
                response.encoding = encoding
                if json_data:
                    return _header, response.json()
                return _header, response.text
            except Exception as e:
                error_info = '%s\nError: %s' % (url, e)
                signal.add_log('[%s/%s] %s' % (i + 1, retry_times, error_info))
        signal.add_log(f"🔴 请求失败！{error_info}")
        return False, error_info

    def post_html(self, url: str, data=None, json=None, headers=None, cookies=None, proxies=True, json_data=False,
                  keep=True):
        # 获取代理信息
        timeout = config.timeout
        retry_times = config.retry
        if not headers:
            headers = config.headers
        if proxies:
            proxies = config.proxies
        else:
            proxies = {
                "http": None,
                "https": None,
            }

        signal.add_log(f'🔎 POST请求 {url}')
        for i in range(int(retry_times)):
            try:
                if keep:
                    response = self.session_g.post(url=url, data=data, json=json, headers=headers, cookies=cookies,
                                                   proxies=proxies, timeout=timeout, verify=False)
                else:
                    response = requests.post(url=url, data=data, json=json, headers=headers, cookies=cookies,
                                             proxies=proxies, timeout=timeout, verify=False)
                if response.status_code > 299:
                    error_info = f"{response.status_code} {url}"
                    signal.add_log('🔴 重试 [%s/%s] %s' % (i + 1, retry_times, error_info))
                    continue
                else:
                    signal.add_log(f'✅ POST成功 {url}')
                response.encoding = 'utf-8'
                if json_data:
                    return True, response.json()
                return True, response.text
            except Exception as e:
                error_info = '%s\nError: %s' % (url, e)
                signal.add_log('[%s/%s] %s' % (i + 1, retry_times, error_info))
        signal.add_log(f"🔴 请求失败！{error_info}")
        return False, error_info

    def scraper_html(self, url: str, proxies=True, cookies=None, headers=None):
        # 获取代理信息
        is_docker = config.is_docker
        timeout = config.timeout
        retry_times = config.retry
        if is_docker:
            return self.get_html(url, proxies=proxies, cookies=cookies)
        if proxies:
            proxies = config.proxies
        else:
            proxies = {
                "http": None,
                "https": None,
            }

        signal.add_log(f'🔎 Scraper请求 {url}')
        for i in range(retry_times):
            try:
                with self.scraper.get(url, headers=headers, proxies=proxies, cookies=cookies, timeout=timeout) as f:
                    response = f

                if response.status_code > 299:
                    error_info = f"{response.status_code} {url} {str(f.cookies).replace('<RequestsCookieJar[', '').replace(']>', '')}"
                    return False, error_info
                else:
                    signal.add_log(f'✅ Scraper成功 {url}')
                response.encoding = 'utf-8'
                return True, f.text
            except Exception as e:
                error_info = '%s\nError: %s' % (url, e)
                signal.add_log('🔴 重试 [%s/%s] %s' % (i + 1, retry_times, error_info))
        signal.add_log(f"🔴 请求失败！{error_info}")
        return False, error_info

    def _get_filesize(self, url):
        proxies = config.proxies
        timeout = config.timeout
        retry_times = config.retry
        headers = config.headers

        for _ in range(int(retry_times)):
            try:
                response = self.session_g.head(url, headers=headers, proxies=proxies, timeout=timeout, verify=False)
                file_size = response.headers.get('Content-Length')
                return file_size
            except:
                pass
        return False

    def multi_download(self, url, file_path):
        # 获取文件大小
        file_size = self._get_filesize(url)

        # 判断是不是webp文件
        webp = False
        if file_path.endswith('jpg') and '.webp' in url:
            webp = True

        # 没有大小时，不支持分段下载，直接下载；< 2 MB 的直接下载
        MB = 1024 ** 2
        if not file_size or int(file_size) <= 2 * MB or webp:
            result, response = get_html(url, content=True)
            if result:
                if webp:
                    byte_stream = BytesIO(response)
                    img = Image.open(byte_stream)
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')
                    img.save(file_path, quality=95, subsampling=0)
                    img.close()
                else:
                    with open(file_path, "wb") as f:
                        f.write(response)
                return True
            return False

        return self._multi_download2(url, file_path, int(file_size))

    def _multi_download2(self, url, file_path, file_size) -> bool:
        # 分块，每块 1 MB
        MB = 1024 ** 2
        file_size = int(file_size)
        each_size = min(int(1 * MB), file_size)
        parts = [(s, min(s + each_size, file_size)) for s in range(0, file_size, each_size)]
        # print(f'分块数：{len(parts)} \n')

        # 先写入一个文件
        f = open(file_path, 'wb')
        f.truncate(file_size)
        f.close()

        # 开始下载
        i = 0
        task_list = []
        for part in parts:
            i += 1
            start, end = part
            task_list.append([start, end, i, url, file_path])
        result = self.pool.map(self._start_download, task_list)
        for res in result:
            if not res:
                # bar.close()
                return False
        # bar.close()
        return True

    def _start_download(self, task) -> bool:
        start, end, i, url, file_path = task

        proxies = config.proxies
        timeout = config.timeout
        retry_times = config.retry
        headers = config.headers
        _headers = headers.copy()
        _headers['Range'] = f'bytes={start}-{end}'
        for _ in range(int(retry_times)):
            try:
                response = self.session_g.get(url, headers=_headers, proxies=proxies, timeout=timeout, verify=False,
                                              stream=True)
                chunk_size = 128
                chunks = []
                for chunk in response.iter_content(chunk_size=chunk_size):
                    chunks.append(chunk)
                    # bar.update(chunk_size)
                self.lock.acquire()
                with open(file_path, "rb+") as fp:
                    fp.seek(start)
                    for chunk in chunks:
                        fp.write(chunk)
                    self.lock.release()
                    # 释放锁
                del chunks
                return True
            except:
                pass
        return False

    def curl_html(self, url, headers=None, proxies=True, cookies=None):
        """
        curl请求(模拟浏览器指纹)
        """
        # 获取代理信息
        retry_times = config.retry
        if proxies:
            proxies = config.proxies
        else:
            proxies = {
                "http": None,
                "https": None,
            }

        signal.add_log(f'🔎 请求 {url}')
        for i in range(int(retry_times)):
            try:
                response = self.curl_session.get(url_encode(url), headers=headers, cookies=cookies, proxies=proxies,
                                                 impersonate="edge99")
                if 'amazon' in url:
                    response.encoding = 'Shift_JIS'
                else:
                    response.encoding = 'UFT-8'
                if response.status_code == 200:
                    signal.add_log(f'✅ 成功 {url}')
                    return response.headers, response.text
                else:
                    error_info = f"{response.status_code} {url}"
                    signal.add_log('🔴 重试 [%s/%s] %s' % (i + 1, retry_times, error_info))
                    continue
            except Exception as e:
                error_info = '%s\nError: %s' % (url, e)
                signal.add_log('[%s/%s] %s' % (i + 1, retry_times, error_info))
        signal.add_log(f"🔴 请求失败！{error_info}")
        return False, error_info


web = WebRequests()
get_html = web.get_html
post_html = web.post_html
scraper_html = web.scraper_html
multi_download = web.multi_download
curl_html = web.curl_html


def url_encode(url):
    new_url = ''
    for i in url:
        if i not in [':', '/', '&', '?', '=', '%']:
            i = quote(i)
        new_url += i
    return new_url


def check_url(url, length=False, real_url=False):
    proxies = config.proxies
    timeout = config.timeout
    retry_times = config.retry
    headers = config.headers

    if not url:
        return 0

    signal.add_log(f'⛑️ 检测链接 {url}')
    if 'http' not in url:
        signal.add_log(f'🔴 检测未通过！链接格式错误！ {url}')
        return 0

    if 'getchu' in url:
        headers_o = {
            'Referer': 'http://www.getchu.com/top.html',
        }
        headers.update(headers_o)

    for j in range(retry_times):
        try:
            r = requests.head(url, headers=headers, proxies=proxies, timeout=timeout, verify=False,
                              allow_redirects=True)

            # 状态码 > 299，表示请求失败，视为不可用
            if r.status_code > 299:
                error_info = f"{r.status_code} {url}"
                signal.add_log('🔴 请求失败！ 重试: [%s/%s] %s' % (j + 1, retry_times, error_info))
                continue

            # 返回重定向的url
            true_url = r.url
            if real_url:
                return true_url

            # 检查是否需要登录 https://lookaside.fbsbx.com/lookaside/crawler/media/?media_id=637921621668064
            if 'login' in true_url:
                signal.add_log(f'🔴 检测未通过！需要登录查看 {true_url}')
                return 0

            # 检查是否带有图片不存在的关键词
            '''
            如果跳转后的真实链接存在删图标识，视为不可用
            https://pics.dmm.co.jp/mono/movie/n/now_printing/now_printing.jpg dmm 删图的标识，javbus、javlib 用的是 dmm 图
            https://static.mgstage.com/mgs/img/common/actress/nowprinting.jpg mgstage 删图的标识
            https://jdbimgs.com/images/noimage_600x404.jpg javdb删除的图 WANZ-921
            https://www.javbus.com/imgs/cover/nopic.jpg
            https://assets.tumblr.com/images/media_violation/community_guidelines_v1_1280.png tumblr删除的图
            '''
            bad_url_keys = ['now_printing', 'nowprinting', 'noimage', 'nopic', 'media_violation']
            for each_key in bad_url_keys:
                if each_key in true_url:
                    signal.add_log(f'🔴 检测未通过！当前图片已被网站删除 {url}')
                    return 0

            # 获取文件大小。如果没有获取到文件大小，尝试下载15k数据，如果失败，视为不可用
            content_length = r.headers.get('Content-Length')
            if not content_length:
                response = requests.get(true_url, headers=headers, proxies=proxies, timeout=timeout, verify=False,
                                        stream=True)
                i = 0
                chunk_size = 5120
                for _ in response.iter_content(chunk_size):
                    i += 1
                    if i == 3:
                        response.close()
                        signal.add_log(f'✅ 检测通过！未返回大小，预下载15k通过 {true_url}')
                        return 10240 if length else true_url
                signal.add_log(f'🔴 检测未通过！未返回大小，预下载15k失败 {true_url}')
                return 0

            # 如果返回内容的文件大小 < 8k，视为不可用
            elif int(content_length) < 8192:
                signal.add_log(f'🔴 检测未通过！返回大小({content_length}) < 8k {true_url}')
                return 0
            signal.add_log(f'✅ 检测通过！返回大小({content_length}) {true_url}')
            return int(content_length) if length else true_url
        except InvalidProxyURL as e:
            error_info = f' 无效的代理链接 ({e}) {url}'
        except ProxyError as e:
            error_info = f' 代理错误 {e} {url}'
        except SSLError as e:
            error_info = f' SSL错误 ({e}) {url}'
        except ConnectTimeout as e:
            error_info = f' 尝试连接到远程服务器时超时 ({e}) {url}'
        except ReadTimeout as e:
            error_info = f' 服务器未在分配的时间内发送任何数据 ({e}) {url}'
        except Timeout as e:
            error_info = f' 请求超时错误 ({e}) {url}'
        except ConnectionError as e:
            error_info = f' 连接错误 {e} {url}'
        except URLRequired as e:
            error_info = f' URL格式错误 ({e}) {url}'
        except TooManyRedirects as e:
            error_info = f' 过多的重定向 ({e}) {url}'
        except InvalidURL as e:
            error_info = f' 无效的url ({e}) {url}'
        except InvalidHeader as e:
            error_info = f' 无效的请求头 ({e}) {url}'
        except HTTPError as e:
            error_info = f' HTTP错误 {e} {url}'
        except ChunkedEncodingError as e:
            error_info = f' 服务器声明了分块编码，但发送了无效的分块 ({e}) {url}'
        except ContentDecodingError as e:
            error_info = f' 解码响应内容失败 ({e}) {url}'
        except StreamConsumedError as e:
            error_info = f' 该响应的内容已被占用 ({e}) {url}'
        except Exception as e:
            error_info = f' Error ({e}) {url}'
        signal.add_log('🔴 重试 [%s/%s] %s' % (j + 1, retry_times, error_info))
    signal.add_log(f'🔴 检测未通过！ {url}')
    return 0


def get_avsox_domain():
    issue_url = 'https://tellme.pw/avsox'
    result, response = get_html(issue_url)
    domain = 'https://avsox.click'
    if result:
        res = re.findall(r'(https://[^"]+)', response)
        for s in res:
            if s and 'https://avsox.com' not in s or 'api.qrserver.com' not in s:
                return s
    return domain


def get_amazon_data(req_url):
    """
    获取 Amazon 数据，修改地区为540-0002
    """
    headers = {
        "accept-encoding": "gzip, deflate, br",
        'Host': 'www.amazon.co.jp',
        'User-Agent': get_user_agent(),
    }
    try:
        result, html_info = curl_html(req_url)
    except:
        result, html_info = curl_html(req_url, headers=headers)
        session_id = ''
        ubid_acbjp = ''
        if x := re.findall(r'sessionId: "([^"]+)', html_info):
            session_id = x[0]
        if x := re.findall(r'ubid-acbjp=([^ ]+)', html_info):
            ubid_acbjp = x[0]
        headers_o = {
            'cookie': f'session-id={session_id}; ubid_acbjp={ubid_acbjp}',
        }
        headers.update(headers_o)
        result, html_info = curl_html(req_url, headers=headers)

    if not result:
        if '503 http' in html_info:
            headers = {
                'Host': 'www.amazon.co.jp',
                'User-Agent': get_user_agent(),
            }
            result, html_info = get_html(req_url, headers=headers, keep=False, back_cookie=True)

        if not result:
            return False, html_info

    if '540-0002' not in html_info:
        try:
            # 获取 anti_csrftoken_a2z
            anti_csrftoken_a2z = re.findall(r'anti-csrftoken-a2z([^}]+)', html_info)[0].replace('&quot;', '').strip(':')
            session_id = re.findall(r'sessionId: "([^"]+)', html_info)[0]
            ubid_acbjp = ''
            if 'ubid-acbjp' in str(result):
                try:
                    ubid_acbjp = result['set-cookie']
                except:
                    try:
                        ubid_acbjp = re.findall(r'ubid-acbjp=([^ ]+)', str(result))[0]
                    except:
                        pass
            headers_o = {
                'Anti-csrftoken-a2z': anti_csrftoken_a2z,
                'cookie': f'session-id={session_id}; ubid_acbjp={ubid_acbjp}',
            }
            headers.update(headers_o)
            mid_url = 'https://www.amazon.co.jp/portal-migration/hz/glow/get-rendered-toaster' \
                      '?pageType=Search&aisTransitionState=in&rancorLocationSource=REALM_DEFAULT&_='
            result, html = curl_html(mid_url, headers=headers)
            anti_csrftoken_a2z = re.findall(r'csrfToken="([^"]+)', html)[0]
            try:
                ubid_acbjp = re.findall(r'ubid-acbjp=([^ ]+)', str(result))[0]
            except:
                pass

            # 修改配送地址为日本，这样结果多一些
            headers_o = {
                'Anti-csrftoken-a2z': anti_csrftoken_a2z,
                'Content-length': '140',
                'Content-Type': 'application/json',
                'cookie': f'session-id={session_id}; ubid_acbjp={ubid_acbjp}',
            }
            headers.update(headers_o)
            post_url = 'https://www.amazon.co.jp/portal-migration/hz/glow/address-change?actionSource=glow'
            data = {"locationType": "LOCATION_INPUT", "zipCode": "540-0002", "storeContext": "generic",
                    "deviceType": "web", "pageType": "Search", "actionSource": "glow"}
            result, html = post_html(post_url, json=data, headers=headers)
            if result:
                if '540-0002' in str(html):
                    headers = {
                        'Host': 'www.amazon.co.jp',
                        'User-Agent': get_user_agent(),
                    }
                    result, html_info = curl_html(req_url, headers=headers)
                else:
                    print('Amazon 修改地区失败: ', req_url, str(result), str(html))
            else:
                print('Amazon 修改地区异常: ', req_url, str(result), str(html))

        except Exception as e:
            print('Amazon 修改地区出错: ', req_url, str(e))
            print(traceback.format_exc())

    return result, html_info


if "__main__" == __name__:
    # 测试下载文件
    list1 = [
        'https://issuecdn.baidupcs.com/issue/netdisk/yunguanjia/BaiduNetdisk_7.2.8.9.exe',
        'https://cc3001.dmm.co.jp/litevideo/freepv/1/118/118abw015/118abw015_mhb_w.mp4',
        'https://cc3001.dmm.co.jp/litevideo/freepv/1/118/118abw00016/118abw00016_mhb_w.mp4',
        'https://cc3001.dmm.co.jp/litevideo/freepv/1/118/118abw00017/118abw00017_mhb_w.mp4',
        'https://cc3001.dmm.co.jp/litevideo/freepv/1/118/118abw00018/118abw00018_mhb_w.mp4',
        'https://cc3001.dmm.co.jp/litevideo/freepv/1/118/118abw00019/118abw00019_mhb_w.mp4',
        'https://www.prestige-av.com/images/corner/goods/prestige/tktabw/018/pb_tktabw-018.jpg',
        'https://iqq1.one/preview/80/b/3SBqI8OjheI-800.jpg?v=1636404497',
    ]
    for each in list1:
        url = each
        file_path = each.split('/')[-1]
        t = threading.Thread(target=multi_download, args=(url, file_path))
        t.start()

    # 死循环，避免程序程序完后，pool自动关闭
    while True:
        pass


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
                    except:
                        return 0, 0
        except:
            return 0, 0
    return 0, 0


def get_dmm_trailer(trailer_url):  # 获取预览片
    if '.dmm.co' not in trailer_url:
        return trailer_url
    if trailer_url.startswith('//'):
        trailer_url = 'https:' + trailer_url
    '''
    '_sm_w.mp4': 320*180, 3.8MB
    '_dm_w.mp4': 560*316, 10.1MB
    '_dmb_w.mp4': 720*404, 14.6MB
    '_mhb_w.mp4': 720*404, 27.9MB
    https://cc3001.dmm.co.jp/litevideo/freepv/s/ssi/ssis00090/ssis00090_sm_w.mp4
    https://cc3001.dmm.co.jp/litevideo/freepv/s/ssi/ssis00090/ssis00090_dm_w.mp4
    https://cc3001.dmm.co.jp/litevideo/freepv/s/ssi/ssis00090/ssis00090_dmb_w.mp4
    https://cc3001.dmm.co.jp/litevideo/freepv/s/ssi/ssis00090/ssis00090_mhb_w.mp4
    '''

    # keylist = ['_sm_w.mp4', '_dm_w.mp4', '_dmb_w.mp4', '_mhb_w.mp4']
    if '_mhb_w.mp4' not in trailer_url:
        t = re.findall(r'(.+)(_[sd]mb?_w.mp4)', trailer_url)
        if t:
            s, e = t[0]
            mhb_w = s + '_mhb_w.mp4'
            dmb_w = s + '_dmb_w.mp4'
            dm_w = s + '_dm_w.mp4'
            if e == '_dmb_w.mp4':
                if check_url(mhb_w):
                    trailer_url = mhb_w
            elif e == '_dm_w.mp4':
                if check_url(mhb_w):
                    trailer_url = mhb_w
                elif check_url(dmb_w):
                    trailer_url = dmb_w
            elif e == '_sm_w.mp4':
                if check_url(mhb_w):
                    trailer_url = mhb_w
                elif check_url(dmb_w):
                    trailer_url = dmb_w
                elif check_url(dm_w):
                    trailer_url = dm_w
    return trailer_url


def _ping_host_thread(host_address, result_list, i):
    response = ping(host_address, timeout=1)
    result_list[i] = int(response * 1000) if response else 0


def ping_host(host_address):
    count = config.retry
    result_list = [None] * count
    thread_list = [0] * count
    for i in range(count):
        thread_list[i] = threading.Thread(target=_ping_host_thread, args=(host_address, result_list, i))
        thread_list[i].start()
    for i in range(count):
        thread_list[i].join()
    new_list = [each for each in result_list if each]
    return f'  ⏱ Ping {int(sum(new_list) / len(new_list))} ms ({len(new_list)}/{count})' \
        if new_list else f'  🔴 Ping - ms (0/{count})'


def check_version():
    if config.update_check == 'on':
        url = 'https://api.github.com/repos/sqzw-x/mdcx/releases/latest'
        _, res_json = get_html(url, json_data=True)
        if isinstance(res_json, dict):
            try:
                latest_version = res_json['tag_name']
                latest_version = int(latest_version)
                return latest_version
            except:
                signal.add_log(f'❌ 获取最新版本失败！{res_json}')


def check_theporndb_api_token():
    tips = '✅ 连接正常! '
    headers = config.headers
    proxies = config.proxies
    timeout = config.timeout
    api_token = config.theporndb_api_token
    url = 'https://api.metadataapi.net/scenes/hash/8679fcbdd29fa735'
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': get_user_agent(),
    }
    if not api_token:
        tips = '❌ 未填写 API Token，影响欧美刮削！可在「设置」-「网络」添加！'
    else:
        try:
            response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout, verify=False)
            if response.status_code == 401 and 'Unauthenticated' in str(response.text):
                tips = '❌ API Token 错误！影响欧美刮削！请到「设置」-「网络」中修改。'
            elif response.status_code == 200:
                if response.json().get('data'):
                    tips = '✅ 连接正常！'
                else:
                    tips = '❌ 返回数据异常！'
            else:
                tips = f'❌ 连接失败！请检查网络或代理设置！ {response.status_code} {response.text}'
        except Exception as e:
            tips = f'❌ 连接失败!请检查网络或代理设置！ {e}'
    signal.show_log_text(tips.replace('❌', ' ❌ ThePornDB').replace('✅', ' ✅ ThePornDB'))
    return tips


def _get_pic_by_google(pic_url):
    google_keyused = config.google_keyused
    google_keyword = config.google_keyword
    req_url = f'https://www.google.com/searchbyimage?sbisrc=2&image_url={pic_url}'
    # req_url = f'https://lens.google.com/uploadbyurl?url={pic_url}&hl=zh-CN&re=df&ep=gisbubu'
    result, response = get_html(req_url, keep=False)
    big_pic = True
    if result:
        url_list = re.findall(r'a href="([^"]+isz:l[^"]+)">', response)
        url_list_middle = re.findall(r'a href="([^"]+isz:m[^"]+)">', response)
        if not url_list and url_list_middle:
            url_list = url_list_middle
            big_pic = False
        if url_list:
            req_url = 'https://www.google.com' + url_list[0].replace('amp;', '')
            result, response = get_html(req_url, keep=False)
            if result:
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
                if 'goo_only' not in config.download_hd_pics:
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

                        p_url = temp_url.encode('utf-8').decode('unicode_escape')  # url中的Unicode字符转义，不转义，url请求会失败
                        if 'm.media-amazon.com' in p_url:
                            p_url = re.sub(r'\._[_]?AC_[^\.]+\.', '.', p_url)
                            pic_size = get_imgsize(p_url)
                            if pic_size[0]:
                                return p_url, pic_size, big_pic
                        else:
                            url = check_url(p_url)
                            if url:
                                pic_size = (w, h)
                                return url, pic_size, big_pic
    return '', '', ''


def get_big_pic_by_google(pic_url, poster=False):
    url, pic_size, big_pic = _get_pic_by_google(pic_url)
    if not poster:
        if big_pic or (
                pic_size and int(pic_size[0]) > 800 and int(pic_size[1]) > 539):  # cover 有大图时或者图片高度 > 800 时使用该图片
            return url, pic_size
        return '', ''
    if url and int(pic_size[1]) < 1000:  # poster，图片高度小于 1500，重新搜索一次
        url, pic_size, big_pic = _get_pic_by_google(url)
    if pic_size and (big_pic or 'blogger.googleusercontent.com' in url or int(
            pic_size[1]) > 560):  # poster，大图或高度 > 560 时，使用该图片
        return url, pic_size
    else:
        return '', ''
