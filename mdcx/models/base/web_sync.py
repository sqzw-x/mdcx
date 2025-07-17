from typing import Dict, Optional

from mdcx.config.manager import config
from mdcx.utils import executor


def get_text_sync(
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


def get_json_sync(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    use_proxy=True,
):
    return executor.run(config.async_client.get_json(url, headers=headers, cookies=cookies, use_proxy=use_proxy))
