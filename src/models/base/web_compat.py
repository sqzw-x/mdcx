"""
Web 请求兼容层 - 使用异步客户端和执行器提供向后兼容的同步接口
"""

from typing import Any, Dict, Optional, Tuple, Union

from ..config.manager import config
from ..signals import signal
from .utils import executor


def get_html(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    proxies: Union[bool, Optional[Dict[str, str]]] = True,
    allow_redirects: bool = True,
    json_data: bool = False,
    content: bool = False,
    res: bool = False,
    keep: bool = True,
    timeout: Union[bool, float] = False,
    encoding: str = "utf-8",
    back_cookie: bool = False,
):
    """GET 请求的同步包装器"""
    # 处理代理参数
    use_proxy = proxies is not False

    # 处理 cookies
    cookies_dict = cookies or {}

    if content:
        # 返回二进制内容
        content_data, error = executor.run(
            config.async_client.get_content(url, headers=headers, cookies=cookies_dict, use_proxy=use_proxy)
        )
        if content_data is not None:
            return True, content_data
        else:
            return False, error

    elif json_data:
        # 返回 JSON 数据
        json_result, error = executor.run(
            config.async_client.get_json(url, headers=headers, cookies=cookies_dict, use_proxy=use_proxy)
        )
        if json_result is not None:
            return True, json_result
        else:
            return False, error

    elif res:
        # 返回响应对象的模拟
        # 由于异步客户端不直接返回响应对象，我们需要获取文本内容和头部信息
        resp, error = executor.run(
            config.async_client.request("GET", url, headers=headers, cookies=cookies_dict, use_proxy=use_proxy)
        )
        if resp is not None:
            return resp.headers, resp
        else:
            return False, error

    else:
        # 返回文本内容
        text, error = executor.run(
            config.async_client.get_text(
                url, headers=headers, cookies=cookies_dict, encoding=encoding, use_proxy=use_proxy
            )
        )
        if text is None:
            return False, error
        else:
            if back_cookie:
                return cookies_dict, text  # 返回 cookies 和文本
            return True, text


def post_html(
    url: str,
    *,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    use_proxy: Union[bool, Optional[Dict[str, str]]] = True,
    json_data: bool = False,
    keep: bool = True,
):
    """POST 请求的同步包装器"""
    # 处理代理参数
    use_proxy_flag = use_proxy is not False

    # 处理 cookies
    cookies_dict = cookies or {}

    if json_data:
        # 返回 JSON 数据
        json_result, error = executor.run(
            config.async_client.post_json(
                url, data=data, json_data=json, headers=headers, cookies=cookies_dict, use_proxy=use_proxy_flag
            )
        )
        if json_result is not None:
            return True, json_result
        else:
            return False, error
    else:
        # 返回文本内容
        text_result, error = executor.run(
            config.async_client.post_text(
                url, data=data, json_data=json, headers=headers, cookies=cookies_dict, use_proxy=use_proxy_flag
            )
        )
        if text_result is not None:
            return True, text_result
        else:
            return False, error


def curl_html(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    proxies: Union[bool, Optional[Dict[str, str]]] = True,
    cookies: Optional[Dict[str, str]] = None,
) -> Tuple[Union[bool, Any], Union[str, Any]]:
    """
    curl请求的同步包装器 (使用普通的 get_text 方法)
    """
    # 处理代理参数
    use_proxy = proxies is not False

    # 处理 cookies
    cookies_dict = cookies or {}

    # 使用 get_text 方法获取内容
    response, error = executor.run(
        config.async_client.request("GET", url, headers=headers, cookies=cookies_dict, use_proxy=use_proxy)
    )

    if response is None:
        return False, error
    else:
        if "amazon" in url:
            response.encoding = "Shift_JIS"
        else:
            response.encoding = "UTF-8"
        if response.status_code == 200:
            signal.add_log(f"✅ 成功 {url}")
            return response.headers, response.text
        else:
            return False, f"请求失败，状态码: {response.status_code}"


def multi_download(self, url: str, file_path: str) -> bool:
    """多线程下载的同步包装器"""
    result = executor.run(config.async_client.download(url, file_path))
    return result


scraper_html = curl_html
