import time
import traceback
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from parsel import Selector

from mdcx.config.models import Website
from mdcx.models.types import CrawlerInput, CrawlerResponse, CrawlerResult

from .types import Context, CralwerException, CrawlerData

if TYPE_CHECKING:
    from mdcx.web_async import AsyncWebClient


class GenericBaseCrawler[T: Context = Context](ABC):
    """
    爬虫基类. 所有具体爬虫均应继承此类并实现其抽象方法.

    Crawler 本身应该是无状态的, 所有与单次爬取相关的数据均应存储在 `Context` 中, 可在所有方法中通过 `ctx` 参数访问.

    `Context` 是默认类型, 必要时可实现子类并通过泛型参数 T 指定.

    由于爬取逻辑因网站而异, 在最极端情况下可以重写 `_run` 方法以完全自定义爬取流程.
    """

    def __init__(self, client: "AsyncWebClient", base_url: str = ""):
        self.async_client = client
        self.base_url: str = base_url or self.base_url_()

    @classmethod
    @abstractmethod
    def site(cls) -> Website:
        """此爬虫对应的网站枚举值."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def base_url_(cls) -> str:
        """支持自定义 URL 的爬虫在不提供自定义值时的默认值. 可以通过 self.base_url 访问实际值."""
        raise NotImplementedError

    @abstractmethod
    def new_context(self, input: CrawlerInput) -> T:
        raise NotImplementedError

    async def run(self, input: CrawlerInput) -> CrawlerResponse:
        start_time = time.time()
        ctx = self.new_context(input)
        ctx.debug(f"{input=}")
        ctx.show(f"-> {self.site}")

        try:
            res = await self._run(ctx)
            res.execution_time = time.time() - start_time
            return res
        except Exception as e:
            ctx.show(str(e))
            ctx.debug(traceback.format_exc())
            return CrawlerResponse(
                success=False,
                logs=ctx.show_logs,
                execution_time=time.time() - start_time,
                error=e,
            )
        finally:
            ctx.show(f"({round(time.time() - start_time, 2)}s)")

    async def _run(self, ctx: T):
        if not ctx.input.appoint_url:
            search_urls = await self._generate_search_url(ctx)
            if not search_urls:
                raise CralwerException("生成搜索页 URL 失败")
            if isinstance(search_urls, str):
                search_urls = [search_urls]
            ctx.debug(f"搜索页 URL: {search_urls}")

            detail_urls = await self._search(ctx, search_urls)
            if not detail_urls:
                raise CralwerException("未找到匹配的详情页 URL")
        else:
            detail_urls = [ctx.input.appoint_url]
            ctx.debug(f"使用指定详情页 URL: {ctx.input.appoint_url}")

        data = await self._detail(ctx, detail_urls)
        if not data:
            raise CralwerException("解析详情页数据失败")
        data.source = self.site().value  # todo use Enum directly
        data = data.to_result()
        await self.post_process(ctx, data)

        return CrawlerResponse(
            success=True,
            data=data,
            detail_urls=detail_urls,
        )

    async def _search(self, ctx: T, search_urls: list[str]) -> list[str] | None:
        for search_url in search_urls:
            html, error = await self._fetch_search(ctx, search_url)
            if html is None:
                ctx.debug(f"搜索页请求失败: {search_url=} {error=}")
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
                ctx.debug(f"详情页请求失败: {detail_url=} {error=}")
                continue
            ctx.debug(f"详情页请求成功: {detail_url=}")
            selector = Selector(text=html)
            scraped_data = await self._parse_detail_page(ctx, selector, detail_url)
            if scraped_data:
                scraped_data.website = detail_url
                return scraped_data

    @abstractmethod
    async def _generate_search_url(self, ctx: T) -> list[str] | str | None:
        """
        生成搜索 URL.
        """
        raise NotImplementedError

    @abstractmethod
    async def _parse_search_page(self, ctx: T, html: Selector, search_url: str) -> list[str] | str | None:
        """
        解析搜索结果页, 获取详情页 URL.

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
        解析详情页获取数据.

        Args:
            html (Selector): 包含详情页 HTML 的 parsel Selector 对象.
            detail_url (str): 详情页 URL.

        Returns:
            爬取数据对象, 如果解析失败则返回 None.
        """
        raise NotImplementedError

    async def post_process(self, ctx: T, res: CrawlerResult):
        """
        爬取并解析完成后对结果进行后处理.

        Args:
            res (CrawlerResult): 爬取结果对象.
        """
        return

    async def _fetch_search(self, ctx: T, url: str) -> tuple[str | None, str]:
        """
        获取搜索页. 此方法不应抛出异常.

        """
        return await self.async_client.get_text(url, headers=self._get_headers(ctx), cookies=self._get_cookies(ctx))

    async def _fetch_detail(self, ctx: T, url: str) -> tuple[str | None, str]:
        """
        获取详情页. 此方法不应抛出异常.
        """
        return await self.async_client.get_text(url, headers=self._get_headers(ctx), cookies=self._get_cookies(ctx))

    def _get_cookies(self, ctx: T) -> dict[str, str] | None:
        return None

    def _get_headers(self, ctx: T) -> dict[str, str] | None:
        return None


class BaseCrawler(GenericBaseCrawler[Context]):
    def new_context(self, input: CrawlerInput) -> Context:
        return Context(input=input)


crawler_registry: dict[Website, type[GenericBaseCrawler]] = {}


def register_crawler(crawler_cls: type[GenericBaseCrawler]):
    crawler_registry[crawler_cls.site()] = crawler_cls


def get_crawler(site: Website) -> type[GenericBaseCrawler] | None:
    return crawler_registry.get(site)
