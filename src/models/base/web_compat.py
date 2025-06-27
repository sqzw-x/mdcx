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
    keep: bool = True,
    timeout: Union[bool, float] = False,
    encoding: str = "utf-8",
    back_cookie: bool = False,
):
    """
    目标是全部替换为 get_text, 一些参数不兼容:

    keep: 此参数 False 的原行为是使用裸 requests.get 而不是 session 发出请求
    timeout: 此参数允许为请求单独设置超时, 可以支持. 但实际上此前项目里只有 getchu 刮削使用此参数, 且设置固定值 40s (首个提交就如此), 似乎不合理
    back_cookie: 此参数会返回 response.cookies, 只有 get_amazon_data 使用此参数. 可以用 get_response 替代
    """
    success, result = get_text(url, headers=headers, cookies=cookies, proxies=proxies, encoding=encoding)
    if not success:
        return False, result
    if back_cookie:
        # 返回 cookies 和文本
        cookies_dict = cookies or {}
        return cookies_dict, result
    return True, result


def get_text(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    use_proxy=True,
    encoding: str = "utf-8",
):
    """获取文本内容的同步包装器"""
    text, error = executor.run(
        config.async_client.get_text(url, headers=headers, cookies=cookies, encoding=encoding, use_proxy=use_proxy)
    )
    if text is None:
        return False, error
    else:
        return True, text


def get_content(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    use_proxy=True,
):
    """获取二进制内容的同步包装器"""
    cookies_dict = cookies or {}

    content_data, error = executor.run(
        config.async_client.get_content(url, headers=headers, cookies=cookies_dict, use_proxy=use_proxy)
    )
    if content_data is not None:
        return True, content_data
    else:
        return False, error


def get_json(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    use_proxy=True,
):
    """获取JSON数据的同步包装器"""
    cookies_dict = cookies or {}

    json_result, error = executor.run(
        config.async_client.get_json(url, headers=headers, cookies=cookies_dict, use_proxy=use_proxy)
    )
    if json_result is not None:
        return True, json_result
    else:
        return False, error


def get_response(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    use_proxy=True,
):
    """获取响应对象的同步包装器"""
    cookies_dict = cookies or {}

    resp, error = executor.run(
        config.async_client.request("GET", url, headers=headers, cookies=cookies_dict, use_proxy=use_proxy)
    )
    if resp is not None:
        return resp.headers, resp
    else:
        return False, error


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
