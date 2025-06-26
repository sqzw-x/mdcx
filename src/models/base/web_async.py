import asyncio
import time
from io import BytesIO
from typing import Any, Callable, Literal, Optional

import httpx
from PIL import Image


class AsyncWebClient:
    def __init__(
        self,
        *,
        proxy: Optional[str] = None,
        retry: int = 3,
        timeout: Optional[httpx.Timeout] = None,
        default_headers: Optional[dict[str, str]] = None,
        log_fn: Optional[Callable[[str], None]] = None,
    ):
        limits = httpx.Limits(max_connections=100, max_keepalive_connections=50, keepalive_expiry=20)
        self.retry = retry
        self.default_headers = default_headers or {}
        # httpx 不支持为每个请求单独设置代理
        self.proxy_client = httpx.AsyncClient(
            limits=limits,
            proxy=proxy,
            verify=False,
            timeout=timeout,
            follow_redirects=True,
            max_redirects=10,
        )
        self.no_proxy_client = httpx.AsyncClient(
            limits=limits,
            verify=False,
            timeout=timeout,
            follow_redirects=True,
            max_redirects=10,
        )
        self.log_fn = log_fn if log_fn is not None else lambda _: None

    def _client(self, use_proxy):
        return self.proxy_client if use_proxy else self.no_proxy_client

    def _prepare_headers(self, url: Optional[str] = None, headers: Optional[dict[str, str]] = None) -> dict[str, str]:
        """预处理请求头"""
        if not headers:
            headers = self.default_headers.copy()

        # 根据URL设置特定的Referer
        if url:
            if "getchu" in url:
                headers.update({"Referer": "http://www.getchu.com/top.html"})
            elif "xcity" in url:
                headers.update(
                    {"referer": "https://xcity.jp/result_published/?genre=%2Fresult_published%2F&q=2&sg=main&num=60"}
                )
            elif "javbus" in url:
                headers.update({"Referer": "https://www.javbus.com/"})
            elif "giga" in url and "cookie_set.php" not in url:
                headers.update({"Referer": "https://www.giga-web.jp/top.html"})

        return headers

    async def request(
        self,
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
        url: str,
        *,
        headers: Optional[dict[str, str]] = None,
        cookies: Optional[dict[str, str]] = None,
        use_proxy: bool = True,
        data: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        timeout: Optional[httpx.Timeout] = None,
    ):
        """
        执行请求的通用方法

        Args:
            url: 请求URL
            headers: 请求头
            cookies: cookies
            use_proxy: 是否使用代理
            data: 表单数据
            json_data: JSON数据
            timeout: 请求超时时间, 覆盖客户端默认值

        Returns:
            tuple[Optional[httpx.Response], str]: (响应对象, 错误信息)
        """
        try:
            headers = self._prepare_headers(url, headers)
            retry_count = self.retry
            error_msg = ""
            for attempt in range(retry_count):
                try:
                    self.log_fn(f"🔎 {time.time()} {method} {url}" + f" ({attempt + 1}/{retry_count})" * (attempt != 0))
                    resp = await self._client(use_proxy).request(
                        method,
                        url,
                        headers=headers,
                        cookies=cookies,
                        data=data,
                        json=json_data,
                        timeout=timeout or httpx.USE_CLIENT_DEFAULT,
                    )
                    # 检查响应状态
                    if resp.status_code >= 300 and not (resp.status_code == 302 and resp.headers.get("Location")):
                        error_msg = f"HTTP {resp.status_code}"
                        self.log_fn(f"🔴 请求失败 {error_msg}")
                    else:
                        self.log_fn(f"✅ 请求成功 {url}")
                        return resp, ""
                except httpx.TimeoutException:
                    error_msg = "请求超时"
                    self.log_fn(f"🔴 {error_msg} (尝试 {attempt + 1}/{retry_count})")
                except httpx.ConnectError as e:
                    error_msg = f"连接错误: {str(e)}"
                    self.log_fn(f"🔴 {error_msg} (尝试 {attempt + 1}/{retry_count})")
                except Exception as e:
                    error_msg = f"请求异常: {str(e)}"
                    self.log_fn(f"🔴 {error_msg} (尝试 {attempt + 1}/{retry_count})")
                # 重试前等待
                if attempt < retry_count - 1:
                    await asyncio.sleep(attempt * 3 + 2)
            return None, f"{method} {url} 失败: {error_msg}"
        except Exception as e:
            error_msg = f"{method} {url} 发生未知错误:  {str(e)}"
            self.log_fn(f"🔴 {error_msg}")
            return None, error_msg

    async def get_text(
        self,
        url: str,
        *,
        headers: Optional[dict[str, str]] = None,
        cookies: Optional[dict[str, str]] = None,
        encoding: str = "utf-8",
        use_proxy: bool = True,
    ) -> tuple[Optional[str], str]:
        """请求文本内容"""
        resp, error = await self.request("GET", url, headers=headers, cookies=cookies, use_proxy=use_proxy)
        if resp is None:
            return None, error
        try:
            resp.encoding = encoding
            return resp.text, error
        except Exception as e:
            return None, f"文本解析失败: {str(e)}"

    async def get_content(
        self,
        url: str,
        *,
        headers: Optional[dict[str, str]] = None,
        cookies: Optional[dict[str, str]] = None,
        use_proxy: bool = True,
    ) -> tuple[Optional[bytes], Optional[str]]:
        """请求二进制内容"""
        resp, error = await self.request("GET", url, headers=headers, cookies=cookies, use_proxy=use_proxy)
        if resp is None:
            return None, error

        return resp.content, None

    async def get_json(
        self,
        url: str,
        *,
        headers: Optional[dict[str, str]] = None,
        cookies: Optional[dict[str, str]] = None,
        use_proxy: bool = True,
    ) -> tuple[Optional[dict[str, Any]], Optional[str]]:
        """请求JSON数据"""
        response, error = await self.request("GET", url, headers=headers, cookies=cookies, use_proxy=use_proxy)
        if response is None:
            return None, error
        try:
            return response.json(), None
        except Exception as e:
            return None, f"JSON解析失败: {str(e)}"

    async def post_text(
        self,
        url: str,
        *,
        data: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        cookies: Optional[dict[str, str]] = None,
        encoding: str = "utf-8",
        use_proxy: bool = True,
    ) -> tuple[Optional[str], Optional[str]]:
        """POST 请求, 返回响应文本内容"""
        response, error = await self.request(
            "POST", url, data=data, json_data=json_data, headers=headers, cookies=cookies, use_proxy=use_proxy
        )
        if response is None:
            return None, error
        try:
            response.encoding = encoding
            return response.text, None
        except Exception as e:
            return None, f"文本解析失败: {str(e)}"

    async def post_json(
        self,
        url: str,
        *,
        data: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        cookies: Optional[dict[str, str]] = None,
        use_proxy: bool = True,
    ) -> tuple[Optional[dict[str, Any]], Optional[str]]:
        """POST 请求, 返回响应JSON数据"""
        response, error = await self.request(
            "POST", url, data=data, json_data=json_data, headers=headers, cookies=cookies, use_proxy=use_proxy
        )
        if error or response is None:
            return None, error

        try:
            return response.json(), None
        except Exception as e:
            return None, f"JSON解析失败: {str(e)}"

    async def post_content(
        self,
        url: str,
        *,
        data: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        cookies: Optional[dict[str, str]] = None,
        use_proxy: bool = True,
    ) -> tuple[Optional[bytes], Optional[str]]:
        """POST请求, 返回二进制响应"""
        response, error = await self.request(
            "POST", url, data=data, json_data=json_data, headers=headers, cookies=cookies, use_proxy=use_proxy
        )
        if error or response is None:
            return None, error

        return response.content, None

    async def get_filesize(self, url: str, *, use_proxy: bool = True) -> Optional[int]:
        """获取文件大小"""
        response, error = await self.request("HEAD", url, use_proxy=use_proxy)
        if response is None:
            self.log_fn(f"🔴 获取文件大小失败: {error}")
            return None
        if response.status_code < 400:
            return int(response.headers.get("Content-Length"))
        return None

    async def download(self, url: str, file_path: str, *, use_proxy: bool = True) -> bool:
        """
        下载文件. 当文件较大时分块下载

        Args:
            url: 下载链接
            file_path: 保存路径
            use_proxy: 是否使用代理

        Returns:
            bool: 下载是否成功
        """
        # 获取文件大小
        file_size = await self.get_filesize(url, use_proxy=use_proxy)
        # 判断是不是webp文件
        webp = False
        if file_path.endswith("jpg") and ".webp" in url:
            webp = True
        MB = 1024**2
        if not file_size or file_size <= 2 * MB or webp:
            # 没有大小时, 不支持分段下载, 直接下载; < 2 MB 的直接下载
            content, error = await self.get_content(url, use_proxy=use_proxy)
            if not content:
                self.log_fn(f"🔴 下载失败: {error}")
                return False
            if webp:
                try:
                    byte_stream = BytesIO(content)
                    img: Image.Image = Image.open(byte_stream)
                    if img.mode == "RGBA":
                        img = img.convert("RGB")
                    img.save(file_path, quality=95, subsampling=0)
                    img.close()
                    return True
                except Exception as e:
                    self.log_fn(f"🔴 WebP转换失败: {str(e)}")
                    return False
            else:
                try:
                    with open(file_path, "wb") as f:
                        f.write(content)
                    return True
                except Exception as e:
                    self.log_fn(f"🔴 文件写入失败: {str(e)}")
                    return False

        return await self._download_chunks(url, file_path, file_size, use_proxy)

    async def _download_chunks(self, url: str, file_path: str, file_size: int, use_proxy: bool = True) -> bool:
        """分块下载大文件"""
        # 分块，每块 1 MB
        MB = 1024**2
        each_size = min(1 * MB, file_size)
        parts = [(s, min(s + each_size, file_size)) for s in range(0, file_size, each_size)]

        self.log_fn(f"📦 分块下载: {len(parts)} 个分块, 总大小: {file_size} bytes")

        # 先创建文件并预分配空间
        try:
            with open(file_path, "wb") as f:
                f.truncate(file_size)
        except Exception as e:
            self.log_fn(f"🔴 文件创建失败: {str(e)}")
            return False

        # 创建下载任务
        semaphore = asyncio.Semaphore(10)  # 限制并发数
        tasks = []

        for i, (start, end) in enumerate(parts):
            task = self._download_chunk(semaphore, url, file_path, start, end, i, use_proxy)
            tasks.append(task)

        # 并发执行所有下载任务
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # 检查所有任务是否成功
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.log_fn(f"🔴 分块 {i} 下载异常: {str(result)}")
                    return False
                elif not result:
                    self.log_fn(f"🔴 分块 {i} 下载失败")
                    return False
            self.log_fn(f"✅ 多分块下载完成: {file_path}")
            return True
        except Exception as e:
            self.log_fn(f"🔴 并发下载异常: {str(e)}")
            return False

    async def _download_chunk(
        self,
        semaphore: asyncio.Semaphore,
        url: str,
        file_path: str,
        start: int,
        end: int,
        chunk_id: int,
        use_proxy: bool = True,
    ) -> bool:
        """下载单个分块"""
        async with semaphore:
            res, error = await self.get_content(url, headers={"Range": f"bytes={start}-{end}"}, use_proxy=use_proxy)
            if res is None:
                self.log_fn(f"🔴 分块 {chunk_id} 下载失败: {error}")
                return False
        # 写入文件
        with open(file_path, "rb+") as fp:
            fp.seek(start)
            fp.write(res)
        self.log_fn(f"✅ 分块 {chunk_id} 下载完成 ({start}-{end})")
        return True
