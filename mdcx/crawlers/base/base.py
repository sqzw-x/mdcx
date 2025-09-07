import time
import traceback
from abc import ABC, abstractmethod
from asyncio import Lock
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal, Never

from parsel import Selector
from patchright._impl._api_structures import SetCookieParam
from patchright.async_api import Browser, BrowserContext

from mdcx.config.models import Website
from mdcx.models.types import CrawlerInput, CrawlerResponse, CrawlerResult

from .types import Context, CralwerException, CrawlerData

if TYPE_CHECKING:
    from mdcx.web_async import AsyncWebClient


class GenericBaseCrawler[T: Context = Context](ABC):
    """
    爬虫基类. 所有具体爬虫均应继承此类并实现其抽象方法.

    Crawler 实例的生命周期是一次刮削任务, 即刮削一批文件. 此次任务内对同一网站的请求将使用同一实例.
    所有与单次爬取相关的数据均应存储在 `Context` 中, 可在所有方法中通过 `ctx` 参数访问.

    `Context` 是默认类型, 必要时可实现子类并通过泛型参数 T 指定.

    由于爬取逻辑因网站而异, 在最极端情况下可以重写 `_run` 方法以完全自定义爬取流程.
    """

    def __init__(self, client: "AsyncWebClient", base_url: str = "", browser: Browser | None = None):
        """
        初始化爬虫实例.

        Args:
            client (AsyncWebClient): 异步 HTTP 客户端, 用于发送请求.
            base_url (str, optional): 基础 URL, 用于支持自定义 URL. 不提供则使用默认值.
            browser (_type_, optional): 浏览器实例, 如果提供则某些请求可以改用浏览器进行处理.
        """
        self.async_client = client
        self.base_url: str = base_url or self.base_url_()
        self.lock = Lock()
        self.browser = browser
        """此实例会被多个 Crawler 复用, 其生命周期由调用方负责管理. 但创建的 Context 由每个 Crawler 独立管理."""
        self._browser_context: BrowserContext | None = None

    async def close(self):
        """释放资源, 如关闭浏览器上下文等."""
        if self._browser_context is not None:
            await self._browser_context.close()

    @classmethod
    @abstractmethod
    def site(cls) -> Website:
        """此爬虫对应的网站枚举值."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def base_url_(cls) -> str:
        """默认 URL, 结尾无斜杠. 可以通过 self.base_url 访问实际值."""
        raise NotImplementedError

    @abstractmethod
    def new_context(self, input: CrawlerInput) -> T:
        raise NotImplementedError

    async def run(self, input: CrawlerInput) -> CrawlerResponse:
        """
        执行爬虫任务.

        此方法负责初始化 `Context`, 处理异常, 记录调试信息等. 具体执行流程应在 `_run` 方法中实现.
        """
        start_time = time.time()
        ctx = self.new_context(input)
        ctx.debug(f"{input=}")

        try:
            data = await self._run(ctx)
            return CrawlerResponse(data=data, debug_info=ctx.debug_info)
        except Exception as e:
            ctx.debug(traceback.format_exc())
            ctx.debug_info.error = e
            return CrawlerResponse(debug_info=ctx.debug_info)
        finally:
            ctx.debug_info.execution_time = time.time() - start_time

    async def _run(self, ctx: T):
        if not ctx.input.appoint_url:
            search_urls = await self._generate_search_url(ctx)
            if not search_urls:
                raise CralwerException("生成搜索页 URL 失败")
            if isinstance(search_urls, str):
                search_urls = [search_urls]
            ctx.debug(f"搜索页 URL: {search_urls}")
            ctx.debug_info.search_urls = search_urls

            detail_urls = await self._search(ctx, search_urls)
            if not detail_urls:
                raise CralwerException("搜索失败")
        else:
            detail_urls = [ctx.input.appoint_url]
            ctx.debug(f"使用指定详情页 URL: {ctx.input.appoint_url}")

        ctx.debug_info.detail_urls = detail_urls
        data = await self._detail(ctx, detail_urls)
        if not data:
            raise CralwerException("获取详情页数据失败")
        data.source = self.site().value  # todo use Enum directly
        data = data.to_result()
        return await self.post_process(ctx, data)

    async def _search(self, ctx: T, search_urls: list[str]) -> list[str] | None:
        for search_url in search_urls:
            html, error = await self._fetch_search(ctx, search_url)
            if html is None:
                ctx.debug(f"搜索页请求失败: {error=}")
                continue
            ctx.debug(f"搜索页请求成功: {search_url=}")
            selector = Selector(text=html)
            detail_urls = await self._parse_search_page(ctx, selector, search_url)
            if detail_urls:
                ctx.debug(f"详情页 URL: {detail_urls}")
                return detail_urls if isinstance(detail_urls, list) else [detail_urls]

    async def _detail(self, ctx: T, detail_urls: list[str]) -> CrawlerData | None:
        for detail_url in detail_urls:
            html, error = await self._fetch_detail(ctx, detail_url)
            if html is None:
                ctx.debug(f"详情页请求失败: {error=}")
                continue
            ctx.debug(f"详情页请求成功: {detail_url=}")
            selector = Selector(text=html)
            scraped_data = await self._parse_detail_page(ctx, selector, detail_url)
            if scraped_data and not scraped_data.external_id:
                scraped_data.external_id = detail_url
                return scraped_data

    @abstractmethod
    async def _generate_search_url(self, ctx: T) -> list[str] | str | None:
        """
        生成搜索 URL. 如果重写 `_run` 则无须实现此方法.
        """
        raise NotImplementedError

    @abstractmethod
    async def _parse_search_page(self, ctx: T, html: Selector, search_url: str) -> list[str] | str | None:
        """
        解析搜索结果页, 获取详情页 URL. 如果重写 `_search` 则无须实现此方法.

        此方法应返回完整 URL, 当解析页面获取到相对 URL 时需进行处理.

        Args:
            html (Selector): 包含搜索结果页 HTML 的 parsel Selector 对象.
            search_url (str): 搜索页 URL.

        Returns:
            detail_urls: 一个或多个详情页的 URL, 如果找不到则返回 None.
        """
        raise NotImplementedError

    @abstractmethod
    async def _parse_detail_page(self, ctx: T, html: Selector, detail_url: str) -> CrawlerData | None:
        """
        解析详情页获取数据. 如果重写 `_detail` 则无须实现此方法.

        Args:
            html (Selector): 包含详情页 HTML 的 parsel Selector 对象.
            detail_url (str): 详情页 URL.

        Returns:
            爬取数据对象, 如果解析失败则返回 None.
        """
        raise NotImplementedError

    async def post_process(self, ctx: T, res: CrawlerResult) -> CrawlerResult:
        """
        爬取并解析完成后对结果进行后处理.

        Args:
            res (CrawlerResult): 爬取结果对象.
        """
        return res

    async def _fetch_search(self, ctx: T, url: str, use_browser: bool | None = False) -> tuple[str | None, str]:
        """
        获取搜索页. 此方法不应抛出异常.
        """
        return await self._fetch(ctx, url, use_browser)

    async def _fetch_detail(self, ctx: T, url: str, use_browser: bool | None = False) -> tuple[str | None, str]:
        """
        获取详情页. 此方法不应抛出异常.
        """
        return await self._fetch(ctx, url, use_browser)

    async def _fetch(self, ctx: T, url: str, use_browser: bool | None) -> tuple[str | None, str]:
        if use_browser is not False:
            content, error = await self._browser_fetch(ctx, url)
            if content is not None:
                return content, error
            if use_browser is True:
                return None, f"强制使用浏览器请求但失败: {error=}"
        return await self.async_client.get_text(url, headers=self._get_headers(ctx), cookies=self._get_cookies(ctx))

    async def _browser_fetch(
        self,
        ctx: T,
        url: str,
        wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] | None = "load",
    ) -> tuple[str | None, str]:
        if not await self._init_browser_context(ctx, self._get_cookies_browser(ctx)):
            return None, "浏览器初始化失败"
        assert self._browser_context is not None
        try:
            async with await self._browser_context.new_page() as page:
                await page.goto(url, wait_until=wait_until)
                content = await page.content()
                return content, ""
        except Exception as e:
            return None, f"浏览器请求失败: {e}"

    async def _init_browser_context(self, ctx: T, cookies: Sequence[SetCookieParam] | None = None) -> bool:
        if self.browser is None:
            return False
        if self._browser_context is not None:
            return True
        async with self.lock:
            if self._browser_context is not None:
                return True
            try:
                context = await self.browser.new_context(ignore_https_errors=True)
                if cookies:
                    await context.add_cookies(cookies)
                self._browser_context = context
            except Exception as e:
                ctx.debug(f"创建浏览器上下文失败: {e}")
                return False
        return True

    def _get_cookies(self, ctx: T) -> dict[str, str] | None:
        return None

    def _get_cookies_browser(self, ctx: T) -> Sequence[SetCookieParam] | None:
        return None

    def _get_headers(self, ctx: T) -> dict[str, str] | None:
        return None


class BaseCrawler(GenericBaseCrawler[Context]):
    def new_context(self, input: CrawlerInput) -> Context:
        return Context(input=input)


crawler_registry: dict[Website, type[GenericBaseCrawler[Never]]] = {}


def register_crawler(crawler_cls: type[GenericBaseCrawler[Any]]):
    crawler_registry[crawler_cls.site()] = crawler_cls


def get_crawler(site: Website) -> type[GenericBaseCrawler[Never]] | None:
    """
    获取指定网站的爬虫类.

    注意: 出于类型安全的目的, 将返回类型标注为 `GenericBaseCrawler[Never]`.
    由于允许子类继承 `Context` 作为泛型, 因此实际上没有类型可以准确标注此方法的返回值.

    在应用内部, 只有 `run` 被视为公开 API 调用, `Context` 实际上是内部实现细节, 因此这种标注不会导致问题.
    在测试等情况下, 如果需要调用具有 `ctx` 参数的方法, 必须使用返回类的 `new_context` 类方法创建具体使用的泛型类并传入.
    """
    return crawler_registry.get(site)
