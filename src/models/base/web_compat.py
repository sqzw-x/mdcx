"""
Web 请求兼容层 - 使用异步客户端和执行器提供向后兼容的同步接口
"""

from typing import Any, Dict, Optional

from ..config.manager import config
from .utils import executor


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


def post_text(
    url: str,
    *,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    use_proxy=True,
):
    text_result, error = executor.run(
        config.async_client.post_text(
            url, data=data, json_data=json, headers=headers, cookies=cookies, use_proxy=use_proxy
        )
    )
    if text_result is not None:
        return True, text_result
    else:
        return False, error


def post_json(
    url: str,
    *,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    use_proxy=True,
):
    """POST 请求并返回 JSON 数据的同步包装器"""
    json_result, error = executor.run(
        config.async_client.post_json(
            url, data=data, json_data=json, headers=headers, cookies=cookies, use_proxy=use_proxy
        )
    )
    if json_result is not None:
        return True, json_result
    else:
        return False, error


def curl_html(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    use_proxy=True,
):
    """
    curl请求的同步包装器 (使用普通的 get_text 方法)
    """
    if "amazon" in url:
        encoding = "Shift_JIS"
    else:
        encoding = "utf-8"
    response, error = executor.run(
        config.async_client.request("GET", url, headers=headers, cookies=cookies, use_proxy=use_proxy)
    )

    if response is None:
        return False, error
    else:
        response.encoding = encoding
        return response.headers, response.text


def multi_download(self, url: str, file_path: str) -> bool:
    """多线程下载的同步包装器"""
    result = executor.run(config.async_client.download(url, file_path))
    return result
