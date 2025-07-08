from typing import Any, Dict, Optional

from ..config.manager import config
from .utils import executor


def get_text(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    use_proxy=True,
    encoding: str = "utf-8",
):
    return executor.run(
        config.async_client.get_text(url, headers=headers, cookies=cookies, encoding=encoding, use_proxy=use_proxy)
    )


def get_content(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    use_proxy=True,
):
    return executor.run(config.async_client.get_content(url, headers=headers, cookies=cookies, use_proxy=use_proxy))


def get_json(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    use_proxy=True,
):
    return executor.run(config.async_client.get_json(url, headers=headers, cookies=cookies, use_proxy=use_proxy))


def get_response(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    use_proxy=True,
):
    return executor.run(config.async_client.request("GET", url, headers=headers, cookies=cookies, use_proxy=use_proxy))


def post_text(
    url: str,
    *,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    use_proxy=True,
):
    return executor.run(
        config.async_client.post_text(
            url, data=data, json_data=json, headers=headers, cookies=cookies, use_proxy=use_proxy
        )
    )


def post_json(
    url: str,
    *,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    use_proxy=True,
):
    return executor.run(
        config.async_client.post_json(
            url, data=data, json_data=json, headers=headers, cookies=cookies, use_proxy=use_proxy
        )
    )


def multi_download(url: str, file_path: str) -> bool:
    return executor.run(config.async_client.download(url, file_path))
