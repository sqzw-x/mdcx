"""
Web 请求兼容层 - 使用异步客户端和执行器提供向后兼容的同步接口
"""

from typing import Any, Dict, Optional, Tuple, Union

import httpx

from ..config.manager import config
from ..signals import signal
from .utils import executor
from .web_async import AsyncWebClient

async_client = AsyncWebClient(
    proxy=config.httpx_proxy,
    retry=config.retry,
    timeout=httpx.Timeout(config.timeout),
    default_headers=config.headers,
    log_fn=signal.add_log,
)


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
            async_client.get_content(url, headers=headers, cookies=cookies_dict, use_proxy=use_proxy)
        )
        if content_data is not None:
            return True, content_data
        else:
            return False, error or "请求失败"

    elif json_data:
        # 返回 JSON 数据
        json_result, error = executor.run(
            async_client.get_json(url, headers=headers, cookies=cookies_dict, use_proxy=use_proxy)
        )
        if json_result is not None:
            return True, json_result
        else:
            return False, error or "请求失败"

    elif res:
        # 返回响应对象的模拟
        # 由于异步客户端不直接返回响应对象，我们需要获取文本内容和头部信息
        text_result, error = executor.run(
            async_client.get_text(url, headers=headers, cookies=cookies_dict, encoding=encoding, use_proxy=use_proxy)
        )
        if text_result is not None:
            # 创建一个模拟响应对象
            class MockResponse:
                def __init__(self, text):
                    self.text = text
                    self.headers = {}  # 简化处理，实际应该获取真实头部

            mock_response = MockResponse(text_result)
            return mock_response.headers, mock_response
        else:
            return False, error or "请求失败"

    else:
        # 返回文本内容
        text_result, error = executor.run(
            async_client.get_text(url, headers=headers, cookies=cookies_dict, encoding=encoding, use_proxy=use_proxy)
        )
        if text_result is not None:
            # 根据 back_cookie 参数决定返回内容
            if back_cookie:
                return cookies_dict, text_result  # 返回 cookies 和文本
            else:
                return {}, text_result  # 返回空字典和文本
        else:
            return False, error or "请求失败"


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
            async_client.post_json(
                url, data=data, json_data=json, headers=headers, cookies=cookies_dict, use_proxy=use_proxy_flag
            )
        )
        if json_result is not None:
            return True, json_result
        else:
            return False, error or "请求失败"
    else:
        # 返回文本内容
        text_result, error = executor.run(
            async_client.post_text(
                url, data=data, json_data=json, headers=headers, cookies=cookies_dict, use_proxy=use_proxy_flag
            )
        )
        if text_result is not None:
            return True, text_result
        else:
            return False, error or "请求失败"


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
    text_result, error = executor.run(
        async_client.get_text(url, headers=headers, cookies=cookies_dict, use_proxy=use_proxy)
    )

    if text_result is not None:
        # 返回模拟的头部信息和文本内容
        return {}, text_result
    else:
        return False, error or "请求失败"


def multi_download(self, url: str, file_path: str) -> bool:
    """多线程下载的同步包装器"""
    result = executor.run(async_client.download(url, file_path))
    return result
